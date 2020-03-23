
from typing import Dict, Callable
from os import system

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Gdk, GLib, GObject, Vte

class Terminalle:
    """ Manages the window. """

    def __init__(self, settings: Dict[str, object], show: bool):
        """ Initialize the window and VTE widget. """
        wnd = Gtk.Window()
        wnd.set_title('Terminalle')
        wnd.fullscreen()
        wnd.set_keep_above(True)
        wnd.set_skip_taskbar_hint(True)
        wnd.set_skip_pager_hint(True)
        wnd.set_type_hint(Gdk.WindowTypeHint.DOCK)
        # For some reason the top-level window opacity must not be 1
        # in order to enable any kind of child widget transparency.
        wnd.set_opacity(.99)
        wnd.set_events(Gdk.EventType.FOCUS_CHANGE)
        wnd.connect('focus-out-event', self._focus_out)

        term = Vte.Terminal()
        term.set_font(font_desc=settings['font'])
        term.set_allow_bold(True)
        term.set_allow_hyperlink(True)
        bg = settings['colors'][0].copy()
        bg.alpha = settings['opacity']
        term.set_colors(background=bg, palette=settings['colors'])
        term.connect('child-exited', self._term_exited)
        wnd.add(term)

        accel_group = Gtk.AccelGroup()
        # Ctrl+Shift+(C|V) to use the clipboard.
        _init_ctrl_shift_handler('c', wnd, accel_group, self._copy_clipboard)
        _init_ctrl_shift_handler('v', wnd, accel_group, self._paste_clipboard)
        if settings['tmux']:
            # Hardwire recommended shortcuts that are impossible to bind from `.tmux.conf`.
            _init_ctrl_handler('quotedbl', wnd, accel_group, _tmux_cmd('split-window'))
            _init_ctrl_handler('percent', wnd, accel_group, _tmux_cmd('split-window -h'))
            _init_ctrl_handler('braceleft', wnd, accel_group, _tmux_cmd('swap-pane -U'))
            _init_ctrl_handler('braceright', wnd, accel_group, _tmux_cmd('swap-pane -D'))
        wnd.add_accel_group(accel_group)

        self.wnd = wnd
        self.term = term
        self.settings = settings
        self.show_on_startup = show

    def run(self):
        """ Open the TTY and enter the GTK main loop. """
        success, vte_pid = self.term.spawn_sync(
            pty_flags=Vte.PtyFlags.DEFAULT,
            working_directory=self.settings['home'],
            argv=[self.settings['shell']],
            envv=None,
            spawn_flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD)
        if not success:
            self.wnd.close()
            raise RuntimeError('Error spawning VTE terminal.')
        self.wnd.show_all()
        if not self.show_on_startup:
            self.wnd.hide()
        Gtk.main()

    def toggle(self):
        """ Toggle window visibility. """
        GLib.idle_add(self._toggle)

    def _toggle(self):
        if self.wnd.is_active():
            self.wnd.hide()
        else:
            self.wnd.show()
            self.wnd.grab_focus()

    def _copy_clipboard(self, wnd: Gtk.Window):
        self.term.copy_clipboard_format(Vte.Format.TEXT)

    def _paste_clipboard(self, wnd: Gtk.Window):
        self.term.paste_clipboard()

    def _focus_out(self, wnd: Gtk.Window, event: Gdk.EventFocus):
        GLib.idle_add(self.wnd.hide)

    def _term_exited(self, term: Vte.Terminal, status: int):
        self.quit()

    def quit(self):
        """ Close the window and exit the GTK main loop. """
        GLib.idle_add(self._quit)

    def _quit(self):
        self.wnd.close()
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
                  wnd: Gtk.Window,
                  accel_group: Gtk.AccelGroup,
                  handler: Callable):
    GObject.signal_new(signal_name, Gtk.Window,
                       GObject.SignalFlags.RUN_LAST | GObject.SignalFlags.ACTION,
                       None, ())
    wnd.connect(signal_name, handler)
    wnd.add_accelerator(signal_name, accel_group,
                        Gdk.keyval_from_name(key_name), mod_mask,
                        Gtk.AccelFlags.LOCKED)

def _tmux_cmd(cmd: str):
    def _handler(wnd: Gtk.Window):
        system('tmux ' + cmd)
    return _handler
