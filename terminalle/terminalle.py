
from os import system
from typing import Dict, Callable

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Gdk, GLib, Gio, GObject, Vte

class Terminalle:
    """ Manages the window. """

    def __init__(self, settings: Dict[str, object], show: bool):
        """ Initialize the window and VTE widget. """
        window = Gtk.Window()
        window.set_title('Terminalle')
        window.fullscreen()
        window.set_keep_above(True)
        window.set_skip_taskbar_hint(True)
        window.set_skip_pager_hint(True)
        # For some reason the top-level window opacity must not be 1
        # in order to enable any kind of child widget transparency.
        window.set_opacity(.99)
        window.set_events(Gdk.EventType.FOCUS_CHANGE)
        window.connect('focus-out-event', self._focus_out)

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
            # Hardwire recommended shortcuts that are impossible to bind from `.tmux.conf`.
            for key_name, cmd in [('quotedbl', 'split-window'),
                                  ('percent', 'split-window -h'),
                                  ('braceleft', 'swap-pane -U'),
                                  ('braceright', 'swap-pane -D'),
                                  ('bracketleft', 'copy-mode'),
                                  ('bracketright', 'paste-buffer')]:
                _init_ctrl_handler(key_name, window, accel_group, _tmux_cmd(cmd))
        window.add_accel_group(accel_group)

        self.window = window
        self.terminal = terminal
        self.settings = settings
        self.show_on_startup = show

    def run(self):
        """ Open the TTY and enter the GTK main loop. """
        term_spawn_canceller = Gio.Cancellable.new()
        self.terminal.spawn_async(
            Vte.PtyFlags.DEFAULT,
            self.settings['home'],            # Initial working directory.
            [self.settings['shell']],         # argv
            None,                             # Initial environment variables.
            GLib.SpawnFlags.DEFAULT,
            None,                             # Callback for child setup.
            None,                             # User data passed to callback.
            -1,                               # Use the default timeout.
            term_spawn_canceller,             # In case we need to cancel the spawn.
            self._term_spawn_async_callback,  # Callback after spawn complete.
            None)                             # User data passed to callback.
        try:
            Gtk.main()
        finally:
            term_spawn_canceller.cancel()

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

    def toggle(self):
        """ Toggle window visibility. """
        GLib.idle_add(self._toggle)

    def _toggle(self):
        if self.window.is_active():
            self.window.hide()
        else:
            self.window.show()
            self.window.grab_focus()

    def quit(self):
        """ Close the window and exit the GTK main loop. """
        GLib.idle_add(self._quit)

    def move(self, axis: int, direction: int):
        """ Move the window to an adjacent monitor.
        `axis` must be either `0` (x-axis) or `1` (y-axis).
        `direction` must be either `1` (down / right) or `-1` (up / left).
        """
        if self.window.is_active():
            display = self.window.get_display()
            curr_geometry = display.get_monitor_at_window(self.window).get_geometry()
            mid = (curr_geometry.x + (curr_geometry.width * 0.5),
                   curr_geometry.y + (curr_geometry.height * 0.5))
            curr_mid_on = mid[axis]
            curr_mid_off = mid[1 - axis]
            best_gain = None
            best_monitor = None
            for i in range(display.get_n_monitors()):
                geometry = display.get_monitor(i).get_geometry()
                mid = (geometry.x + (geometry.width * 0.5),
                       geometry.y + (geometry.height * 0.5))
                mid_on = mid[axis]
                mid_off = mid[1 - axis]
                gain = mid_on * direction - curr_mid_on
                if gain > 0 and (best_gain is None or gain < best_gain) \
                        and gain > abs(curr_mid_off - mid_off):
                    best_gain = gain
                    best_monitor = i
            if best_monitor is not None:
                self.window.fullscreen_on_monitor(screen, best_monitor)

    def _copy_clipboard(self, window: Gtk.Window):
        self.terminal.copy_clipboard_format(Vte.Format.TEXT)

    def _paste_clipboard(self, window: Gtk.Window):
        self.terminal.paste_clipboard()

    def _focus_out(self, window: Gtk.Window, event: Gdk.EventFocus):
        GLib.idle_add(self.window.hide)

    def _term_exited(self, terminal: Vte.Terminal, status: int):
        self.quit()

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
