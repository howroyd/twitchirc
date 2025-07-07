#!./.venv/bin/python3
import contextlib
import dataclasses
import datetime
import logging
import multiprocessing as mp
import os
import pathlib
import queue
import socket
import time
from typing import NoReturn, Self

import pydantic.dataclasses as pydataclasses
from rich.logging import RichHandler

from . import bufferedsocket, message

type address_tuple = tuple[str, int]
DEFAULT_SERVER: address_tuple = ("irc.chat.twitch.tv", 6667)


class NoMessageException(Exception):
    """No message received"""

    pass


@pydataclasses.dataclass(slots=True)
class IrcSocket:
    """Wrapper around a socket for reading and writing to the Twitch IRC server"""

    address: address_tuple = dataclasses.field(default_factory=lambda: DEFAULT_SERVER)
    timeout: float = 0.25
    sock: bufferedsocket.BufferedSocket = dataclasses.field(init=False)

    def __post_init__(self):
        self.sock = bufferedsocket.create_connection(self.address, timeout=self.timeout)

    def close(self) -> None:
        """Closes the connection"""
        self.sock.close()

    def read(self) -> str | None:
        """Reads a line from the buffer"""
        b = self.sock.read()
        if b:
            return b.decode("utf-8")
        return None

    def readlines(self) -> list[str]:
        """Reads all lines from the buffer"""
        return [line.decode("utf-8") for line in self.sock.readlines()]

    def write(self, string: str) -> None:
        """Writes a chunk of data to the buffer"""
        self.sock.write(bytes(string, "utf-8"))


class IrcSocketManaged(IrcSocket):
    """Context manager for IrcSocket"""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


@pydataclasses.dataclass(slots=True)
class IrcThreadArgs:
    """Arguments for the IRC thread"""

    address: address_tuple
    timeout: float
    username: str
    oauth: str
    channel: frozenset[str]
    max_timeout: float = 5.0
    queue: mp.Queue = dataclasses.field(default_factory=mp.Queue)
    event: mp.Event = dataclasses.field(default_factory=mp.Event)


def _twitch_irc_thread(args: IrcThreadArgs) -> NoReturn:
    """Thread for reading from Twitch IRC server"""
    while True:
        try:
            logging.info("Connecting to Twitch IRC server")

            with contextlib.ExitStack() as stack:
                irc = stack.enter_context(IrcSocketManaged(args.address, args.timeout))

                irc.write(f"PASS {args.oauth}\r\n")
                irc.write(f"NICK {args.username}\r\n")
                [irc.write(f"JOIN #{channel.strip().lower()}\r\n") for channel in args.channel]

                args.event.set()

                while True:
                    lines = irc.readlines()

                    if not lines:
                        continue

                    logging.debug(lines)

                    for line in lines:
                        if "PING :tmi.twitch.tv" in line:
                            irc.write("PONG :tmi.twitch.tv\r\n")
                        else:
                            args.queue.put(line)

        except (OSError, TimeoutError, socket.gaierror, ConnectionResetError, ConnectionAbortedError) as e:
            logging.error(f"Error in Twitch IRC thread: {e}")
            args.event.clear()
            args.timeout = min(args.max_timeout, args.timeout * 2)
            time.sleep(1)


class TwitchIrcConnectionError(Exception):
    """Failed to connect to the Twitch IRC Server"""

    pass


class TwitchIrc:
    """Context manager for connecting to Twitch IRC server"""

    def __init__(self, channel: frozenset[str], username: str | None = None, oauth: str | None = None, timeout: float = None):
        if not channel or channel.issubset(frozenset([""])):
            raise TwitchIrcConnectionError("No channels specified")
        self._processdata = IrcThreadArgs(
            address=("irc.chat.twitch.tv", 6667), timeout=0.25, username=username or "justinfan97339", oauth=oauth or "gfdszgfds", channel=channel
        )
        self._process: mp.Process | None = None
        self.timeout: float = timeout or 20.0

    @property
    def queue(self) -> mp.Queue:
        """Returns the queue of messages from the IRC server"""
        return self._processdata.queue

    @property
    def connected(self) -> bool:
        """Returns True if the connection is established"""
        return self._processdata.event.is_set()

    def start(self, *, wait_for_connection: bool = True) -> None:
        """Starts the connection to Twitch IRC server"""
        self._process = mp.Process(target=_twitch_irc_thread, args=(self._processdata,))
        self._process.start()

        if wait_for_connection and not self._processdata.event.wait(self.timeout):
            raise TwitchIrcConnectionError(f"Failed to connect to Twitch IRC server after {self.timeout} seconds")

    def stop(self) -> None:
        """Forcibly terminate the connection.  May deadlock anyone waiting on the queue"""
        #  FIXME - This is a bit of a hack.  We should probably send a message to the thread to tell it to stop
        self._process.terminate() if self._process else None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    @staticmethod
    def get_message(irc: Self, *, timeout: float = 0.1) -> message.TwitchMessage | None:
        """Returns a message from the IRC server, or None if no message is available"""
        msg: message.TwitchMessage | None = None
        try:
            queue_msg = irc.queue.get(timeout=timeout)
            msg = message.TwitchMessage.from_irc_message(queue_msg) if queue_msg else None
            if not msg:
                raise NoMessageException
        except (NoMessageException, queue.Empty):
            pass
        return msg


if __name__ == "__main__":
    IRC_LOGFILE = os.getenv("IRC_LOGFILE", None)

    log_handlers = [
        RichHandler(rich_tracebacks=True, markup=True, show_time=True, show_path=False, show_level=True),
    ]
    if IRC_LOGFILE:
        logpath = pathlib.Path().parent.resolve() / "logs"
        logpath.mkdir(parents=True, exist_ok=True)
        file_logger = logging.FileHandler(logpath / IRC_LOGFILE, mode="a", encoding="utf-8")
        file_logger.setFormatter(logging.Formatter("%(asctime)s|%(levelname)s|%(message)s"))
        log_handlers.append(file_logger)

    logging.basicConfig(level="NOTSET", format="%(message)s", handlers=log_handlers)

    # testchannels = frozenset([""])
    testchannels = frozenset(["drgreengiant"])

    with TwitchIrc(testchannels) as irc:
        while True:
            msg = message.TwitchMessage.from_irc_message(irc.queue.get())

            if msg:
                logging.debug(msg)
