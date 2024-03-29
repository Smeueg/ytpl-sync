#!/usr/bin/env python3
# TODO: Finish Syncer.sync
# TODO: Finish Syncer.remove
# TODO: Put err(), warn(), header() and other UI functions to the class: UI
# TODO: https://stackoverflow.com/questions/4814040/allowed-characters-in-filename
from enum import Enum
import argparse
import os
import sys
import json
from yt_dlp import YoutubeDL


# CLI args parser
parser = argparse.ArgumentParser(description="Sync a Youtube playlist to a directory")
parser.add_argument("--url", type=str, help="Use URL instead of prompting for one")
parser.add_argument("--dir", type=str, help="Use DIR instead of prompting for one")
parser.add_argument(
    "--format", type=str, help="Download media as FORMAT instead of propting for one"
)
parser.add_argument(
    "--remove",
    action="store_true",
    help="Remove media that isn't in the playlist (use with caution)",
)
parser.add_argument(
    "--list-formats",
    action="store_true",
    help="Print the supported formats supported by '--format'",
)


class Color(Enum):
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36


class UI:
    getch = None

    @staticmethod
    def __getchUnix() -> None:
        import sys
        import tty
        import termios

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    try:
        import msvcrt

        getch = msvcrt.getch
    except ImportError:
        getch = __getchUnix

    @staticmethod
    def colorize(string: str, color: Color, bold=False, reverse=False) -> str:
        escape = "\033["
        code = f"{escape}{color.value}m"
        reset = f"{escape}m"
        if bold:
            code += f"{escape}1m"
        if reverse:
            code += f"{escape}7m"
        return f"{code}{string}{reset}"

    @staticmethod
    def promptYN(question: str):
        question_colorized = UI.colorize(question, Color.BLUE)
        print(question_colorized)
        agreed = True
        while True:
            print(UI.colorize("Yes", Color.GREEN, reverse=agreed))
            print(UI.colorize("No", Color.RED, reverse=not agreed))
            ch = UI.getch()
            print("\033[3A")
            if ch == "[":
                ch = UI.getch()
                if ch == "A":
                    agreed = True
                elif ch == "B":
                    agreed = False
            if ch == "k":
                agreed = True
            elif ch == "j":
                agreed = False
            elif ord(ch) == 13:  # Enter is pressed
                choice = "No"
                if agreed:
                    choice = "Yes"
                print(f"\033[A{question_colorized} {choice}")
                return agreed

    @staticmethod
    def err(msg: str, exit_code: int) -> None:
        print("{} {}".format(UI.colorize("*", Color.RED), msg), file=sys.stderr)
        sys.exit(exit_code)

    @staticmethod
    def warn(msg: str) -> None:
        print("{} {}".format(UI.colorize("*", Color.YELLOW), msg))

    @staticmethod
    def header(title: str) -> None:
        print("── {} ──".format(UI.colorize(title, Color.YELLOW)))

    @staticmethod
    def footer(length: int) -> None:
        print("─" * (length + 6))


class PlaylistInfo:
    _illegal_chars = {
        '"': "”",
        "/": "╱",
        ":": "꞉",
        "<": "‹",
        ">": "›",
        "|": "│",
        "?": "︖",
        "\\": "╲",
    }

    @staticmethod
    def _format_title(title: str) -> str:
        title = title.strip()
        # get rid of the leading periods
        i = 0
        while title[i] == ".":
            i += 1
        title = title[i:]
        # Get rid of illegal characters for filenames
        for char in PlaylistInfo._illegal_chars:
            title = title.replace(char, PlaylistInfo._illegal_chars[char])
        return title

    def __init__(self, url: str):
        with YoutubeDL({"extract_flat": True}) as ytdl:
            info = ytdl.sanitize_info(ytdl.extract_info(url, download=False))
            info_json = json.loads(json.dumps(info))
        self.title = info_json["title"]
        self.entries = info_json["entries"]
        for entry in self.entries:
            entry["title"] = self._format_title(entry["title"])

    def has(self, title: str, ext: str) -> bool:
        for entry in self.entries:
            if title == "{}.{}".format(entry["title"], ext):
                return True
        return False


class PlaylistValid:
    @staticmethod
    def url(url: str) -> bool:
        from re import search

        return (
            search("https://(www.)?youtube.com/playlist\?list=[0-9A-Za-z_-]", url)
            is not None
        )

    @staticmethod
    def dir(dir: str) -> bool:
        return os.path.isdir(os.path.expanduser(dir))


class Syncer:
    __formats = {
        "audio": ("aac", "flac", "mp3", "m4a", "opus", "vorbis"),
        "video": ("mp4", "webm"),
    }

    __deps = {"yt": {"yt-dlp", "youtube-dl"}, "bins": {"ffmpeg"}}

    def __init__(self, url, dir, format, remove, list_formats):
        if list_formats:
            self.listFormats()
            sys.exit(0)
        else:
            self.url = url
            self.dir = dir
            self.format = format
            self.remove = remove

    def checkDeps(self) -> None:
        from shutil import which

        for b in self.__deps["bins"]:
            if which(b) is None:
                UI.err(f"`{b}` isn't installed but required", 1)

        for b in self.__deps["yt"]:
            if which(b):
                return
        UI.err("`yt-dlp` and `youtube-dl` aren't installed but one is required", 1)

    def checkConnection() -> None:
        from socket import create_connection

        try:
            create_connection(("1.1.1.1", 53))
            return True
        except OSError:
            pass
        UI.err("Could not connect to the internet", 1)

    def listFormats(self) -> None:
        """List the available formats supported by the syncher"""
        UI.header("Formats")
        for key in self.__formats:
            print("{}:".format(UI.colorize(key, Color.BLUE)))
            for f in self.__formats[key]:
                print("   * {}:".format(UI.colorize(f, Color.GREEN)))

    @staticmethod
    def ask(question: str, default=None) -> str:
        string = UI.colorize(question, Color.BLUE)
        if default is not None:
            string = f"{string} (Default is '{default}')"
        response = input(f"{string}: ")
        return response

    def validateSettings(self) -> None:
        while True:  # Url
            if self.url is None:
                self.url = self.ask("URL")
            if PlaylistValid.url(self.url):
                break
            else:
                UI.warn(f"'{self.url}' isn't a valid Youtube playlist URL.")
                self.url = None
            print("")

        while True:  # Directory
            if self.dir is None:
                self.dir = self.ask("Directory", "~/Music")
            if self.dir == "":
                self.dir = "~/Music"
            if PlaylistValid.dir(self.dir):
                break
            else:
                UI.warn(f"'{self.dir}' isn't a directory")
                self.dir = None
            print("")

        while True:  # Format
            if self.format is None:
                self.format = self.ask("Format", "mp3")
            if self.format == "":
                self.format = "mp3"
            if self.format in self.__formats["audio"]:
                self.format_type = "audio"
                break
            elif self.format in self.__formats["video"]:
                self.format_type = "video"
                break
            else:
                UI.warn(
                    f"'{self.format}' is an invalid format, "
                    "use '--list-formats to see the available formats'"
                )
                self.format = None
            print("")

        if not self.remove:
            print(
                "Remove file that aren't in the playlist?\n"
                "This will also delete files that aren't in the provided format\n"
                f"(i.e. {self.format})"
            )
            self.remove = UI.promptYN("Remove?")

    def initInfo(self) -> None:
        self.info = PlaylistInfo(self.url)

    def confirm(self) -> None:
        UI.header("Overview")
        print("{}: {}".format(UI.colorize("Title", Color.BLUE), self.info.title))
        print("{}: {}".format(UI.colorize("URL", Color.BLUE), self.url))
        print("{}: {}".format(UI.colorize("Directory", Color.BLUE), self.dir))
        print("{}: {}".format(UI.colorize("Format", Color.BLUE), self.format))
        UI.footer(8)

        if not UI.promptYN("Do you want to continue?"):
            sys.exit(0)

    def sync(self) -> None:
        with YoutubeDL() as ytdl:
            for entry in self.info.entries:
                path = os.path.expanduser(
                    "{}/{}.{}".format(self.dir, entry["title"], self.format)
                )
                colored_skipping = UI.colorize("Skipping", Color.CYAN)
                colored_downloading = UI.colorize("Downloading", Color.YELLOW)
                if os.path.isfile(path):
                    print(
                        "{} {}.{}, already exists".format(
                            colored_skipping, entry["title"], self.format
                        )
                    )
                else:
                    print(
                        "{} {}.{}".format(
                            colored_downloading, entry["title"], self.format
                        )
                    )
                    ytdl.download(entry["url"])

    def removeFiles(self) -> None:
        if self.remove:
            files = os.listdir(os.path.expanduser(self.dir))
            colored_removing = UI.colorize("Removing", Color.RED)
            for f in files:
                if not self.info.has(f, self.format):
                    print(f"{colored_removing} {f}")
                    os.remove(os.path.expanduser("{}/{}", self.dir, f))


if __name__ == "__main__":
    args = parser.parse_args()  # (url=, dir=, format=, remove=, list_formats=)
    syncer = Syncer(
        args.url,
        args.dir,
        args.format,
        args.remove,
        args.list_formats
    )
    syncer.checkDeps()
    syncer.validateSettings()
    syncer.initInfo()
    syncer.confirm()
    syncer.sync()
    syncer.removeFiles()
