
from typing import Dict, Callable

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Gdk, GLib, GObject, Vte

class Terminalle:

    def __init__(self, settings: Dict, show: bool):
        self.settings = settings
        self.show_on_startup = show

        self.wnd = Gtk.Window()
        # For some reason the top-level window opacity must not be 1
        # in order to enable any kind of child widget transparency.
        self.wnd.set_opacity(.99)
        self.wnd.set_title('Terminalle')
        self.wnd.set_hide_titlebar_when_maximized(True)
        self.wnd.maximize()
        self.wnd.fullscreen()
        self.wnd.set_keep_above(True)
        self.wnd.set_skip_taskbar_hint(True)
        self.wnd.set_skip_pager_hint(True)
        self.wnd.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.wnd.set_events(Gdk.EventType.FOCUS_CHANGE)
        self.wnd.connect('focus-out-event', self._focus_out)

        self.term = Vte.Terminal()
        self.term.connect('child-exited', self._term_exited)
        self.term.set_font(font_desc=self.settings['font'])
        self.term.set_allow_bold(True)
        self.term.set_allow_hyperlink(True)
        bg = self.settings['colors'][0].copy()
        bg.alpha = self.settings['opacity']
        self.term.set_colors(background=bg, palette=self.settings['colors'])

        success, pid = self.term.spawn_sync(
            pty_flags=Vte.PtyFlags.DEFAULT,
            working_directory=self.settings['home'],
            argv=[self.settings['shell']],
            envv=None,
            spawn_flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD)
        if not success:
            del self.term
            self.wnd.close()
            del self.wnd
            raise RuntimeError('error spawning VTE terminal')
        self.wnd.add(self.term)

        self.accel_group = Gtk.AccelGroup()
        self._init_ctrl_shift_handler('C', self._copy_clipboard)
        self._init_ctrl_shift_handler('V', self._paste_clipboard)
        self.wnd.add_accel_group(self.accel_group)

    def _init_ctrl_shift_handler(self, key_name: str, handler: Callable):
        signal = 'ctrl-shift-' + key_name
        GObject.signal_new(signal, Gtk.Window,
                           GObject.SignalFlags.RUN_LAST | GObject.SignalFlags.ACTION,
                           None, ())
        self.wnd.connect(signal, handler)
        self.wnd.add_accelerator(signal, self.accel_group,
                                 Gdk.keyval_from_name(key_name),
                                 Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK,
                                 Gtk.AccelFlags.LOCKED)

    def run(self):
        self.wnd.show_all()
        if not self.show_on_startup:
            self.wnd.hide()
        Gtk.main()

    def toggle(self):
        GLib.idle_add(self._toggle)

    def _copy_clipboard(self, wnd: Gtk.Window):
        self.term.copy_clipboard_format(Vte.Format.TEXT)

    def _paste_clipboard(self, wnd: Gtk.Window):
        self.term.paste_clipboard()

    def _toggle(self):
        if self.wnd.is_active():
            self.wnd.hide()
        else:
            self.wnd.show()
            self.wnd.grab_focus()

    def _focus_out(self, wnd: Gtk.Window, event: Gdk.EventFocus):
        self.wnd.hide()

    def quit(self):
        GLib.idle_add(Gtk.main_quit)

    def _term_exited(self, term: Vte.Terminal, status: int):
        self.wnd.remove(self.term)
        del self.term
        self.wnd.close()
        del self.wnd
        Gtk.main_quit()
