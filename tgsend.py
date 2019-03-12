#!/usr/bin/env python3

__version__ = '0.2'

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
    
    _icons = { 
        'warn': '\U000026A0', 
        'alert': '\U0001f198', 
        'info': '\U0001f4cb', 
        'error': '\u274c', 
        'success': '\u2705', 
        'no': ""}

    _req_url = "https://api.telegram.org/bot"

    def __init__(self, token=None, chat_id=None):
        self.token, self.chat_id = token or TOKEN, chat_id or CHAT_ID
        if not self.token:
            try:
                token_read, chat_read = Telegram._read_config('Default')
                if not self.token:
                    self.token = token_read
                if not self.chat_id:
                    self.chat_id = chat_read
            except:
                pass
        if not self.token:
            raise RuntimeError("Could not find a valid configuration with BotToken.")

    @classmethod
    def load(cls, name='Default', config_file=None):
        """Load a bot token and chat id configuration from file.
        """
        token, chat_id = Telegram._read_config(name, config_file)
        if not token:
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
                token = current['BotToken'] if 'BotToken' in current else None
                chat = current['ChatID'] if 'ChatID' in current else None
                return token, chat
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

    def send_message(self, text, title="", parse_mode=ParseMode.MARKDOWN, level="no", icon="", silent=False, fixed=False, web_page_preview=True, chat_id=None):
        """Send a text message to a Telegram chat.
        """
        if not self.chat_id and not chat_id:
            raise RuntimeError("No chat ID specified.")
        s = self._text(text, title, parse_mode, icon if icon else Telegram._icons[level])
        if fixed:
            s = self._fixed(s, parse_mode)
        params = { 'chat_id': chat_id or self.chat_id, 'parse_mode':  parse_mode, 'text': s, 
            'disable_notification': str(silent), "disable_web_page_preview": str(web_page_preview) }
        return requests.get(Telegram._req_url  + self.token + "/sendMessage", params=params)

    def _send_file_helper(self, chat_id, method, files, text, title, p_m, lvl, icon, silent):
        if not self.chat_id and not chat_id:
            raise RuntimeError("No chat ID specified.")
        s = self._text(text or "", title, p_m, icon if icon else Telegram._icons[lvl])
        params = { 'chat_id': chat_id or self.chat_id, 'parse_mode':  p_m, 'caption': s,
            'disable_notification': str(silent)}
        return requests.post(Telegram._req_url + self.token + method, data=params, files=files)

    def send_photo(self, photo, text=None, title="", parse_mode=ParseMode.MARKDOWN, level="no", icon="", silent=False, chat_id=None):
        """Send a photo to a Telegram chat.
        """
        files = {'photo': open(photo, 'rb')}
        return self._send_file_helper(chat_id, "/sendPhoto", files,
                                      text, title, parse_mode, level, icon, silent)

    def send_document(self, document, text=None, title="", parse_mode=ParseMode.MARKDOWN, level="no", icon="", silent=False, chat_id=None):
        """Send a general file to a Telegram chat.
        """
        files = {'document': open(document, 'rb')}
        return self._send_file_helper(chat_id, "/sendDocument", files,
                                      text, title, parse_mode, level, icon, silent)

    def send_audio(self, audio, text=None, title="", parse_mode=ParseMode.MARKDOWN, level="no", icon="", silent=False, chat_id=None):
        """Send an audio file to a Telegram chat.
        """
        files = {'audio': open(audio, 'rb')}
        return self._send_file_helper(chat_id, "/sendAudio", files,
                                      text, title, parse_mode, level, icon, silent)

    def send_video(self, video, text=None, title="", parse_mode=ParseMode.MARKDOWN, level="no", icon="", silent=False, chat_id=None):
        """Send a video file to a Telegram chat.
        """
        files = {'video': open(video, 'rb')}
        return self._send_file_helper(chat_id, "/sendVideo", files,
                                      text, title, parse_mode, level, icon, silent)

    def send_animation(self, animation, text=None, title="", parse_mode=ParseMode.MARKDOWN, level="no", icon="", silent=False, chat_id=None):
        """Send a video file to a Telegram chat.
        """
        files = {'animation': open(animation, 'rb')}
        return self._send_file_helper(chat_id, "/sendAnimation", files,
                                      text, title, parse_mode, level, icon, silent)

    def send_location(self, latitude, longitude, silent=False, chat_id=None):
        """Send a location on a map to a Telegram chat.
        """
        if not self.chat_id and not chat_id:
            raise RuntimeError("No chat ID specified.")
        params = { 'chat_id': chat_id or self.chat_id, 'latitude': latitude, 'longitude': longitude,
            'disable_notification': str(silent)}
        return requests.get(Telegram._req_url  + self.token + "/sendLocation", params=params)

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
    group.add_argument('--audio', help="path to an audio file to be sent")
    group.add_argument('--video', help="path to a video file to be sent")
    group.add_argument('--anim', help="path to an animation (gif or mp4) file to be sent")
    group.add_argument('--loc', help="send a location of the form <latitude>,<longitude>")
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
    if args.photo:
        response = telegram.send_photo(args.photo, args.text, args.title, args.parse_mode,
                    args.level, args.icon, args.silent, chat_id=args.id)
    elif args.doc:
        response = telegram.send_document(args.doc, args.text, args.title, args.parse_mode,
                    args.level, args.icon, args.silent, chat_id=args.id)
    elif args.audio:
        response = telegram.send_audio(args.audio, args.text, args.title, args.parse_mode,
                    args.level, args.icon, args.silent, chat_id=args.id)
    elif args.video:
        response = telegram.send_video(args.video, args.text, args.title, args.parse_mode,
                    args.level, args.icon, args.silent, chat_id=args.id)
    elif args.anim:
        response = telegram.send_animation(args.anim, args.text, args.title, args.parse_mode,
                    args.level, args.icon, args.silent, chat_id=args.id)
    elif args.loc:
        lat, long = tuple(args.loc.split(','))
        response = telegram.send_location(lat, long, silent=args.silent, chat_id=args.id)
    else:
        text = sys.stdin.read() if args.text == "-" else args.text
        response = telegram.send_message(text, args.title, args.parse_mode,
                    args.level, args.icon, args.silent, fixed=args.fixed, web_page_preview=args.preview,
                    chat_id=args.id)
    failure = not response.json()["ok"]
    if args.verbose or failure:
        print(response.text)

if __name__ == "__main__":
    main()
