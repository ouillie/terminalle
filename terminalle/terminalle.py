from subprocess import Popen
from functools import partial
from math import inf
from typing import Callable, Dict, Tuple, Optional

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Vte', '3.91')
from gi.repository import Gtk, GLib, Gio, Vte

SERVICE_NAME = 'party.will.Terminalle'
OBJECT_PATH = '/party/will/Terminalle'
SERVICE_XML = f'''
<!DOCTYPE node PUBLIC
    "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN"
    "http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
<node>
  <interface name="{SERVICE_NAME}">
    <method name="Toggle" />
    <method name="MoveRight" />
    <method name="MoveLeft" />
    <method name="MoveDown" />
    <method name="MoveUp" />
    <method name="Quit" />
  </interface>
</node>
'''

# key names: https://cgit.freedesktop.org/xorg/proto/x11proto/plain/keysymdef.h
# tmux keybinding commands: https://github.com/tmux/tmux/blob/3.5a/key-bindings.c#L347
_tmux_mode_commands = [
    ('exclam', ['tmux', 'break-pane']),
    ('quotedbl', ['tmux', 'split-window']),
    ('numbersign', ['tmux', 'list-buffers']),
    ('dollar', ['tmux', 'command-prompt', '-I', '#S', 'rename-session -- \'%%\'']),
    ('percent', ['tmux', 'split-window', '-h']),
    ('ampersand', ['tmux', 'confirm-before', '-p', 'kill-window #W? (y/n)', 'kill-window']),
    ('apostrophe', ['tmux', 'command-prompt', '-T', 'window-target', '-pindex', 'select-window -t \':%%\'']),
    ('parenleft', ['tmux', 'switch-client', '-p']),
    ('parenright', ['tmux', 'switch-client', '-n']),
    ('comma', ['tmux', 'command-prompt', '-I', '#W', 'rename-window -- \'%%\'']),
    ('minus', ['tmux', 'delete-buffer']),
    ('period', ['tmux', 'command-prompt', '-T', 'target', 'move-window -t \'%%\'']),
    ('colon', ['tmux', 'command-prompt']),
    ('semicolon', ['tmux', 'last-pane']),
    ('equal', ['tmux', 'choose-buffer', '-Z']),
    ('bracketleft', ['tmux', 'copy-mode']),
    ('bracketright', ['tmux', 'paste-buffer']),
    ('braceleft', ['tmux', 'swap-pane', '-U']),
    ('braceright', ['tmux', 'swap-pane', '-D']),
]

class Terminalle:
    """ Manages the D-Bus service and the terminal window. """

    def __init__(self, settings: Dict[str, object], show: bool):
        """ Initialize the window and VTE widget. """
        self.app = Gtk.Application(application_id=SERVICE_NAME)
        self.app.connect('activate', self._on_activate)
        self.settings = settings
        self.show_on_startup = show

    def _on_activate(self, app: Gtk.Application):
        """ Create and show the main window. """
        window = Gtk.ApplicationWindow(application=app)
        window.set_title('Terminalle')
        window.set_icon_name('utilities-terminal')
        window.set_decorated(False)
        # Make the application window's background transparent using CSS.
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b'* { background-color: transparent; }')
        Gtk.StyleContext.add_provider_for_display(
            window.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        # Maximize the window because fullscreen does not support transparency.
        # https://gitlab.freedesktop.org/wayland/wayland-protocols/-/issues/116
        window.maximize()
        if self.settings['autohide']:
            focus_controller = Gtk.EventControllerFocus()
            focus_controller.connect('leave', self._autohide)
            window.add_controller(focus_controller)

        terminal = Vte.Terminal()
        terminal.set_font(font_desc=self.settings['font'])
        terminal.set_allow_bold(True)
        terminal.set_allow_hyperlink(True)
        bg = self.settings['colors'][0].copy()
        bg.alpha = self.settings['opacity']
        terminal.set_colors(background=bg, palette=self.settings['colors'])
        terminal.connect('child-exited', self._term_exited)
        window.set_child(terminal)

        self.window = window
        self.terminal = terminal

        terminal.spawn_async(
            Vte.PtyFlags.DEFAULT,
            self.settings['home'],            # Initial working directory.
            [self.settings['shell']],         # argv
            None,                             # Initial environment variables.
            GLib.SpawnFlags.DEFAULT,
            None,                             # Callback for child setup.
            (),                               # User arguments passed to callback.
            -1,                               # Use the default timeout.
            None,                             # Gio Cancellable
            self._term_spawn_async_callback,  # Callback after spawn complete.
            (),                               # User arguments passed to callback.
        )

        # Set up keyboard shortcuts.
        shortcut_controller = Gtk.ShortcutController()
        shortcut_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        _add_shortcut(shortcut_controller, "<Control><Shift>c", self._copy_clipboard)
        _add_shortcut(shortcut_controller, "<Control><Shift>v", self._paste_clipboard)
        if self.settings['tmux']:
            for key_name, cmd in _tmux_mode_commands:
                _add_shortcut(shortcut_controller, f"<Control>{key_name}", _run_cmd_handler(cmd))
        window.add_controller(shortcut_controller)

    def _term_spawn_async_callback(self, terminal: Vte.Terminal, pid: int, error: Optional[GLib.Error]):
        """ Finish starting up after the terminal has been spawned. """
        if error is not None:
            self.quit()
            raise RuntimeError(f'Error spawning VTE [{error.domain}:{error.code}]: {error.message}')
        if self.show_on_startup:
            self.window.present()
            self.window.grab_focus()

        self.methods = {
            'Toggle': self.toggle,
            'MoveRight': partial(self.move, 0, 1),
            'MoveLeft': partial(self.move, 0, -1),
            'MoveDown': partial(self.move, 1, 1),
            'MoveUp': partial(self.move, 1, -1),
            'Quit': self.quit,
        }
        service = Gio.DBusNodeInfo.new_for_xml(SERVICE_XML)
        self.app.get_dbus_connection().register_object(OBJECT_PATH, service.interfaces[0], self._on_method_call)

    def _on_method_call(self, connection: Gio.DBusConnection,
                        sender: str, object_path: str, interface_name: str,
                        method_name: str, parameters: Tuple,
                        invocation: Gio.DBusMethodInvocation):
        """ Handle a D-Bus method invocation. """
        self.methods[method_name]()
        invocation.return_value()

    def run(self):
        """ Run the GTK application. """
        self.app.run(None)

    def toggle(self):
        """ Toggle window visibility. """
        GLib.idle_add(self._toggle)

    def _toggle(self):
        if self.window.is_active():
            self.window.hide()
        else:
            if not self.window.props.visible:
                self.window.present()
            self.window.grab_focus()

    def move(self, axis: int, direction: int):
        """
        Move the window to the closest adjacent monitor in a particular direction.

        `axis` must be either `0` (left / right) or `1` (up / down).
        `direction` must be either `1` (right / down) or `-1` (left / up).
        """
        if self.window.is_active():
            display = self.window.get_display()
            curr_geometry = display.get_monitor_at_surface(self.window.get_surface()).get_geometry()
            mid = (curr_geometry.x + 0.5 * curr_geometry.width,
                   curr_geometry.y + 0.5 * curr_geometry.height)
            curr_mid_on = mid[axis]
            curr_mid_off = mid[1 - axis]
            best_gain = inf
            best_monitor = None
            for monitor in display.get_monitors():
                geometry = monitor.get_geometry()
                mid = (geometry.x + 0.5 * geometry.width,
                       geometry.y + 0.5 * geometry.height)
                mid_on = mid[axis]
                mid_off = mid[1 - axis]
                gain = (mid_on - curr_mid_on) * direction
                if gain > 0 and gain < best_gain and gain > abs(mid_off - curr_mid_off):
                    best_gain = gain
                    best_monitor = monitor
            if best_monitor is not None:
                self.window.fullscreen_on_monitor(best_monitor)
                self.window.maximize()
                self.window.unfullscreen()
                self.window.grab_focus()

    def _copy_clipboard(self, widget: Gtk.Widget, args: Optional[GLib.Variant]) -> bool:
        self.terminal.copy_clipboard_format(Vte.Format.TEXT)
        return True

    def _paste_clipboard(self, widget: Gtk.Widget, args: Optional[GLib.Variant]) -> bool:
        self.terminal.paste_clipboard()
        return True

    def _autohide(self, controller: Gtk.EventControllerFocus):
        """ Hide the window when it loses focus. """
        GLib.idle_add(self.window.hide)

    def _term_exited(self, terminal: Vte.Terminal, status: int):
        """ Close the window automatically when the terminal exits. """
        self.quit()

    def quit(self):
        """ Quit the GTK application. """
        GLib.idle_add(self.app.quit)

def _add_shortcut(controller: Gtk.ShortcutController, trigger: str, handler: Callable[[Gtk.Widget, Optional[GLib.Variant], object], bool]):
    """ Set up a keyboard shortcut. """
    controller.add_shortcut(
        Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string(trigger),
            Gtk.CallbackAction.new(handler),
        )
    )

def _run_cmd_handler(cmd: str) -> Callable[[Gtk.Widget, Optional[GLib.Variant]], bool]:
    def _handler(widget: Gtk.Widget, args: Optional[GLib.Variant]) -> bool:
        Popen(cmd)
        return True
    return _handler
