
# HolyCleansing

This is a simple script to automatically delete tvshows episodes watched in the media player Kodi/OSMC.

It supports a whitelist per tvshow which episodes won't be deleted.

To launch it on a schedule, please use a crontab

It has been tested and developed on a Linux system, but should be working properly on Windows and Mac.

## Features and usage

usage: HolyCleansing.py [-h] [-s] [-c] [-t] [-a] [-d] [-r] [-v]

optional arguments:

  -h, --help     show this help message and exit.

  -s, --simu     Display which episodes are going to be deleted without processing.

  -c, --clean    Delete all the watched episodes.

  -t, --tvshows  Display the list of tvshows in the database.

  -a, --add      Add a tvshow to the whitelist.

  -d, --display  Display the tvshows in the whitelist.

  -r, --remove   Remove tvshows from the whitelist.

  -v, --verbose  Increase output verbosity.
  
## Kodi's versions supported

It has been tested and developed against Kodi Leia version 18.2. If the version is anterior, the database version[^1]  is not supported natively by the script.
[^1]: https://kodi.wiki/view/Databases#Database_Versions

To change that, add to `config.json` in the key `dbNames` with the schema `MyVideos<versionNumber>.db` then run the script with `--add` option and `--simu`. If no error is raised, all is good (please report it to me)!

Example for `config.json` and database version 37
```json
{
    "kodiPaths": {
        "Linux": [
            "~/.kodi/userdata/"
        ],
        "Darwin": [
            "/Library/Application Support/Kodi/userdata/"
        ],
        "Windows": [
            "%APPDATA%\\Kodi\\userdata\\"
        ]
    },
    "dbNames": [
        "MyVideos116.db",
        "MyVideos37.db"
    ]
}
```

## Dependencies and installation
The script can be installed in any directory by cloning this repository.

The user launching the script should have:
- read and write rights on the script directory,
- read rights on kodi's database[^2] ,
- read and write rights on the tvshows directory
[^2]: (see `config.json` to get its directory)

Python version 3.6 or above

Use the `--simu` option to insure a correct installation:
```bash
python3 ./HolyCleansing.py -sv
```

## Schedule
The owner of the crontab should have the same rights as stipulated in the previous section.

```bash
crontab -e
```
Examples:
(replace <installDirectory\> by the script installation directory)
_Every day at 01 in the morning_:
```cron
00 01 * * * python3 <installDirectory>/HolyCleansing.py -c
```
_Every 4 hours_:
```cron
00 0,4,8,12,16,20 * * * python3 <installDirectory>/HolyCleansing.py -c
```

_Once a week (Sunday) at 01 in the morning_
```cron
00 01 * * 7 python3 <installDirectory>/HolyCleansing.py -c
```

_Once a month (the 1th) at 01 in the morning_
```cron
00 01 1 * * python3 <installDirectory>/HolyCleansing.py -c
```

## Reporting bugs and push requests
All contribution is welcome, just do a push requests with a tag `bug fix` or `improvement`

In case of bugs, with its description please attach the following elements:

- Kodi's version number
- OS name and version
- Python's version (in a terminal `python3 --version` or `python --version` for Windows)
- `HolyCleansing.log` file 

