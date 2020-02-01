
It's just a big, semi-transparent terminal window over everything.

### Install

```bash
$ sudo pip install .
```

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

You'll probably want to hook up the toggle method to a keybinding.

### Configuration

See an [example configuration](terminalle.yaml).
See the defaults in [`settings.py`](terminalle/settings.py).
Defaults can be overridden in `${HOME}/.config/terminalle.yaml`.
