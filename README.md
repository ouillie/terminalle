# TERMINALLE

A modern, extremely minimalist, semi-transparent fullscreen "drop-down" terminal emulateur.
Use [dbus][1] (installed by default in GNOME and KDE) to toggle window visibility or quit.

Based on [VTE][2], the business logic of this Python package is contained entirely within
[a concise ~150-line file][3] &mdash; which mostly just configures keyboard shortcuts &mdash;
making it easy to modify for alternative uses.

It omits many features common in other terminal emulators, such as tabs,
because it's meant to be used in conjunction with a terminal multiplexer
such as [tmux][4], which offers a stable, powerful, and mature UI.
See also [tmux mode][5] for enhanced tmux features.

### Usage

```bash
# See usage info.
$ terminalle --help

# Start the server. The window is initially hidden by default.
# This is unnecessary if you've enabled auto-start with `terminalle auto`.
$ terminalle &

# Toggle window visibility.
$ dbus-send --session --type=method_call --dest=org.gnome.Terminalle /org/gnome/Terminalle org.gnome.Terminalle.Toggle

# Close the window and kill the server.
$ dbus-send --session --type=method_call --dest=org.gnome.Terminalle /org/gnome/Terminalle org.gnome.Terminalle.Quit
```

Use `Ctrl+Shift+C` and `Ctrl+Shift+V` to access the clipboard.

### Install

```bash
$ sudo pip install terminalle

# Optional: start the server automatically on login and restart automatically if exited.
$ terminalle auto

# Optional: disable auto-start (if enabled, this should be done prior to uninstalling).
$ terminalle no-auto
```

You'll probably want to hook up the toggle method to a keybinding for easy access.
In GNOME, you can either do that in the GNOME Control Center GUI (a.k.a "Settings"),
or with `gsettings`:

```bash
# WARNING: Running this verbatim will disable any other custom keybindings.
#          It is merely provided as an example.
$ gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/']"

# WARNING: This will overwrite any existing custom keybinding called 'custom0'.
$ gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ name "Toggle Terminalle"
$ gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ command "dbus-send --session --type=method_call --dest=org.gnome.Terminalle /org/gnome/Terminalle org.gnome.Terminalle.Toggle"
$ gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ binding "<Super>Return"
```

### Configuration

See an [example configuration][6]. See the defaults in [`settings.py`][7].
Defaults can be selectively overridden in `${XDG_CONFIG_HOME}/terminalle.yaml`.
Typically, this is `${HOME}/.config/terminalle.yaml`.

### TMUX MODE

This is the recommended way to use Terminalle.
Turn it on by setting `tmux: true` in `terminalle.yaml` (see [configuration][8]).
It configures some alternative tmux keyboard shortcuts,
which would normally be impossible to configure in `.tmux.conf`
since terminal emulators typically cannot handle these key combinations.
Generally replacing the tmux prefix with a simple `Ctrl` modifier,
it cuts the number of keystrokes in half
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
taking care of other common tmux shortcuts that do not get mangled by typical terminal emulators:

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

This all goes especially well with something like [vim-tmux-navigator][9].

[1]: https://www.freedesktop.org/wiki/Software/dbus/
[2]: https://wiki.gnome.org/Apps/Terminal/VTE
[3]: terminalle/terminalle.py
[4]: https://tmux.github.io/
[5]: #tmux-mode
[6]: terminalle.yaml
[7]: terminalle/settings.py
[8]: #configuration
[9]: https://github.com/christoomey/vim-tmux-navigator
