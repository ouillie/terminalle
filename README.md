# Terminalle

A modern, minimalist, semi-transparent, fullscreen "drop-down" terminal emulateur
for [freedesktop.org]-compatible desktops (e.g. GNOME, KDE, Cinnamon).

It omits many features common in other terminal emulators, such as tabs,
because it's meant to be used in conjunction with a terminal multiplexer such as [tmux],
which has a solid, mature UI.
See also [tmux mode] for enhanced tmux features.

Based on [VTE].

[freedesktop.org]: https://freedesktop.org
[tmux]: https://tmux.github.io
[tmux mode]: #tmux-mode
[VTE]: https://wiki.gnome.org/Apps/Terminal/VTE

## Dependencies

<details>
<summary><strong>Arch</strong></summary>

```bash
pacman -S gtk4 vte4 python-gobject python-yaml
```

</details>

<details>
<summary><strong>Debian / Ubuntu</strong></summary>

```bash
apt install gir1.2-gtk-4.0 gir1.2-vte-3.91 python3-gi python3-yaml
```

</details>

<details>
<summary><strong>Fedora</strong></summary>

```bash
dnf install gtk4 python3-gobject python3-pyyaml
```

</details>

<details>
<summary><strong>Other systems</strong></summary>

Install these dependencies:

- [GTK-4](https://www.gtk.org/)
- [VTE](https://wiki.gnome.org/Apps/Terminal/VTE)
- [PyGObject](https://pygobject.gnome.org/)
- [PyYAML](https://pyyaml.org/)

</details>

## Install

```bash
pip install terminalle

# Recommended: Enable auto-start.
# Starts the server automatically (window hidden) on login
# and restarts automatically on toggle if closed.
terminalle auto
```

## Usage

Whichever process runs `terminalle` is the "server".

```bash
# See usage info.
terminalle --help

# Start the server (in this case, as a background job).
# The window is initially hidden by default.
# This is unnecessary if you've enabled auto-start with `terminalle auto`.
terminalle &
```

When toggled on, the terminal window opens on the monitor where the mouse is located.
To move it to a different monitor, move the mouse, then toggle it on again.
Wayland does not allow applications to position their own windows.

Use `Ctrl+Shift+C` and `Ctrl+Shift+V` to access the clipboard.

### Shortcuts

If you use GNOME or KDE,
Terminalle can manage keyboard shortcuts for you:

```bash
# This example enables 2 keyboard shortcuts to toggle the window,
# and 1 keyboard shortcut to shut down the server.
terminalle key --toggle '<Super>Return' --toggle '<Alt>Return' --quit <Super>Backspace'
```

For any other kind of dekstop environment,
you'll have to set up your own shortcuts to invoke these [D-Bus] methods:

```bash
# Toggle window visibility.
dbus-send --session --type=method_call --dest=party.will.Terminalle \
    /party/will/Terminalle party.will.Terminalle.Toggle

# Close the window and kill the server.
dbus-send --session --type=method_call --dest=party.will.Terminalle \
    /party/will/Terminalle party.will.Terminalle.Quit
```

[D-Bus]: https://www.freedesktop.org/wiki/Software/dbus

### Uninstall

```bash
# If enabled, auto-start should be disabled prior to uninstalling.
# Also disable any keyboard shortcuts.
terminalle no-auto
terminalle no-key

pip uninstall terminalle
```

## Configuration

See an [example configuration]. See the defaults in [`settings.py`].
Defaults can be selectively overridden in
`${XDG_CONFIG_HOME:-${HOME}/.config}/terminalle.yaml`.

[example configuration]: terminalle.yaml
[`settings.py`]: terminalle/settings.py

## TMUX MODE

This is the recommended way to use Terminalle.
It enables some alternative tmux keyboard shortcuts,
which would normally be impossible to configure in `.tmux.conf`
since terminal emulators typically cannot handle these key combinations.
Generally replacing the tmux prefix with a simple `Ctrl` modifier,
it cuts the number of keystrokes in half
without requiring you to memorize new shortcuts.
If you're a tmux power-user, this will *change* things for you.
Turn it on by setting `tmux: true` in `terminalle.yaml` (see [configuration]).

The following shortcuts are enabled in tmux mode:

| tmux default | tmux mode | Command                                                            |
| -----------: | --------: | :----------------------------------------------------------------- |
| `<Prefix> !` |  `Ctrl+!` | `break-pane`                                                       |
| `<Prefix> "` |  `Ctrl+"` | `split-window`                                                     |
| `<Prefix> #` |  `Ctrl+#` | `list-buffers`                                                     |
| `<Prefix> $` |  `Ctrl+$` | `command-prompt -I "#S" "rename-session -- '%%'"`                  |
| `<Prefix> %` |  `Ctrl+%` | `split-window -h`                                                  |
| `<Prefix> &` |  `Ctrl+&` | `confirm-before -p "kill-window #W? (y/n)" kill-window`            |
| `<Prefix> '` |  `Ctrl+'` | `command-prompt -T window-target -pindex "select-window -t ':%%'"` |
| `<Prefix> (` |  `Ctrl+(` | `switch-client -p`                                                 |
| `<Prefix> )` |  `Ctrl+)` | `switch-client -n`                                                 |
| `<Prefix> ,` |  `Ctrl+,` | `command-prompt -I "#W" "rename-window -- '%%'"`                   |
| `<Prefix> .` |  `Ctrl+.` | `command-prompt -T target "move-window -t '%%'"`                   |
| `<Prefix> :` |  `Ctrl+:` | `command-prompt`                                                   |
| `<Prefix> ;` |  `Ctrl+;` | `last-pane`                                                        |
| `<Prefix> =` |  `Ctrl+=` | `choose-buffer -Z`                                                 |
| `<Prefix> [` |  `Ctrl+[` | `copy-mode`                                                        |
| `<Prefix> ]` |  `Ctrl+]` | `paste-buffer`                                                     |
| `<Prefix> {` |  `Ctrl+{` | `swap-pane -U`                                                     |
| `<Prefix> }` |  `Ctrl+}` | `swap-pane -D`                                                     |

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

This all goes especially well with [Vim Tmux Navigator],
which provides shortened bindings for switching seemlessly between tmux panes and Vim windows.

[configuration]: #configuration
[Vim Tmux Navigator]: https://github.com/christoomey/vim-tmux-navigator
