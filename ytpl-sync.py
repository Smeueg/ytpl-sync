#!/usr/bin/env python3
# TODO: Finish Syncer.sync
# TODO: Finish Syncer.remove
# TODO: Put err(), warn(), header() and other UI functions to the class: UI
from enum import Enum
import argparse
import os
import sys


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

class UI:
    pass

def err(msg: str, exit_code: int) -> None:
    print("{} {}".format(colorize("*", Color.RED), msg), file=sys.stderr)
    sys.exit(exit_code)


def warn(msg: str) -> None:
    print("{} {}".format(colorize("*", Color.YELLOW), msg))

def header(title: str) -> None:
    print("── {} ──".format(colorize(title, Color.YELLOW)))


class Color(Enum):
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36


class PlaylistValid:
    @staticmethod
    def url(url: str) -> bool:
        from re import search

        return (
            search("https://(www.)?youtube.com/playlist\?list=[0-9A-Za-z_-]", url)
            is not None
        )

    @staticmethod
    def dir(dir):
        return os.path.isdir(os.path.expanduser(dir))


class Syncer:
    formats = {
        "audio": ("aac", "flac", "mp3", "m4a", "opus", "vorbis"),
        "video": ("mp4", "webm"),
    }

    deps = {"yt": {"yt-dlp", "youtube-dl"}, "bins": {"ffmpeg"}}

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

        for b in self.deps["bins"]:
            if which(b) is None:
                err(f"`{b}` isn't installed but required", 1)

        for b in self.deps["yt"]:
            if which(b):
                return
        err("`yt-dlp` and `youtube-dl` aren't installed but one is required", 1)

    def checkConnection() -> None:
        from socket import create_connection

        try:
            create_connection(("1.1.1.1", 53))
            return True
        except OSError:
            pass
        err("Could not connect to the internet", 1)

    def listFormats(self) -> None:
        """List the available formats supported by the syncher"""
        header("Formats")
        for key in self.formats:
            print("{}:".format(colorize(key, Color.BLUE)))
            for f in self.formats[key]:
                print("   * {}:".format(colorize(f, Color.GREEN)))

    def validateSettings(self):
        while True:  # Url
            if self.url is None:
                self.url = input("URL: ")
            if PlaylistValid.url(self.url):
                break
            else:
                warn(f"'{self.url}' isn't a valid Youtube playlist URL.")
                self.url = None

        while True:  # Directory
            if self.dir is None:
                self.dir = input("Directory (Default is '~/Music'): ")
            if self.dir == "":
                self.dir = "~/Music"
            if PlaylistValid.dir(self.dir):
                break
            else:
                warn(f"'{self.dir}' isn't a directory")
                self.dir = None

        while True:  # Format
            if self.format is None:
                self.format = input("Format (Default is 'mp3'): ")
            if self.format == "":
                self.format = "mp3"
            if self.format in self.formats["audio"]:
                self.format_type = "audio"
                break
            elif self.format in self.formats["video"]:
                self.format_type = "video"
                break
            else:
                warn(f"'{self.format}' is an invalid format, use '--list-formats' to see the available formats")
                self.format = None

        if not self.remove:
            print(
                "Remove file that aren't in the playlist?\n" \
                "This will also delete files that aren't in the provided format\n" \
                f"(i.e. {self.format})"
            )
            self.remove = prompt_yn("Remove?")


def colorize(string: str, color: Color, bold=False, reverse=False):
    escape = "\033["
    code = f"{escape}{color.value}m"
    reset = f"{escape}m"
    if bold:
        code += f"{escape}1m"
    if reverse:
        code += f"{escape}7m"
    return f"{code}{string}{reset}"


def _getchUnix():
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


def _getchWindows():
    import msvcrt

    return msvcrt.getch()


def _getGetch():
    # https://stackoverflow.com/questions/510357/how-to-read-a-single-character-from-the-user#510364
    try:
        import msvcrt

        return msvcrt.getch
    except ImportError:
        import termios

        def _getch():
            import sys
            import tty

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

        return _getch


getch = _getGetch()


def prompt_yn(question):
    question_colorized = colorize(question, "blue")
    print(question_colorized)
    agreed = True
    while True:
        print(colorize("Yes", "green", reverse=agreed))
        print(colorize("No", "red", reverse=not agreed))
        ch = getch()
        print("\033[3A")
        if ch == "[":
            ch = getch()
            if ch == "A":
                agreed = True
            elif ch == "B":
                agreed = False
        elif ord(ch) == 13:  # Enter is pressed
            choice = "No"
            if agreed:
                choice = "Yes"
            print(f"\033[A{question_colorized} {choice}")
            return agreed


if __name__ == "__main__":
    args = parser.parse_args()  # (url=, dir=, format=, remove=, list_formats=)
    syncer = Syncer(args.url, args.dir, args.format, args.remove, args.list_formats)
    syncer.checkDeps()
    syncer.validateSettings()
    syncer.sync()
    syncer.remove()
    sys.exit(0)
