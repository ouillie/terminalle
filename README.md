
A modern, extremely minimalist, fullscreen "drop-down" terminal emulator that supports transparency.
Use [dbus](https://www.freedesktop.org/wiki/Software/dbus/) (installed by default in Gnome and KDE)
to toggle window visibility or quit.

Based on [VTE](https://github.com/GNOME/vte), the business logic of this python package
is contained entirely within [a concise ~130-line file](terminalle/terminalle.py),
which mostly just configures keyboard shortcuts, making it easy to adapt to alternative uses.
See also [configuration](#configuration).

It omits many features common in other terminal emulators, such as tabs,
because it's meant to be used in conjunction with a terminal multiplexer
such as [tmux](https://github.com/tmux/tmux), which offers a stable, powerful, and mature UI.
See also [tmux mode](#tmux-mode) for enhanced tmux features.

### Usage

```bash
# See usage info.
$ python -m terminalle --help

# Start the server. The window is initially hidden by default.
$ python -m terminalle &

# Toggle window visibility.
$ dbus-send --session --type=method_call --dest=org.gnome.Terminalle /termctl org.gnome.Terminalle.Toggle

# Close the window and kill the server.
$ dbus-send --session --type=method_call --dest=org.gnome.Terminalle /termctl org.gnome.Terminalle.Quit
```

### Install

```bash
$ sudo pip install .

# Optional: Start the server automatically on login.
$ AUTOSTART="${HOME}/.config/autostart"
$ mkdir -p "${AUTOSTART}"
$ cp ./terminalle.desktop "${AUTOSTART}"

# Optional: Restart the server automatically if exited.
$ DBUS_SERVICES="${XDG_DATA_DIRS:-/usr/share}/dbus-1/services"
$ mkdir -p "${DBUS_SERVICES}"
$ cp ./org.gnome.Terminalle.service "${DBUS_SERVICES}"
```

You'll probably want to hook up the toggle method to a keybinding.
In Gnome, you can do that with `gsettings`:

```bash
# WARNING: Running this verbatim will disable any other custom keybindings.
$ gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/']"
# WARNING: This will overwrite any existing custom keybinding called 'custom0'.
$ gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ name "Toggle Terminalle"
$ gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ command "dbus-send --session --type=method_call --dest=org.gnome.Terminalle /termctl org.gnome.Terminalle.Toggle"
$ gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ binding "<Super>Return"
```

### Configuration

See an [example configuration](terminalle.yaml).
See the defaults in [`settings.py`](terminalle/settings.py).
Defaults can be selectively overridden in `${HOME}/.config/terminalle.yaml`.

### TMUX Mode

This is the recommended way to use Terminalle.
Turn it on by setting `tmux: true` in `terminalle.yaml` (see [configuration](#configuration)).
It configures some alternative tmux keyboard shortcuts,
which would normally be impossible to configure in `.tmux.conf`,
eliminating the prefix in favor of a simple `Ctrl` modifier,
thus cutting the number of keystrokes in half.
If you're a tmux power-user, this will change things for you.

| Command         | tmux default | tmux mode |
| :-------------- | -----------: | --------: |
| split-window    | `<Prefix> "` |  `Ctrl+"` |
| split-window -h | `<Prefix> %` |  `Ctrl+%` |
| swap-pane -U    | `<Prefix> {` |  `Ctrl+{` |
| swap-pane -D    | `<Prefix> }` |  `Ctrl+}` |
| copy-mode       | `<Prefix> [` |  `Ctrl+[` |

To reap maximum benefits, add the following to your `.tmux.conf`,
to take care of other common tmux shortcuts that do not get mangled by typical terminal emulators:

```bash
# Generally shorten `<Prefix> X` to `Ctrl+X` for various `X`.
bind-key -n C-Up resize-pane -U       # Ctrl+Up
bind-key -n C-Down resize-pane -D     # Ctrl+Down
bind-key -n C-Left resize-pane -L     # Ctrl+Left
bind-key -n C-Right resize-pane -R    # Ctrl+Right

# Generally shorten `<Prefix> Meta+X` to `Meta+X`.
bind-key -n M-Up resize-pane -U 5     # Alt+Up
bind-key -n M-Down resize-pane -D 5   # Alt+Down
bind-key -n M-Left resize-pane -L 5   # Alt+Left
bind-key -n M-Right resize-pane -R 5  # Alt+Right

bind-key -n C-n next-window           # Ctrl+n
bind-key -n C-p previous-window       # Ctrl+p
# Note that `new-window` is not shortened because `Ctrl+c` sends `SIGINT`.

bind-key -n C-Space next-layout       # Ctrl+Space
```

This all goes especially well with something like
[vim-tmux-navigator](https://github.com/christoomey/vim-tmux-navigator).
