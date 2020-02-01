
It's just a big transparent terminal window over everything.

### Usage

```bash
# See usage info.
python -m terminalle --help
# Start the server. The window is initially hidden by default.
python -m terminalle &

# Toggle window visibility.
dbus-send --session --type=method_call --dest=org.gnome.Terminalle /termctl \
    org.gnome.Terminalle.Toggle

# Close the window and kill the server.
dbus-send --session --type=method_call --dest=org.gnome.Terminalle /termctl \
    org.gnome.Terminalle.Quit
```

### Configuration

See example configuration in `terminalle.yaml`.
Defaults can be overridden in `~/.config/terminalle.yaml`.
By default, `shell` is taken from the `${SHELL}` environment variable,
and `home` is taken from `${HOME}`.
