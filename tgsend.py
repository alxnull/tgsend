#!/usr/bin/env python3

__version__ = "0.3"

import configparser
import json
import os
import sys
from os.path import abspath, expanduser, isfile

import requests

BOT_API_URL = "https://api.telegram.org/bot"

LOCAL_CONFIG_FILE = "~/tgsend.conf"
CONFIG_FILE = "/etc/tgsend.conf"
TOKEN = os.environ.get("TGSEND_TOKEN")
CHAT_ID = os.environ.get("TGSEND_CHATID")


class ParseMode:
    NONE = "none"
    MARKDOWN = "markdown"
    MARKDOWN_V2 = "markdownV2"
    HTML = "html"


class Telegram:
    """Send messages to Telegram chats via a bot.

    :param token: The bot token of the bot (read from env var or config file if not specified), defaults to None
    :param token: str, optional
    :param chat_id: The ID of the chat messages should be sent to, defaults to None
    :param chat_id: str, optional
    :param parse_mode: The default ParseMode used to format messages, defaults to ParseMode.MARKDOWN_V2
    :param parse_mode: ParseMode, optional
    :raises RuntimeError: If no valid token and chat ID configuration was found
    """

    _icons = {
        "warn": "\U000026A0",
        "alert": "\U0001f198",
        "info": "\U0001f4cb",
        "error": "\u274c",
        "success": "\u2705",
        "no": "",
    }

    def __init__(self, token=None, chat_id=None, parse_mode=ParseMode.MARKDOWN_V2):
        self.token, self.chat_id = token or TOKEN, chat_id or CHAT_ID
        self.parse_mode = parse_mode
        if not self.token:
            try:
                token_read, chat_read = Telegram._read_config("Default")
                if not self.token:
                    self.token = token_read
                if not self.chat_id:
                    self.chat_id = chat_read
            except Exception:
                pass
        if not self.token:
            raise RuntimeError("Could not find a valid configuration with BotToken.")

    @classmethod
    def load(cls, name="Default", config_file=None):
        """Load a bot token and chat id configuration from file."""
        token, chat_id = Telegram._read_config(name, config_file)
        if not token:
            raise RuntimeError("Given configuration '{}' not available".format(name))
        return cls(token, chat_id)

    @staticmethod
    def _read_config(name, custom_config_file=None):
        # infer file
        if custom_config_file and isfile(abspath(expanduser(custom_config_file))):
            config_file = abspath(expanduser(custom_config_file))
        elif isfile(expanduser(LOCAL_CONFIG_FILE)):
            config_file = expanduser(LOCAL_CONFIG_FILE)
        elif isfile(CONFIG_FILE):
            config_file = CONFIG_FILE
        else:
            raise RuntimeError("Configuration file '{}' could not be found.".format(config_file))
        # read config
        config = configparser.ConfigParser()
        config.read(config_file)
        if name in config:
            current = config[name]
            token = current["BotToken"] if "BotToken" in current else None
            chat = current["ChatID"] if "ChatID" in current else None
            return token, chat
        return None, None

    def get_me(self):
        """
        Get basic user information about the bot.
        Bot information has the form defined at https://core.telegram.org/bots/api#user.
        """
        response = requests.get(BOT_API_URL + self.token + "/getMe")
        response.raise_for_status()
        if response.status_code == 200 and response.json()["ok"]:
            return response.json()["result"]
        else:
            raise EnvironmentError(response.text)

    def format_bold(self, text, parse_mode=None):
        parse_mode = parse_mode or self.parse_mode
        if parse_mode == ParseMode.HTML:
            return "<b>{}</b>".format(text)
        elif parse_mode == ParseMode.MARKDOWN or parse_mode == ParseMode.MARKDOWN_V2:
            return "*{}*".format(text)
        else:
            return text

    def format_italic(self, text, parse_mode=None):
        parse_mode = parse_mode or self.parse_mode
        if parse_mode == ParseMode.HTML:
            return "<i>{}</i>".format(text)
        elif parse_mode == ParseMode.MARKDOWN or parse_mode == ParseMode.MARKDOWN_V2:
            return "_{}_".format(text)
        else:
            return text

    def format_fixed(self, text, parse_mode=None):
        parse_mode = parse_mode or self.parse_mode
        if parse_mode == ParseMode.HTML:
            return "<code>{}</code>".format(text)
        elif parse_mode == ParseMode.MARKDOWN or parse_mode == ParseMode.MARKDOWN_V2:
            return "`{}`".format(text)
        else:
            return text

    def _text(self, text, title, parse_mode, icon):
        s = icon + " "
        if title:
            s += self.format_bold(title, parse_mode) + "\n\n"
        return s + text

    def _to_real_parse_mode(self, parse_mode):
        parse_mode = parse_mode or self.parse_mode
        if parse_mode == ParseMode.NONE:
            return ""
        else:
            return parse_mode

    def send_message(
        self,
        text,
        title="",
        chat_id=None,
        parse_mode=None,
        level="no",
        icon="",
        silent=False,
        fixed=False,
        disable_web_page_preview=True,
        reply_to_message_id=None,
    ):
        """Send a text message to a Telegram chat."""
        if not self.chat_id and not chat_id:
            raise RuntimeError("No chat ID specified.")
        s = self._text(text, title, parse_mode or self.parse_mode, icon if icon else Telegram._icons[level])
        if fixed:
            s = self.format_fixed(s, parse_mode)
        params = {
            "chat_id": chat_id or self.chat_id,
            "parse_mode": self._to_real_parse_mode(parse_mode),
            "text": s,
            "disable_notification": str(silent),
            "disable_web_page_preview": str(disable_web_page_preview),
            "reply_to_message_id": int(reply_to_message_id) if reply_to_message_id else None,
        }
        return requests.get(BOT_API_URL + self.token + "/sendMessage", params=params)

    def _send_file_helper(
        self, chat_id, method, files, text, title, p_m, lvl, icon, silent, reply_to_message_id, **kwargs
    ):
        if not self.chat_id and not chat_id:
            raise RuntimeError("No chat ID specified.")
        text_title = title if method != "/sendAudio" else ""  # /sendAudio has a dedicated title param
        s = self._text(text or "", text_title, p_m or self.parse_mode, icon if icon else Telegram._icons[lvl])
        params = {
            "chat_id": chat_id or self.chat_id,
            "parse_mode": self._to_real_parse_mode(p_m),
            "caption": s,
            "disable_notification": str(silent),
            "reply_to_message_id": int(reply_to_message_id) if reply_to_message_id else None,
        }
        if method == "/sendAudio":
            params["title"] = title
        params.update(kwargs)
        return requests.post(BOT_API_URL + self.token + method, data=params, files=files)

    def send_photo(
        self,
        photo,
        text=None,
        title="",
        chat_id=None,
        parse_mode=None,
        level="no",
        icon="",
        silent=False,
        reply_to_message_id=None,
    ):
        """Send a photo to a Telegram chat."""
        files = {"photo": open(photo, "rb")}
        return self._send_file_helper(
            chat_id, "/sendPhoto", files, text, title, parse_mode, level, icon, silent, reply_to_message_id
        )

    def send_document(
        self,
        document,
        thumb=None,
        text=None,
        title="",
        chat_id=None,
        parse_mode=None,
        level="no",
        icon="",
        silent=False,
        reply_to_message_id=None,
    ):
        """Send a general file to a Telegram chat."""
        files = {"document": open(document, "rb")}
        if thumb:
            files["thumb"] = open(thumb, "rb")
        return self._send_file_helper(
            chat_id, "/sendDocument", files, text, title, parse_mode, level, icon, silent, reply_to_message_id
        )

    def send_audio(
        self,
        audio,
        thumb=None,
        text=None,
        title="",
        chat_id=None,
        parse_mode=None,
        level="no",
        icon="",
        silent=False,
        duration=None,
        performer=None,
        reply_to_message_id=None,
    ):
        """Send an audio file to a Telegram chat."""
        files = {
            "audio": open(audio, "rb"),
        }
        kwargs = {
            "duration": duration,
            "performer": performer,
        }
        if thumb:
            files["thumb"] = open(thumb, "rb")
        return self._send_file_helper(
            chat_id, "/sendAudio", files, text, title, parse_mode, level, icon, silent, reply_to_message_id, **kwargs
        )

    def send_video(
        self,
        video,
        thumb=None,
        text=None,
        title="",
        chat_id=None,
        parse_mode=None,
        level="no",
        icon="",
        silent=False,
        duration=None,
        width=None,
        height=None,
        supports_streaming=False,
        reply_to_message_id=None,
    ):
        """Send a video file to a Telegram chat."""
        files = {
            "video": open(video, "rb"),
        }
        kwargs = {
            "duration": duration,
            "width": width,
            "height": height,
            "supports_streaming": str(supports_streaming),
        }
        if thumb:
            files["thumb"] = open(thumb, "rb")
        return self._send_file_helper(
            chat_id, "/sendVideo", files, text, title, parse_mode, level, icon, silent, reply_to_message_id, **kwargs
        )

    def send_animation(
        self,
        animation,
        thumb=None,
        text=None,
        title="",
        chat_id=None,
        parse_mode=None,
        level="no",
        icon="",
        silent=False,
        duration=None,
        width=None,
        height=None,
        reply_to_message_id=None,
    ):
        """Send a video file to a Telegram chat."""
        files = {
            "animation": open(animation, "rb"),
        }
        kwargs = {
            "duration": duration,
            "width": width,
            "height": height,
        }
        if thumb:
            files["thumb"] = open(thumb, "rb")
        return self._send_file_helper(
            chat_id,
            "/sendAnimation",
            files,
            text,
            title,
            parse_mode,
            level,
            icon,
            silent,
            reply_to_message_id,
            **kwargs
        )

    def send_voice(
        self,
        voice,
        text=None,
        title="",
        chat_id=None,
        parse_mode=None,
        level="no",
        icon="",
        silent=False,
        duration=None,
        reply_to_message_id=None,
    ):
        """Send a voice message file to a Telegram chat. The sent file must be a .ogg file encoded with OPUS."""
        files = {
            "voice": open(voice, "rb"),
        }
        kwargs = {
            "duration": duration,
        }
        return self._send_file_helper(
            chat_id, "/sendVoice", files, text, title, parse_mode, level, icon, silent, reply_to_message_id, **kwargs
        )

    def send_location(
        self,
        latitude,
        longitude,
        chat_id=None,
        silent=False,
        reply_to_message_id=None,
    ):
        """Send a location on a map to a Telegram chat."""
        if not self.chat_id and not chat_id:
            raise RuntimeError("No chat ID specified.")
        params = {
            "chat_id": chat_id or self.chat_id,
            "latitude": latitude,
            "longitude": longitude,
            "disable_notification": str(silent),
            "reply_to_message_id": int(reply_to_message_id) if reply_to_message_id else None,
        }
        return requests.get(BOT_API_URL + self.token + "/sendLocation", params=params)

    def send_venue(
        self,
        latitude,
        longitude,
        title,
        address,
        chat_id=None,
        silent=False,
        reply_to_message_id=None,
    ):
        """Send information about a venue to a Telegram chat."""
        if not self.chat_id and not chat_id:
            raise RuntimeError("No chat ID specified.")
        params = {
            "chat_id": chat_id or self.chat_id,
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "address": address,
            "disable_notification": str(silent),
            "reply_to_message_id": int(reply_to_message_id) if reply_to_message_id else None,
        }
        return requests.get(BOT_API_URL + self.token + "/sendVenue", params=params)

    def send_contact(
        self,
        phone_number,
        first_name,
        last_name=None,
        vcard=None,
        chat_id=None,
        silent=False,
        reply_to_message_id=None,
    ):
        """Send a phone contact to a Telegram chat."""
        if not self.chat_id and not chat_id:
            raise RuntimeError("No chat ID specified.")
        params = {
            "chat_id": chat_id or self.chat_id,
            "phone_number": phone_number,
            "first_name": first_name,
            "last_name": last_name,
            "vcard": vcard,
            "disable_notification": str(silent),
            "reply_to_message_id": int(reply_to_message_id) if reply_to_message_id else None,
        }
        return requests.get(BOT_API_URL + self.token + "/sendContact", params=params)

    def send_poll(
        self,
        question,
        options,
        chat_id=None,
        is_anonymous=False,
        type="regular",
        allows_multiple_answers=False,
        correct_option_id=None,
        explanation=None,
        explanation_parse_mode=None,
        open_period=None,
        close_date=None,
        is_closed=False,
        silent=False,
        reply_to_message_id=None,
    ):
        """Send a native poll to a Telegram chat."""
        if not self.chat_id and not chat_id:
            raise RuntimeError("No chat ID specified.")
        params = {
            "chat_id": chat_id or self.chat_id,
            "question": question,
            "options": json.dumps(options),
            "is_anonymous": str(is_anonymous),
            "type": type,
            "allows_multiple_answers": str(allows_multiple_answers),
            "correct_option_id": correct_option_id,
            "explanation": explanation,
            "explanation_parse_mode": explanation_parse_mode,
            "open_period": open_period,
            "close_date": close_date,
            "is_closed": str(is_closed),
            "disable_notification": str(silent),
            "reply_to_message_id": int(reply_to_message_id) if reply_to_message_id else None,
        }
        return requests.get(BOT_API_URL + self.token + "/sendPoll", params=params)

    def send_sticker(
        self,
        sticker,
        chat_id=None,
        silent=False,
        reply_to_message_id=None,
    ):
        """Send a sticker file to a Telegram chat. Sticker file must be a .webp or an animated .tgs file."""
        if not self.chat_id and not chat_id:
            raise RuntimeError("No chat ID specified.")
        params = {
            "chat_id": chat_id or self.chat_id,
            "disable_notification": str(silent),
            "reply_to_message_id": int(reply_to_message_id) if reply_to_message_id else None,
        }
        files = {"sticker": open(sticker, "rb")}
        return requests.post(BOT_API_URL + self.token + "/sendSticker", data=params, files=files)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Simple tool to send messages to a telegram chat.")
    parser.add_argument("text", help="the text to be send", nargs="?")
    parser.add_argument(
        "-l", "--load", default=None, help="specify a configuration file different from the default config"
    )
    parser.add_argument("-c", "--config", default=None, help="specify the bot configuration to be loaded")
    parser.add_argument("--id", default="", help="override the chat id from the loaded configuration")
    parser.add_argument("-t", "--title", default="", help="title of the message")
    parser.add_argument(
        "--format",
        default="markdownV2",
        choices=["html", "markdown", "markdownV2", "none"],
        help="the formatting used for the text (default: markdownV2)",
        dest="parse_mode",
    )
    parser.add_argument("--silent", help="sends message without notification", action="store_true")
    # message types
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--photo", "-p", help="path to a picture to be sent")
    group.add_argument("--doc", "-d", help="path to a document to be sent")
    group.add_argument("--audio", help="path to an audio file to be sent")
    group.add_argument("--video", help="path to a video file to be sent")
    group.add_argument("--anim", help="path to an animation (gif or mp4) file to be sent")
    group.add_argument("--voice", help="path to a voice message to be sent")
    group.add_argument("--loc", help="send a location of the form <latitude>,<longitude>")
    group.add_argument("--sticker", help="path to a sticker file in .webp or .tgs format")
    # general options
    parser.add_argument("--icon", default="", help="Unicode of an icon placed beside the title of the message")
    parser.add_argument(
        "--thumb",
        default=None,
        help="Path to a file containing a thumbnail image. E.g. used when sending an audio or video message.",
    )
    parser.add_argument(
        "--lvl",
        default="no",
        choices=["success", "info", "warn", "error", "alert", "no"],
        help="log level of the message (icon overriden by --icon)",
        dest="level",
    )
    parser.add_argument("--fixed", help="format message as fixed-width text", action="store_true")
    parser.add_argument("--no-preview", help="disable link previews", action="store_true", dest="preview")
    parser.add_argument("-v", "--verbose", help="always print out return message", action="store_true")
    parser.add_argument("--version", version="tgsend v.{}".format(__version__), action="version")
    args = parser.parse_args()
    if args.config:
        telegram = Telegram.load(args.config, args.load)
    elif args.load:
        telegram = Telegram.load(config_file=args.load)
    else:
        telegram = Telegram()
    if args.photo:
        response = telegram.send_photo(
            args.photo,
            text=args.text,
            title=args.title,
            chat_id=args.id,
            parse_mode=args.parse_mode,
            level=args.level,
            icon=args.icon,
            silent=args.silent,
        )
    elif args.doc:
        response = telegram.send_document(
            args.doc,
            thumb=args.thumb,
            text=args.text,
            title=args.title,
            chat_id=args.id,
            parse_mode=args.parse_mode,
            level=args.level,
            icon=args.icon,
            silent=args.silent,
        )
    elif args.audio:
        response = telegram.send_audio(
            args.audio,
            thumb=args.thumb,
            text=args.text,
            title=args.title,
            chat_id=args.id,
            parse_mode=args.parse_mode,
            level=args.level,
            icon=args.icon,
            silent=args.silent,
        )
    elif args.video:
        response = telegram.send_video(
            args.video,
            thumb=args.thumb,
            text=args.text,
            title=args.title,
            chat_id=args.id,
            parse_mode=args.parse_mode,
            level=args.level,
            icon=args.icon,
            silent=args.silent,
        )
    elif args.anim:
        response = telegram.send_animation(
            args.anim,
            thumb=args.thumb,
            text=args.text,
            title=args.title,
            chat_id=args.id,
            parse_mode=args.parse_mode,
            level=args.level,
            icon=args.icon,
            silent=args.silent,
        )
    elif args.voice:
        response = telegram.send_voice(
            args.voice,
            text=args.text,
            title=args.title,
            chat_id=args.id,
            parse_mode=args.parse_mode,
            level=args.level,
            icon=args.icon,
            silent=args.silent,
        )
    elif args.loc:
        lat, long = tuple(args.loc.split(","))
        response = telegram.send_location(lat, long, chat_id=args.id, silent=args.silent)
    elif args.sticker:
        response = telegram.send_sticker(args.sticker, chat_id=args.id, silent=args.silent)
    else:
        text = sys.stdin.read() if args.text == "-" else args.text
        response = telegram.send_message(
            text,
            title=args.title,
            chat_id=args.id,
            parse_mode=args.parse_mode,
            level=args.level,
            icon=args.icon,
            silent=args.silent,
            fixed=args.fixed,
            disable_web_page_preview=args.preview,
        )
    failure = response.status_code != 200 or not response.json()["ok"]
    if args.verbose or failure:
        print("Status code: ", response.status_code)
        print(response.text)


if __name__ == "__main__":
    main()
