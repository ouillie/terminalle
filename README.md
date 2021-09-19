# TERMINALLE

A modern, minimalist, semi-transparent fullscreen "drop-down" terminal emulateur
for freedesktop.org-compatible desktops (e.g. GNOME, KDE).

It omits many features common in other terminal emulators, such as tabs,
because it's meant to be used in conjunction with a terminal multiplexer such as [tmux][1],
which offers a solid, mature UI.
See also [tmux mode][2] for enhanced tmux features.

Based on [VTE][3], the business logic of this Python package is contained entirely in
[a ~200-line file][4], making it easy to inspect and modify.

## Usage

Use [D-Bus][5] to control the application.

```bash
# See usage info.
$ terminalle --help

# Start the server. The window is initially hidden by default.
# This is unnecessary if you've enabled auto-start with `terminalle auto`.
$ terminalle &

# Toggle window visibility.
$ dbus-send --session --type=method_call --dest=party.will.Terminalle /party/will/Terminalle party.will.Terminalle.Toggle

# Close the window and kill the server.
$ dbus-send --session --type=method_call --dest=party.will.Terminalle /party/will/Terminalle party.will.Terminalle.Quit
```

In addition to `Toggle` and `Quit`,
there are four methods to move the terminal window between monitors:
`MoveRight`, `MoveLeft`, `MoveDown`, and `MoveUp`,
each of which moves the window to the next adjacent monitor in a particular direction.
This only works while the window is open.
See [shortcuts][6] for info on mapping keybindings to these D-Bus methods.

Use `Ctrl+Shift+C` and `Ctrl+Shift+V` to access the clipboard.

## Install

```bash
$ pip install terminalle

# Optional: start the server automatically on login and restart automatically if exited.
$ terminalle auto

# Optional: disable auto-start (if enabled, this should be done prior to uninstalling).
$ terminalle no-auto
```

### Shortcuts

You almost certainly want to hook up the toggle method to a keybinding for easy access.
In GNOME, you can either do that in the GNOME Control Center (a.k.a "Settings"),
or with `gsettings`:

```bash
# WARNING: Running this verbatim will disable any other custom keybindings.
#          It is merely provided as an example.
$ gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/']"

# WARNING: This will overwrite any existing custom keybinding called 'custom0'.
$ gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ name "Toggle Terminalle"
$ gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ command "dbus-send --session --type=method_call --dest=party.will.Terminalle /party/will/Terminalle party.will.Terminalle.Toggle"
$ gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ binding "<Super>Return"
```

If you use multiple monitors,
considering hooking up shortcuts for the aforementioned movement methods as well.

[KDE][7] can configure shortcuts to call D-Bus methods directly.

## Configuration

See an [example configuration][8]. See the defaults in [`settings.py`][9].
Defaults can be selectively overridden in `${XDG_CONFIG_HOME}/terminalle.yaml`
(typically, `${HOME}/.config/terminalle.yaml`).

## TMUX MODE

This is the recommended way to use Terminalle.
It enables some alternative tmux keyboard shortcuts,
which would normally be impossible to configure in `.tmux.conf`
since terminal emulators typically cannot handle these key combinations.
Generally replacing the tmux prefix with a simple `Ctrl` modifier,
it cuts the number of keystrokes in half
without requiring you to memorize new shortcuts.
If you're a tmux power-user, this will **change** things for you.
Turn it on by setting `tmux: true` in `terminalle.yaml` (see [configuration][10]).

The following shortcuts are enabled in tmux mode:

| tmux default | tmux mode | Command                    |
| -----------: | --------: | :------------------------- |
| `<Prefix> "` |  `Ctrl+"` | `split-window`             |
| `<Prefix> %` |  `Ctrl+%` | `split-window -h`          |
| `<Prefix> {` |  `Ctrl+{` | `swap-pane -U`             |
| `<Prefix> }` |  `Ctrl+}` | `swap-pane -D`             |
| `<Prefix> [` |  `Ctrl+[` | `copy-mode`                |
| `<Prefix> ]` |  `Ctrl+]` | `paste-buffer`             |

To reap maximum benefits, add the following to your `.tmux.conf`,
taking care of other common tmux shortcuts that do not get mangled by typical terminal emulators:

```bash
# Generally shorten `Ctrl+b <X>` to `Ctrl+<X>` for various `<X>`.
bind -n C-Up     resize-pane -U
bind -n C-Down   resize-pane -D
bind -n C-Left   resize-pane -L
bind -n C-Right  resize-pane -R

# Generally shorten `Ctrl+b Meta+<X>` to `Meta+<X>`.
bind -n M-Up     resize-pane -U 5
bind -n M-Down   resize-pane -D 5
bind -n M-Left   resize-pane -L 5
bind -n M-Right  resize-pane -R 5

# Note that `new-window` is not shortened because `Ctrl+c` should send `SIGINT`.
bind -n C-n      next-window
bind -n C-p      previous-window
bind -n C-Space  next-layout
bind -n C-x      confirm-before -p 'kill-pane #P? (y/n)' kill-pane
```

This all goes especially well with [vim-tmux-navigator][11],
which provides shortened bindings for switching seemlessly between tmux panes and Vim windows.

[1]: https://tmux.github.io/
[2]: #tmux-mode
[3]: https://wiki.gnome.org/Apps/Terminal/VTE
[4]: terminalle/terminalle.py
[5]: https://www.freedesktop.org/wiki/Software/dbus/
[6]: #shortcuts
[7]: https://docs.kde.org/trunk5/en/khotkeys/kcontrol/khotkeys/khotkeys.pdf
[8]: terminalle.yaml
[9]: terminalle/settings.py
[10]: #configuration
[11]: https://github.com/christoomey/vim-tmux-navigator
