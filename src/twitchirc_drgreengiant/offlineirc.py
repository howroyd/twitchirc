#!./.venv/bin/python3
import dataclasses
import multiprocessing as mp
import queue
import sys
from typing import NoReturn, Self

from . import twitchirc


@dataclasses.dataclass(slots=True)
class OfflineIrcThreadArgs:
    """Arguments to pass to the offline IRC thread"""
    username: str
    channel: frozenset[str]
    queue: mp.Queue = dataclasses.field(default_factory=mp.Queue)


def _offline_irc_thread(args: OfflineIrcThreadArgs) -> NoReturn:
    """Thread for offline IRC connection
    Rather than reading from the IRC server, we read from stdin
    """
    sys.stdin = open(0)

    while True:
        userinput = sys.stdin.readline().strip()

        msg = twitchirc.TwitchMessage(
            twitchirc.TwitchMessageEnum.PRIVMSG,
            args.username,
            next(iter(args.channel)),
            userinput
        )

        args.queue.put(msg)


class OfflineIrc:
    """Context manager for offline IRC connection which reads from stdin rather than the IRC server"""

    def __init__(self, channel: frozenset[str], username: str | None = None):
        if not channel or channel.issubset(frozenset([""])):
            raise twitchirc.TwitchIrcConnectionError("No channels specified")
        self._processdata = OfflineIrcThreadArgs(
            username=username or "justinfan97339",
            channel=channel
        )
        self._process: mp.Process | None = None

    @property
    def queue(self) -> mp.Queue:
        """Returns the queue of messages from stdin"""
        return self._processdata.queue

    @staticmethod
    def get_message(irc: Self, *, timeout: float = 0.1) -> twitchirc.TwitchMessage | None:
        """Returns a message from stdin, or None if no message is available"""
        msg: twitchirc.TwitchMessage | None = None
        try:
            msg = irc.queue.get(timeout=timeout)
            if not msg:
                raise twitchirc.NoMessageException
        except (twitchirc.NoMessageException, queue.Empty):
            pass
        return msg

    def start(self) -> None:
        """Starts the connection to pretend IRC server"""
        self._process = mp.Process(target=_offline_irc_thread, args=(self._processdata,))
        self._process.start()

    def stop(self) -> None:
        """Forcibly terminate the connection.  May deadlock anyone waiting on the queue"""
        #  FIXME - This is a bit of a hack.  We should probably send a message to the thread to tell it to stop
        self._process.terminate() if self._process else None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()
