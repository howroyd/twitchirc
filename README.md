# TwitchIRC

[![CodeQL Vulnerabilities](https://github.com/howroyd/twitchirc/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/howroyd/twitchirc/actions/workflows/codeql-analysis.yml)\
[![Linting and Testing](https://github.com/howroyd/twitchirc/actions/workflows/python-testing.yml/badge.svg)](https://github.com/howroyd/twitchirc/actions/workflows/python-testing.yml)\
[![Build and Release](https://github.com/howroyd/twitchirc/actions/workflows/python-publish.yml/badge.svg)](https://github.com/howroyd/twitchirc/actions/workflows/python-publish.yml)

This module connects to the Twitch IRC as a basic listener client.  It handles the ping pong and initial connection but otherwise does not send anything to Twitch therefore does not appear in the viewer list nor can it post to chat.  As such, no oauth is required, it just works out of the box.

It can join multiple channels at the same time and will report which channel a message was received in.

## Installation

Available on PyPi at https://pypi.org/project/twitchirc-drgreengiant/

```bash
pip install twitchirc_drgreengiant
```

## Typical Usage

```python
from twitchirc_drgreengiant import twitchirc

channels = frozenset(["drgreengiant", "hpxdreamer"])

with twitchirc.TwitchIrc(channels) as irc:
    while True:
        msg = irc.get_message(irc)

        if not msg:
            continue

        print("Received a message:")
        print(f"{msg.channel=} from {msg.username=}")
        print(f"{msg.payload=}")
        print()
```
