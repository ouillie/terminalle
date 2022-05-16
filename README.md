# TERMINALLE

A modern, minimalist, semi-transparent fullscreen "drop-down" terminal emulateur
for freedesktop.org-compatible desktops (e.g. GNOME, KDE).

It omits many features common in other terminal emulators, such as tabs,
because it's meant to be used in conjunction with a terminal multiplexer such as [tmux][1],
which has a solid, mature UI.
See also [tmux mode][2] for enhanced tmux features.

Based on [VTE][3].

## Usage

Use [D-Bus][4] to control the application.

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
See [shortcuts][5] for info on mapping keybindings to these D-Bus methods.

Use `Ctrl+Shift+C` and `Ctrl+Shift+V` to access the clipboard.

## Install

```bash
$ pip install terminalle

# Optional: Enable auto-start.
#           Starts the server automatically (window hidden) on login
#           and restarts automatically (also hidden) if exited.
$ terminalle auto

# Optional: Disable auto-start.
#           If enabled, it should be disabled prior to uninstalling.
$ terminalle no-auto
```

### Shortcuts

You almost certainly want to hook up the toggle method to a keybinding for easy access.
In GNOME, you can either do that in the GNOME Control Center (a.k.a "Settings"),
or with `gsettings`:

```bash
# WARNING: Running this verbatim will disable any existing custom keybindings.
#          It's an example.
$ gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/']"

# WARNING: This will overwrite any existing custom keybinding called 'custom0'.
$ gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ name "Toggle Terminalle"
$ gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ command "dbus-send --session --type=method_call --dest=party.will.Terminalle /party/will/Terminalle party.will.Terminalle.Toggle"
$ gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ binding "<Super>Return"
```

If you use multiple monitors,
consider hooking up shortcuts for the aforementioned movement methods as well.

[KDE can][6] configure shortcuts to call D-Bus methods directly.

## Configuration

See an [example configuration][7]. See the defaults in [`settings.py`][8].
Defaults can be selectively overridden in
`${XDG_CONFIG_HOME:-${HOME}/.config}/terminalle.yaml`.

## TMUX MODE

This is the recommended way to use Terminalle.
It enables some alternative tmux keyboard shortcuts,
which would normally be impossible to configure in `.tmux.conf`
since terminal emulators typically cannot handle these key combinations.
Generally replacing the tmux prefix with a simple `Ctrl` modifier,
it cuts the number of keystrokes in half
without requiring you to memorize new shortcuts.
If you're a tmux power-user, this will *change* things for you.
Turn it on by setting `tmux: true` in `terminalle.yaml` (see [configuration][9]).

The following shortcuts are enabled in tmux mode:

| tmux default | tmux mode | Command                                                               |
| -----------: | --------: | :-------------------------------------------------------------------- |
| `<Prefix> !` |  `Ctrl+!` | `break-pane`                                                          |
| `<Prefix> "` |  `Ctrl+"` | `split-window`                                                        |
| `<Prefix> #` |  `Ctrl+#` | `list-buffers`                                                        |
| `<Prefix> $` |  `Ctrl+$` | `command-prompt -I "#S" "rename-session -- '%%'"`                     |
| `<Prefix> %` |  `Ctrl+%` | `split-window -h`                                                     |
| `<Prefix> &` |  `Ctrl+&` | `confirm-before -p "kill-window #W? (y/n)" kill-window`               |
| `<Prefix> '` |  `Ctrl+'` | `command-prompt -T window-target -p "index" "select-window -t ':%%'"` |
| `<Prefix> (` |  `Ctrl+(` | `switch-client -p`                                                    |
| `<Prefix> )` |  `Ctrl+)` | `switch-client -n`                                                    |
| `<Prefix> ,` |  `Ctrl+,` | `command-prompt -I "#W" "rename-window -- '%%'"`                      |
| `<Prefix> :` |  `Ctrl+:` | `command-prompt`                                                      |
| `<Prefix> ;` |  `Ctrl+;` | `last-pane`                                                           |
| `<Prefix> =` |  `Ctrl+=` | `choose-buffer -Z`                                                    |
| `<Prefix> [` |  `Ctrl+[` | `copy-mode`                                                           |
| `<Prefix> ]` |  `Ctrl+]` | `paste-buffer`                                                        |
| `<Prefix> {` |  `Ctrl+{` | `swap-pane -U`                                                        |
| `<Prefix> }` |  `Ctrl+}` | `swap-pane -D`                                                        |

To reap maximum benefits, add the following to your `.tmux.conf`,
taking care of other common tmux shortcuts that do not get mangled by typical terminal emulators:

```bash
# Generally shorten `<Prefix> <X>` to `Ctrl+<X>` for various `<X>`.
# Note that some commands (e.g. `<Prefix> c` for `new-window`) would conflict with
# established control sequences (`Ctrl+c` should send `SIGINT`) if shortened.
bind -n C-f      command-prompt "find-window -Z -- '%%'"
bind -n C-n      next-window
bind -n C-o      select-pane -t ":.+"
bind -n C-p      previous-window
bind -n C-q      display-panes
bind -n C-s      choose-tree -Zs
bind -n C-t      clock-mode
bind -n C-x      confirm-before -p "kill-pane #P? (y/n)" kill-pane
bind -n C-Space  next-layout

# Resize panes using arrow keys and either `Ctrl` or `Meta`.
bind -n C-Up     resize-pane -U
bind -n M-Up     resize-pane -U 5
bind -n C-Down   resize-pane -D
bind -n M-Down   resize-pane -D 5
bind -n C-Left   resize-pane -L
bind -n M-Left   resize-pane -L 5
bind -n C-Right  resize-pane -R
bind -n M-Right  resize-pane -R 5
```

This all goes especially well with [vim-tmux-navigator][10],
which provides shortened bindings for switching seemlessly between tmux panes and Vim windows.

[1]: https://tmux.github.io/
[2]: #tmux-mode
[3]: https://wiki.gnome.org/Apps/Terminal/VTE
[4]: https://www.freedesktop.org/wiki/Software/dbus/
[5]: #shortcuts
[6]: https://docs.kde.org/trunk5/en/khotkeys/kcontrol/khotkeys/khotkeys.pdf
[7]: terminalle.yaml
[8]: terminalle/settings.py
[9]: #configuration
[10]: https://github.com/christoomey/vim-tmux-navigator
