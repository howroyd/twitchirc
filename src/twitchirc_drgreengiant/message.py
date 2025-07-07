from typing import Protocol, Self

import pydantic.dataclasses as pydataclasses

from . import message_types


@pydataclasses.dataclass(frozen=True, slots=True)
class TwitchMessageProto(Protocol):
    """Protocol definition for TwitchMessage"""

    username: str
    channel: str
    payload: str


@pydataclasses.dataclass(frozen=True, slots=True)
class TwitchMessage:
    """Represents a message from Twitch IRC server"""

    type: message_types.TwitchMessageEnum
    username: str
    channel: str
    payload: str

    @classmethod
    def from_irc_message(cls, irc_msg: str) -> Self | None:
        """Creates a TwitchMessage from an IRC message"""
        msg_type = message_types.TwitchMessageEnum.match_message_type(irc_msg.split(maxsplit=2)[1])

        if msg_type is None or msg_type == message_types.TwitchMessageEnum.NUMERIC:  # TODO should we keep numerics?
            return None

        line_split = irc_msg.split(maxsplit=3)
        idx_of_msg_type = line_split.index(msg_type.name)

        # Remove the username and PRIVMSG from the line
        line = line_split[idx_of_msg_type + 1 :]

        if len(line) != 2:
            return None

        return cls(type=msg_type, username=line_split[0].split("!")[0].lstrip(":"), channel=line[0].lstrip("#"), payload=line[1].lstrip(":").rstrip("\r\n"))
