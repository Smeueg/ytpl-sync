<h1 align="center">ytpl-sync (YoutubePlaylist-Sync)</h1>
Sync a Youtube playlist to a directory, optionally remove videos/audios that
aren't in the playlist.

---

## Dependencies
- [youtube-dl](https://youtube-dl.org/)
- [ffmpeg](ffmpeg.org)

## Installation
Since `ytpl-sync` is just a shell script, installing is as easy as downloading
`ytpl-sync` into somewhere in your `$PATH`.

If, for example, `~/.local/bin` is in your `$PATH`
```bash
curl -L https://raw.githubusercontent.com/Smeueg/ytpl-sync/main/ytpl-sync -o ~/.local/bin/ytpl-sync
```
or if you want to install it system-wide
```bash
curl -L https://raw.githubusercontent.com/Smeueg/ytpl-sync/main/ytpl-sync -o /usr/bin/ytpl-sync
```

## Usage
`ytpl-sync` can be run interactively but there are options that can be used to
further automate the process.
Example:
```bash
ytpl-sync
```
or
```bash
ytpl-sync --url "https://www.youtube.com/playlist?list=PLRV1hc8TIW-7znQIWaVarxdUxf7lskmBc"
```

Options include:
- `--help`, display the help information
- `--url URL`, use this url instead of prompting the user
- `--format FORMAT`, use this url instead of prompting the user
- `--dir DIR`, sync to this directory instead of prompting the user
- `--remove`, remove media that aren't in the playlist (Use with caution)
