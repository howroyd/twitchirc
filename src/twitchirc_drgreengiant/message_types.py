import enum
from typing import Self


@enum.unique
class TwitchMessageEnum(enum.Enum):
    """Message types defined by Twitch IRC server
    Ref: https://dev.twitch.tv/docs/irc/example-parser
    """

    JOIN = enum.auto()
    PART = enum.auto()
    NOTICE = enum.auto()
    CLEARCHAT = enum.auto()
    HOSTTARGET = enum.auto()
    PRIVMSG = enum.auto()
    PING = enum.auto()
    CAP = enum.auto()
    GLOBALUSERSTATE = enum.auto()
    USERSTATE = enum.auto()
    ROOMSTATE = enum.auto()
    RECONNECT = enum.auto()
    NUMERIC = enum.auto()  # All numerics lumped in here.  Extend if required

    @classmethod
    def match_message_type(cls, string_to_match: str) -> Self | None:
        """Matches the message type to the TwitchMessageEnum"""
        match string_to_match.strip().upper():
            case "JOIN":
                return cls.JOIN
            case "PART":
                return cls.PART
            case "NOTICE":
                return cls.NOTICE
            case "CLEARCHAT":
                return cls.CLEARCHAT
            case "HOSTTARGET":
                return cls.HOSTTARGET
            case "PRIVMSG":
                return cls.PRIVMSG
            case "PING":
                return cls.PING
            case "CAP":
                return cls.CAP
            case "GLOBALUSERSTATE":
                return cls.GLOBALUSERSTATE
            case "USERSTATE":
                return cls.USERSTATE
            case "ROOMSTATE":
                return cls.ROOMSTATE
            case "RECONNECT":
                return cls.RECONNECT
            case "421" | "001" | "002" | "003" | "004" | "353" | "366" | "372" | "375" | "376":
                return cls.NUMERIC
            case _:
                return None
