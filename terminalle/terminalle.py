
from os import system
from functools import partial
from typing import Callable, Dict, Tuple

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Gdk, GLib, Gio, GObject, Vte

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

# https://github.com/tmux/tmux/blob/28b6237c623f507188a782a016563c78dd0ffb85/key-bindings.c#L344
# https://cgit.freedesktop.org/xorg/proto/x11proto/plain/keysymdef.h
_default_tmux_commands = [
    ('exclam', 'break-pane'),
    ('quotedbl', 'split-window'),
    ('numbersign', 'list-buffers'),
    ('dollar', 'command-prompt -I "#S" "rename-session -- '"'"'%%'"'"'"'),
    ('percent', 'split-window -h'),
    ('ampersand', 'confirm-before -p "kill-window #W? (y/n)" kill-window'),
    ('apostrophe', 'command-prompt -T window-target -p "index" "select-window -t '"'"':%%'"'"'"'),
    ('parenleft', 'switch-client -p'),
    ('parenright', 'switch-client -n'),
    ('comma', 'command-prompt -I "#W" "rename-window -- '"'"'%%'"'"'"'),
    # ('minus', 'delete-buffer'),
    # ('period', 'command-prompt -T target "move-window -t '"'"'%%'"'"'"'),
    ('colon', 'command-prompt'),
    ('semicolon', 'last-pane'),
    ('equal', 'choose-buffer -Z'),
    ('bracketleft', 'copy-mode'),
    ('bracketright', 'paste-buffer'),
    ('braceleft', 'swap-pane -U'),
    ('braceright', 'swap-pane -D'),
]

class Terminalle:
    """ Manages the D-Bus service and the terminal window. """

    def __init__(self, settings: Dict[str, object], show: bool):
        """ Initialize the window and VTE widget. """
        window = Gtk.Window()
        window.set_title('Terminalle')
        window.fullscreen()
        window.set_keep_above(True)
        window.set_skip_taskbar_hint(True)
        window.set_skip_pager_hint(True)
        window.set_decorated(False)
        window.set_type_hint(Gdk.WindowTypeHint.DOCK)
        # For some reason the top-level window opacity must not be 1
        # in order to enable any kind of child widget transparency.
        window.set_opacity(.99)
        if settings['autohide']:
            window.set_events(Gdk.EventType.FOCUS_CHANGE)
            window.connect('focus-out-event', self._autohide)

        terminal = Vte.Terminal()
        terminal.set_font(font_desc=settings['font'])
        terminal.set_allow_bold(True)
        terminal.set_allow_hyperlink(True)
        bg = settings['colors'][0].copy()
        bg.alpha = settings['opacity']
        terminal.set_colors(background=bg, palette=settings['colors'])
        terminal.connect('child-exited', self._term_exited)
        window.add(terminal)

        accel_group = Gtk.AccelGroup()
        # Ctrl+Shift+(C|V) to use the clipboard.
        _init_ctrl_shift_handler('c', window, accel_group, self._copy_clipboard)
        _init_ctrl_shift_handler('v', window, accel_group, self._paste_clipboard)
        if settings['tmux']:
            # Hardwire shortcuts that are generally impossible to configure in `.tmux.conf`.
            for key_name, cmd in _default_tmux_commands:
                _init_ctrl_handler(key_name, window, accel_group, _tmux_cmd(cmd))
        window.add_accel_group(accel_group)

        self.window = window
        self.terminal = terminal
        self.settings = settings
        self.show_on_startup = show

    def run(self):
        """ Open the TTY and enter the GTK main loop. """
        self.terminal.spawn_async(
            Vte.PtyFlags.DEFAULT,
            self.settings['home'],            # Initial working directory.
            [self.settings['shell']],         # argv
            None,                             # Initial environment variables.
            GLib.SpawnFlags.DEFAULT,
            None,                             # Callback for child setup.
            None,                             # User data passed to callback.
            -1,                               # Use the default timeout.
            None,                             # Gio Cancellable; not supported on legacy KDE
            self._term_spawn_async_callback,  # Callback after spawn complete.
            None)                             # User data passed to callback.
        Gtk.main()

    def _term_spawn_async_callback(self, terminal, pid, error, user_data):
        if error is not None:
            self.window.close()
            Gtk.main_quit()
            raise RuntimeError(f'Error spawning VTE [{error.domain}:{error.code}]: {error.message}')
        if self.show_on_startup:
            self.window.show_all()
        else:
            # Only show the child widgets, waiting for the toggle signal to show the window.
            self.terminal.show_all()
        Gio.bus_own_name(Gio.BusType.SESSION,
                         SERVICE_NAME,
                         Gio.BusNameOwnerFlags.DO_NOT_QUEUE,
                         None,
                         self._on_name_acquired,
                         self._on_name_lost)

    def _on_name_acquired(self, connection: Gio.DBusConnection, name: str) -> None:
        self.methods = {'Toggle': self.toggle,
                        'MoveRight': partial(self.move, 0, 1),
                        'MoveLeft': partial(self.move, 0, -1),
                        'MoveDown': partial(self.move, 1, 1),
                        'MoveUp': partial(self.move, 1, -1),
                        'Quit': self.quit}
        service = Gio.DBusNodeInfo.new_for_xml(SERVICE_XML)
        connection.register_object(OBJECT_PATH, service.interfaces[0], self._on_method_call)

    def _on_name_lost(self, connection: Gio.DBusConnection, name: str) -> None:
        self.quit()
        raise RuntimeError(f'Interface \'{name}\' already in use.')

    def _on_method_call(self, connection: Gio.DBusConnection,
                        sender: str, object_path: str, interface_name: str,
                        method_name: str, parameters: Tuple,
                        invocation: Gio.DBusMethodInvocation) -> None:
        self.methods[method_name]()
        invocation.return_value()

    def toggle(self):
        """ Toggle window visibility. """
        GLib.idle_add(self._toggle)

    def _toggle(self):
        if self.window.is_active():
            self.window.hide()
        else:
            self.window.show()
            self.window.grab_focus()

    def move(self, axis: int, direction: int):
        """ Move the window to the closest adjacent monitor in a particular direction.

        `axis` must be either `0` (x-axis) or `1` (y-axis).
        `direction` must be either `1` (right / down) or `-1` (left / up).
        """
        if self.window.is_active():
            display = self.window.get_display()
            curr_geometry = display.get_monitor_at_window(self.window.get_window()).get_geometry()
            mid = (curr_geometry.x + 0.5 * curr_geometry.width,
                   curr_geometry.y + 0.5 * curr_geometry.height)
            curr_mid_on = mid[axis]
            curr_mid_off = mid[1 - axis]
            best_gain = None
            best_monitor = None
            for i in range(display.get_n_monitors()):
                geometry = display.get_monitor(i).get_geometry()
                mid = (geometry.x + 0.5 * geometry.width,
                       geometry.y + 0.5 * geometry.height)
                mid_on = mid[axis]
                mid_off = mid[1 - axis]
                gain = (mid_on - curr_mid_on) * direction
                if gain > 0 and (best_gain is None or gain < best_gain) \
                        and gain > abs(mid_off - curr_mid_off):
                    best_gain = gain
                    best_monitor = i
            if best_monitor is not None:
                self.window.fullscreen_on_monitor(display.get_default_screen(), best_monitor)
                self.window.grab_focus()

    def _copy_clipboard(self, window: Gtk.Window):
        self.terminal.copy_clipboard_format(Vte.Format.TEXT)

    def _paste_clipboard(self, window: Gtk.Window):
        self.terminal.paste_clipboard()

    def _autohide(self, window: Gtk.Window, event: Gdk.EventFocus):
        GLib.idle_add(self.window.hide)

    def _term_exited(self, terminal: Vte.Terminal, status: int):
        self.quit()

    def quit(self):
        """ Close the window and exit the GTK main loop. """
        GLib.idle_add(self._quit)

    def _quit(self):
        self.window.close()
        GLib.idle_add(Gtk.main_quit)

def _init_ctrl_handler(key_name: str, *args):
    return _init_handler('ctrl-' + key_name,
                         Gdk.ModifierType.CONTROL_MASK,
                         key_name, *args)

def _init_ctrl_shift_handler(key_name: str, *args):
    return _init_handler('ctrl-shift-' + key_name,
                         Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK,
                         key_name, *args)

def _init_handler(signal_name: str,
                  mod_mask: Gdk.ModifierType,
                  key_name: str,
                  window: Gtk.Window,
                  accel_group: Gtk.AccelGroup,
                  handler: Callable):
    GObject.signal_new(signal_name, Gtk.Window,
                       GObject.SignalFlags.RUN_LAST | GObject.SignalFlags.ACTION,
                       None, ())
    window.connect(signal_name, handler)
    window.add_accelerator(signal_name, accel_group,
                           Gdk.keyval_from_name(key_name), mod_mask,
                           Gtk.AccelFlags.LOCKED)

def _tmux_cmd(cmd: str):
    def _handler(window: Gtk.Window):
        system(f'tmux {cmd}')
    return _handler
