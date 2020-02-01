
It's just a big transparent terminal window over everything.

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

### Configuration

See an [example configuration](terminalle.yaml).
See the defaults in [`settings.py`](terminalle/settings.py).
Defaults can be overridden in `${HOME}/.config/terminalle.yaml`.
