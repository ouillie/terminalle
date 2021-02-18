# TERMINALLE

A modern, extremely minimalist, semi-transparent fullscreen "drop-down" terminal emulator.
Use [dbus](https://www.freedesktop.org/wiki/Software/dbus/) (installed by default in Gnome and KDE)
to toggle window visibility or quit.

Based on [VTE](https://wiki.gnome.org/Apps/Terminal/VTE),
the business logic of this python package is contained entirely within
[a concise ~150-line file](terminalle/terminalle.py)
-- which mostly just configures keyboard shortcuts --
making it easy to modify for alternative uses.

It omits many features common in other terminal emulators, such as tabs,
because it's meant to be used in conjunction with a terminal multiplexer
such as [tmux](https://github.com/tmux/tmux), which offers a stable, powerful, and mature UI.
See also [tmux mode](#tmux-mode) for enhanced tmux features.

### Usage

```bash
# See usage info.
$ terminalle --help

# Start the server. The window is initially hidden by default.
# Note that this is unnecessary you run `terminalle auto`.
$ terminalle &

# Toggle window visibility.
$ dbus-send --session --type=method_call --dest=org.gnome.Terminalle /termctl org.gnome.Terminalle.Toggle

# Close the window and kill the server.
$ dbus-send --session --type=method_call --dest=org.gnome.Terminalle /termctl org.gnome.Terminalle.Quit
```

Use `Ctrl+Shift+C` and `Ctrl+Shift+V` to access the clipboard.

### Install

```bash
$ sudo pip install terminalle

# Optional: start the server automatically on login and restart automatically if exited.
$ terminalle auto
```

You'll probably want to hook up the toggle method to a keybinding for easy access.
In Gnome, you can do that with `gsettings`:

```bash
# WARNING: Running this verbatim will disable any other custom keybindings.
#          It is merely provided as an example.
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

### TMUX MODE

This is the recommended way to use Terminalle.
Turn it on by setting `tmux: true` in `terminalle.yaml` (see [configuration](#configuration)).
It configures some alternative tmux keyboard shortcuts,
which would normally be impossible to configure in `.tmux.conf`,
generally eliminating the prefix in favor of a simple `Ctrl` modifier,
thus cutting the number of keystrokes in half
without requiring you to memorize new shortcuts.
If you're a tmux power-user, this will **change** things for you.

The following shortcuts are enabled in tmux mode:

| Command           | tmux default | tmux mode |
| :---------------- | -----------: | --------: |
| `split-window`    | `<Prefix> "` |  `Ctrl+"` |
| `split-window -h` | `<Prefix> %` |  `Ctrl+%` |
| `swap-pane -U`    | `<Prefix> {` |  `Ctrl+{` |
| `swap-pane -D`    | `<Prefix> }` |  `Ctrl+}` |
| `copy-mode`       | `<Prefix> [` |  `Ctrl+[` |
| `paste-buffer`    | `<Prefix> ]` |  `Ctrl+]` |

To reap maximum benefits, add the following to your `.tmux.conf`,
to take care of other common tmux shortcuts that do not get mangled by typical terminal emulators:

```bash
# Generally shorten `Ctrl+b <X>` to `Ctrl+<X>` for various `<X>`.
bind -n C-Up resize-pane -U            # Ctrl+Up
bind -n C-Down resize-pane -D          # Ctrl+Down
bind -n C-Left resize-pane -L          # Ctrl+Left
bind -n C-Right resize-pane -R         # Ctrl+Right

# Generally shorten `Ctrl+b Meta+<X>` to `Meta+<X>`.
bind -n M-Up resize-pane -U 5          # Alt+Up
bind -n M-Down resize-pane -D 5        # Alt+Down
bind -n M-Left resize-pane -L 5        # Alt+Left
bind -n M-Right resize-pane -R 5       # Alt+Right

# Note that `new-window` is not shortened because `Ctrl+c` sends `SIGINT`.
bind -n C-n next-window                # Ctrl+n
bind -n C-p previous-window            # Ctrl+p

bind -n C-Space next-layout            # Ctrl+Space
```

This all goes especially well with something like
[vim-tmux-navigator](https://github.com/christoomey/vim-tmux-navigator).
