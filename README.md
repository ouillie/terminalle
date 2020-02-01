
It's just a fullscreen terminal emulator that supports transparency.

It omits many features,
because it's meant to be used in conjunction with a terminal multiplexer
such as [tmux](https://github.com/tmux/tmux).

### Usage

```bash
# See usage info.
$ python -m terminalle --help

# Start the server. The window is initially hidden by default.
$ python -m terminalle &

# Toggle window visibility.
$ dbus-send --session --type=method_call --dest=org.gnome.Terminalle /termctl \
      org.gnome.Terminalle.Toggle

# Close the window and kill the server.
$ dbus-send --session --type=method_call --dest=org.gnome.Terminalle /termctl \
      org.gnome.Terminalle.Quit
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
In gnome, you can do that with `gsettings`:

```bash
# WARNING: This will disable any other custom keybindings.
$ gsettings set org.gnome.settings-daemon.plugins.media-keys \
     custom-keybindings "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/']"
# WARNING: This will overwrite any existing custom keybinding called 'custom0'.
$ gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ \
     name "Toggle Terminalle"
$ gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ \
     command "dbus-send --session --type=method_call --dest=org.gnome.Terminalle /termctl org.gnome.Terminalle.Toggle"
$ gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ \
     binding "<Super>Return"
```

### Configuration

See an [example configuration](terminalle.yaml).
See the defaults in [`settings.py`](terminalle/settings.py).
Defaults can be overridden in `${HOME}/.config/terminalle.yaml`.
