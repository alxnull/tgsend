#!/usr/bin/env python3

__version__ = '0.1'

import requests
import configparser
from os.path import isfile, abspath, expanduser
import os
import sys

CONFIG_FILE = '/etc/tgsend.conf'
TOKEN = os.environ.get('TGSEND_TOKEN')
CHAT_ID = os.environ.get('TGSEND_CHATID')

class ParseMode:
    NONE = ""
    MARKDOWN = "markdown"
    HTML = "html"

class Telegram:
    """Send messages to Telegram chats via a bot.
    
    :param token: The bot token of the bot (read from env var or config file if not specified), defaults to None
    :param token: str, optional
    :param chat_id: The ID of the chat messages should be sent to, defaults to None
    :param chat_id: str, optional
    :raises RuntimeError: If no valid token and chat ID configuration was found
    """
    
    icons = { 
        'warn': '\U000026A0', 
        'alert': '\U0001f198', 
        'info': '\U0001f4cb', 
        'error': '\u274c', 
        'success': '\u2705', 
        'no': ""}

    _req_url = "https://api.telegram.org/bot"

    def __init__(self, token=None, chat_id=None):
        self.token, self.chat_id = token or TOKEN, chat_id or CHAT_ID
        if not self.token or not self.chat_id:
            try:
                token_read, chat_read = Telegram._read_config('Default')
                if not self.token:
                    self.token = token_read
                if not self.chat_id:
                    self.chat_id = chat_read
            except:
                pass
        if not (self.token and self.chat_id):
            raise RuntimeError("Could not find a valid configuration with BotToken and ChatID.")

    @classmethod
    def load(cls, name='Default', config_file=None):
        """Load a bot token and chat id configuration from file.
        
        :param name: The name of the config section to be loaded, defaults to 'Default'
        :param name: str, optional
        :param config_file: The path to the config file, defaults to '/etc/tgsend.conf'
        :param config_file: str, optional
        :raises RuntimeError: If the given configuration could not be found
        :return: An object of Telegram class used for sending messages
        :rtype: tgsend.Telegram
        """
        token, chat_id = Telegram._read_config(name, config_file)
        if not token or not chat_id:
            raise RuntimeError("Given configuration '{}' not available".format(name))
        return cls(token, chat_id)

    def _read_config(name, custom_config_file=None):
        config_file = expanduser(custom_config_file) if custom_config_file else CONFIG_FILE
        config_file = abspath(config_file)
        if isfile(config_file):
            config = configparser.ConfigParser()
            config.read(config_file)
            if name in config:
                current = config[name]
                if 'BotToken' in current and 'ChatID' in current:
                    return current['BotToken'], current['ChatID']
            return None, None
        else:
            raise RuntimeError("Configuration file '{}' could not be found.".format(config_file))

    def _bold(self, text, parse_mode):
        if parse_mode == ParseMode.HTML:
            return "<b>{}</b>".format(text)
        elif parse_mode == ParseMode.MARKDOWN:
            return "*{}*".format(text)
        else:
            return text

    def _fixed(self, text, parse_mode):
        if parse_mode == ParseMode.HTML:
            return "<code>{}</code>".format(text)
        elif parse_mode == ParseMode.MARKDOWN:
            return "`{}`".format(text)
        else:
            return text

    def _text(self, text, title, parse_mode, icon):
        s = icon + " "
        if title:
            s += self._bold(title, parse_mode) + "\n"
            s += self._bold("-" * 15, parse_mode) + "\n"
        return s + text

    def send_message(self, text, title="", parse_mode=ParseMode.MARKDOWN, level="no", icon="", silent=False, fixed=False, web_page_preview=True):
        """Send a text message to a Telegram chat.
        
        :param text: Text of the message to be sent
        :type text: str
        :param title: Title of the message, defaults to ""
        :param title: str, optional
        :param parse_mode: Text formatting of the message, defaults to ParseMode.MARKDOWN
        :param parse_mode: str, optional
        :param level: Log level (warn, alert, info, error, success, no), defaults to "no"
        :param level: str, optional
        :param icon: A unicode icon to be placed next to the title, defaults to ""
        :param icon: str, optional
        :param silent: Send the message silently, defaults to False
        :param silent: bool, optional
        :param fixed: Format message as fixed-width text, defaults to False
        :param fixed: bool, optional
        :param web_page_preview: Disable link previews, defaults to True
        :param web_page_preview: bool, optional
        :return: Response object of sent request
        :rtype: requests.Response
        """
        s = self._text(text, title, parse_mode, icon if icon else Telegram.icons[level])
        if fixed:
            s = self._fixed(s, parse_mode)
        params = { 'chat_id': self.chat_id, 'parse_mode':  parse_mode, 'text': s, 
            'disable_notification': str(silent), "disable_web_page_preview": str(web_page_preview) }
        return requests.get(Telegram._req_url  + self.token + "/sendMessage", params=params)

    def send_photo(self, photo, text=None, title="", parse_mode=ParseMode.MARKDOWN, level="no", icon="", silent=False):
        """Send a photo to a Telegram chat.
        
        :param photo: Path to the photo to be sent
        :type photo: str
        :param text: Photo caption, defaults to None
        :param text: str, optional
        :param title: Title of the message, defaults to ""
        :param title: str, optional
        :param parse_mode: Text formatting of the message, defaults to ParseMode.MARKDOWN
        :param parse_mode: str, optional
        :param level: Log level (warn, alert, info, error, success, no), defaults to "no"
        :param level: str, optional
        :param icon: A unicode icon to be placed next to the title, defaults to ""
        :param icon: str, optional
        :param silent: Send the message silently, defaults to False
        :param silent: bool, optional
        :return: Response object of sent request
        :rtype: requests.Response
        """
        self.s
        s = self._text(text or "", title, parse_mode, icon if icon else Telegram.icons[level])
        params = { 'chat_id': self.chat_id, 'parse_mode':  parse_mode, 'caption': s,
            'disable_notification': str(silent)}
        files = {'photo': open(photo, 'rb')}
        return requests.post(Telegram._req_url + self.token + "/sendPhoto", data=params, files=files)

    def send_document(self, document, text=None, title="", parse_mode=ParseMode.MARKDOWN, level="no", icon="", silent=False):
        """Send a file to a Telegram chat.
        
        :param document: Path to the file to be sent
        :type document: str
        :param text: Photo caption, defaults to None
        :param text: str, optional
        :param title: Title of the message, defaults to ""
        :param title: str, optional
        :param parse_mode: Text formatting of the message, defaults to ParseMode.MARKDOWN
        :param parse_mode: str, optional
        :param level: Log level (warn, alert, info, error, success, no), defaults to "no"
        :param level: str, optional
        :param icon: A unicode icon to be placed next to the title, defaults to ""
        :param icon: str, optional
        :param silent: Send the message silently, defaults to False
        :param silent: bool, optional
        :return: Response object of sent request
        :rtype: requests.Response
        """
        s = self._text(text or "", title, parse_mode, icon if icon else Telegram.icons[level])        
        params = { 'chat_id': self.chat_id, 'parse_mode':  parse_mode, 'caption': s,
            'disable_notification': str(silent)}
        files = {'document': open(document, 'rb')}
        return requests.post(Telegram._req_url + self.token + "/sendDocument", data=params, files=files)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Simple tool to send messages to a telegram chat.")
    parser.add_argument('text', help="the text to be send", nargs='?')
    parser.add_argument('-l', '--load', default=None, help="specify a configuration file different from the default config")
    parser.add_argument('-c', '--config', default=None, help="specify the bot configuration to be loaded")
    parser.add_argument('--id', default="", help="override the chat id from the loaded configuration")
    parser.add_argument('-t', '--title', default="", help="title of the message")
    parser.add_argument('--format', default="markdown", choices=['html', 'markdown', 'none'],
                        help="the formatting used for the text (default: markdown)", dest="parse_mode")
    parser.add_argument('--silent', help="sends message without notification", action="store_true")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--photo', '-p', help="path to a picture to be sent")
    group.add_argument('--doc', '-d', help="path to a document to be sent")
    parser.add_argument('--icon', default="", help="Unicode of an icon placed beside the title of the message")
    parser.add_argument('--lvl', default='no', choices=['success', 'info', 'warn', 'error', 'alert', 'no'],
                        help="log level of the message (icon overriden by --icon)", dest="level")
    parser.add_argument('--fixed', help="format message as fixed-width text", action="store_true")
    parser.add_argument('--no-preview', help="disable link previews", action="store_true", dest="preview")
    parser.add_argument('-v', '--verbose', help="always print out return message" , action="store_true")
    parser.add_argument('--version', version="tgsend v.{}".format(__version__), action='version')
    args = parser.parse_args()
    if args.config:
        telegram = Telegram.load(args.config, args.load)
    elif args.load:
        telegram = Telegram.load(config_file=args.load)
    else:
        telegram = Telegram()
    if args.id:
        telegram.chat_id = args.id
    if args.photo:
        response = telegram.send_photo(args.photo, args.text, args.title, args.parse_mode,
        args.level, args.icon, args.silent)
    elif args.doc:
        response = telegram.send_document(args.doc, args.text, args.title, args.parse_mode,
        args.level, args.icon, args.silent)
    else:
        text = sys.stdin.read() if args.text == "-" else args.text
        response = telegram.send_message(text, args.title, args.parse_mode,
        args.level, args.icon, args.silent, fixed=args.fixed, web_page_preview=args.preview)
    failure = not response.json()["ok"]
    if args.verbose or failure:
        print(response.text)

if __name__ == "__main__":
    main()
