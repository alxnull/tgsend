# tgsend - Telegram Messaging Tool

[![PyPI](https://img.shields.io/pypi/v/tgsend.svg)](https://pypi.org/project/tgsend/)
[![GitHub](https://img.shields.io/github/license/alxnull/tgsend.svg)](https://github.com/alxnull/tgsend/blob/master/LICENSE.txt)

tgsend is a little Python module to send messages, photos and documents to Telegram chats via a Telegram bot. tgsend can be used either as a command line tool or as a module for Python 3.

## Quick Start (Command Line)

1. Create a Telegram Bot with the help of [@BotFather](https://t.me/BotFather) and take note of the bot token.
2. Start a new chat with your bot or add it to a group where the messages should be sent to.
Find out your personal chat ID or the chat ID of the group chat, e.g. by using [@Echo_ID_Bot](https://t.me/Echo_ID_Bot).
_Important:_ Telegram Bots are shy, so you have to send the first message in a chat with them.
3. Install tgsend with pip:
```bash
sudo pip3 install tgsend
```
4. Quickly configure tgsend with environment variables (see [Configuration](#configuration) for other options). In bash:
```bash
TGSEND_TOKEN=abcdefg # your bot token
TGSEND_CHATID=1234567 # the chat ID of the private/ group chat
```
5. Test it:
```bash
tgsend "Hello World"
```

## Usage

### From Command Line

Send a text message with formatting:
```bash
tgsend --format markdown "This is a text with *bold* and _italic_ words."
```

Add a title and an icon:
```bash
tgsend -t "Title" --icon $'\u2705' "Some text."
```

Send a picture:
```bash
tgsend --photo image.png "Image description."
```

Send a file:
```bash
tgsend --doc log.txt "Log file"
```

Send a video:
```bash
tgsend --video video.mp4 "Video caption"
```

Send a sticker:
```bash
tgsend --sticker sticker.webp
```

Read from stdin:
```bash
cat greeting.txt | tgsend -
```

Type `tgsend --help` to see all options.

### In Python
Example:
```python
from tgsend import Telegram, ParseMode
# token and chat ID will be searched in config files if not specified here
telegram = Telegram("your-bot-token", "your-chat-id")
# send a text message
telegram.send_message(
    "This is a text with *bold* and _italic_ words.",
    title="The Title",
    parse_mode=ParseMode.MARKDOWN
)
```

## Configuration

A configuration for tgsend always consists of a bot token and a chat ID.
These values can be either set through environment variables (as shown above) or through a configuration file.

### Per-user and global configuration

You can place a per-user configuration file at `~/tgsend.conf` and a global configuration file at `/etc/tgsend.conf`.
If no environment variables are specified, tgsend will look for the required values in these files in the given order.
The format of this configuration file should look like this:
```
[Default]
BotToken = your_bot_token
ChatID = your_chat_id
```

### More configuration options

You can add additional bot token/ chat ID profiles by adding a config section to the configuration file, e.g.:
```
[AltConfig]
BotToken = different_bot_token
ChatID = another_chat_id
```
You can then simply switch to this configuration with the `-c` option:
```bash
tgsend -c AltConfig "Hello World"
```

It is also possible to specify a different location for the configuration file by using the `-l` option. E.g.:
```bash
tgsend -l ~/tgsend/botconfig.conf "Some text"
```
tgsend will now look for the `[Default]` section in the given configuration file.

## License

This software is pusblished under [BSD-3-Clause license](https://github.com/alxnull/tgsend/blob/master/LICENSE.txt).
