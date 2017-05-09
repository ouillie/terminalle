
from threading import Thread
from socket import socket, AF_UNIX, SOCK_STREAM, timeout as TimeoutError
from os import remove
from contextlib import suppress
from typing import Callable

_toggle_msg = b't'
_quit_msg = b'q'
_ack_msg = b'a'
_kill_msg = b'k'

class ServerAlreadyRunningError(RuntimeError):
    pass

def serve(path: str,
          force: bool,
          timeout: float,
          run_fn: Callable,
          toggle_fn: Callable,
          quit_fn: Callable):
    """ Bind to a unix domain socket at `path`,
        On binding, spawn a new thread to listen for connections,
        invoking `toggle_fn` upon receiving toggle messages,
        `quit_fn` upon receiving quit messages,
        and always respond with ack messages.
        After starting the listening process,
        invoke `run_fn` on the original process and return its return value.
    """
    sock = socket(family=AF_UNIX, type=SOCK_STREAM)
    try:
        try:
            sock.bind(path)
        except OSError:
            if force:
                with suppress(FileNotFoundError):
                    remove(path)
                try:
                    sock.bind(path)
                except OSError:
                    raise RuntimeError(f'too much contention on \'{path}\'')
            else:
                raise ServerAlreadyRunningError(f'socket \'{path}\' is occupied')
        sock.listen()
        listener = Thread(target=_listen,
                          args=(sock, timeout, toggle_fn, quit_fn))
        listener.start()
        try:
            r = run_fn()
        finally:
            _kill_listener(path, timeout)
            listener.join()
        return r
    finally:
        try:
            sock.close()
        finally:
            with suppress(FileNotFoundError):
                remove(path)

def _listen(sock: socket,
            timeout: float,
            toggle_fn: Callable,
            quit_fn: Callable):
    while True:
        try:
            s, _ = sock.accept()
            try:
                s.settimeout(timeout)
                msg = s.recv(1)
                s.send(_ack_msg)
            except (TimeoutError, BrokenPipeError):
                continue
            else:
                if msg == _toggle_msg:
                    toggle_fn()
                elif msg == _quit_msg:
                    quit_fn()
                elif msg == _kill_msg:
                    break
            finally:
                s.close()
        except OSError:
            # Probably because the socket file was closed.
            raise

def _kill_listener(path: str, timeout: float):
    sock = socket(family=AF_UNIX, type=SOCK_STREAM)
    try:
        sock.settimeout(timeout)
        sock.connect(path)
        sock.sendall(_kill_msg)
        # No need to check the ack at this point.
        sock.recv(1)
    except (BrokenPipeError, PermissionError, FileNotFoundError, TimeoutError):
        # Server socket closed since connection,
        # or caller does not have access to `path`,
        # or `path` no longer exists,
        # or timed out while sending or receiving.
        return
    finally:
        sock.close()
