#!/usr/bin/env python
"""
Tool for for downloading retro IBM/Lenovo ThinkPad
drivers for various operating systems
"""

import logging
import argparse
import sys
import os
from bs4 import BeautifulSoup
import requests

LOGGER = logging.getLogger("thinkpad-driver-downloader")
"""
logging: Logger instance
"""
LOG_LEVEL = None
"""
logging: Logger level
"""
__version__ = "0.6.0"
"""
Program version
"""
OS_OPTIONS = {
    "dos": "MS-DOS",
    "win3x": "Windows 3.x",
    "os2": "OS/2",
    "winnt": "Windows NT",
    "win95": "Windows 95",
    "win98": "Windows 98",
    "winme": "Windows ME",
    "win2k": "Windows 2000",
    "xp": "Windows XP (32-bit)", 
    "xp_64": "Windows XP (64-bit)",
    "7_32": "Windows 7 (32-bit)",
    "7_64": "Windows 7 (64-bit)",
    "8_32": "Windows 8 (32-bit)",
    "8_64": "Windows 8 (64-bit)",
    "independent": "OS Independent"
}
"""
str: Operating system options
"""
DRIVER_GROUPS = {
    "audio": "Audio",
    "bios": "BIOS",
    "bios_uefi": "BIOS/UEFI",
    "bluetooth_modem": "Bluetooth and Modem",
    "camera_cardreader": "Camera and Card Reader",
    "chipset": "Chipset",
    "diagnostic": "Diagnostic",
    "display_video": "Display and Video Graphics",
    "enterprise": "Enterprise Management",
    "fingerprint": "Fingerprint reader",
    "mouse_keyboard": "Mouse and Keyboard",
    "lan": "Networking: LAN (Ethernet)",
    "wlan": "Networking: Wireless LAN",
    "wwan": "Networking: Wireless WAN",
    "optical": "Optical drive",
    "patch": "Patch",
    "power": "Power management",
    "recovery": "Recovery",
    "security": "Security",
    "preloaded_software": "Preloaded software",
    "software": "Software and Utility",
    "storage": "Storage",
    "vantage": "ThinkVantage Technology",
    "usb_firewire": "USB Device, FireWire, IEEE 1394",
    "win_update": "Windows Update"
}
"""
str: Driver groups
"""
# TODO: fix newlines for windows?
# TODO: win8_64 should also include win8.1_64
# Windows XP 32bit
# Windows XP 32-bit
# Windows XP x64


def download_file(url, overwrite=False):
    """
    Download a particular file
    """
    try:
        _file = requests.get(url, timeout=30)
        if _file.status_code == 403:
            LOGGER.error("Access denied: %s", url)
        if _file.status_code == 404:
            LOGGER.error("File not found: %s", url)
        if not os.path.exists(os.path.basename(url)) or overwrite:
            with open(os.path.basename(url), 'wb') as _dl:
                _dl.write(_file.content)
        else:
            LOGGER.info(
                "File '%s' already downloaded - use -f to overwrite",
                os.path.basename(url)
            )
    except requests.exceptions.SSLError:
        LOGGER.error("SSL certificate verification failed")
        sys.exit(1)


def is_blocklisted(link, blocklist):
    """
    Returns whether links is excluded by the blocklist
    """
    LOGGER.debug("***")
    LOGGER.debug(blocklist)
    _filename = os.path.basename(link)
    for entry in blocklist:
        LOGGER.debug(
            "Checking whether file '%s' is blocklisted by '%s'",
            _filename, blocklist
        )
        if entry in _filename:
            LOGGER.info("File '%s' is blocklisted!", _filename)
            return True
    return False


def parse_site(options):
    """
    Parses the particular model site
    """
    try:
        page = requests.get(
            f"{options.dl_site}/{options.model[0].lower()}.html",
            timeout=30,
            verify=options.ssl_verify
        )
        if page.status_code == 404:
            LOGGER.error(
                "Drive page for model '%s' not found - check site/model!",
                options.model[0].lower()
            )
            sys.exit(1)

        # find URLs
        _soup = BeautifulSoup( page.content , 'html.parser')

        if options.dl_all:
            _links = _soup.find_all('a')
        else:
            # set groups
            if options.dl_group:
                _groups = [''.join(x) for x in list(options.dl_group)]
            else:
                _groups = list(DRIVER_GROUPS.keys())

            # iterate through groups
            _return = []
            for _group in _groups:
                LOGGER.debug(
                    "Scanning %s drivers in %s group",
                    OS_OPTIONS[options.dl_os], _group
                )
                _links = _soup.find_all('div', id=DRIVER_GROUPS[_group])
                for _link in _links:
                    table = _link.find("table")
                    for row in table.findAll("tr"):
                        cols = [ e.stripped_strings.next() for e in row.find_all('td') if len(e.text)]
                        # data.append([e for e in cols if e])
                        print([e for e in cols if e])
            # TODO: implement
            # check for OS
            # check for group
            # _links = _soup.find_all('a')
            
            sys.exit(1)

        links = [x['href'] for x in _links if x['href']]

        # exclude filenames
        if options.dl_exclude:
            _blocklist = [''.join(x) for x in list(options.dl_exclude)]
            links = [x for x in links if not is_blocklisted(x, _blocklist)]

        return links
    except requests.exceptions.MissingSchema as err:
        LOGGER.error(
            "Invalid site url: '%s': %s",
            options.dl_site,
            err
        )
        sys.exit(1)
    except requests.exceptions.SSLError:
        LOGGER.error("SSL certificate verification failed")
        sys.exit(1)


def parse_options(args=None):
    """
    Parses options and arguments
    """
    desc = """%(prog)s is used for downloading IBM/Lenovo retro ThinkPad drivers
    for various operating systems.
    """
    epilog = """Check-out the website for more details:
     http://github.com/stdevel/thinkpad_driver_downloader"""
    parser = argparse.ArgumentParser(description=desc, epilog=epilog)
    parser.add_argument("--version", action="version", version=__version__)

    # define option groups
    gen_opts = parser.add_argument_group("generic arguments")
    dl_opts = parser.add_argument_group("download arguments")

    # GENERIC ARGUMENTS
    # -d / --debug
    gen_opts.add_argument(
        "-d",
        "--debug",
        dest="generic_debug",
        default=False,
        action="store_true",
        help="enable debugging outputs (default: no)",
    )

    # DOWNLOAD ARGUMENTS
    # -u / --url
    dl_opts.add_argument(
        "-u",
        "--url",
        dest="dl_site",
        metavar="SITE",
        default="https://download.lenovo.com/lenovo/content/ddfm",
        action="store",
        help="Alternate download site to use"
    )
    # -o / --os
    dl_opts.add_argument(
        "-o",
        "--os",
        dest="dl_os",
        metavar="OS",
        choices=OS_OPTIONS,
        action="store",
        required=True,
        help="Operating system to download drivers for"
    )
    # -g / --group
    dl_opts.add_argument(
        "-g",
        "--group",
        dest="dl_group",
        metavar="GROUP",
        nargs="*",
        choices=DRIVER_GROUPS.keys(),
        action="append",
        help="Groups to download files from (default: all)"
    )
    # -a / --all
    dl_opts.add_argument(
        "-a",
        "--all",
        dest="dl_all",
        action="store_true",
        default=False,
        help="Simply download _all_ the drivers (default: no)"
    )
    # -x / --exclude
    dl_opts.add_argument(
        "-x",
        "--exclude",
        dest="dl_exclude",
        metavar="FILENAME",
        nargs="*",
        action="append",
        help="Filenames to exclude (used as wildcard)"
    )
    # -f / --force
    dl_opts.add_argument(
        "-f",
        "--force",
        dest="dl_overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing files (default: no)"
    )
    # -l / --list
    dl_opts.add_argument(
        "-l",
        "--list",
        dest="dl_list_only",
        action="store_true",
        default=False,
        help="Only lists drivers that would be downloaded (default: no)"
    )
    dl_opts.add_argument(
        "-s",
        "--skip-ssl",
        dest="ssl_verify",
        action="store_false",
        default=True,
        help="Skip SSL verficiation (default: no)"
    )
    # device model
    dl_opts.add_argument(
        'model',
        metavar='MODEL',
        nargs=1,
        help='ThinkPad model (e.g. T23)'
    )

    # parse options and arguments
    options = parser.parse_args()
    return (options, args)


def main(options, args):
    """
    Main function, starts the logic based on parameters
    """
    LOGGER.debug("Options: %s", options)
    LOGGER.debug("Arguments: %s", args)

    _links = parse_site(options)
    LOGGER.debug("Found URLs: %s", _links)
    if options.dl_list_only:
        LOGGER.info(
            "Found %i URLs: %s",
            len(_links),
            _links
        )
        sys.exit(0)

    for _link in _links:
        LOGGER.info(
            "Downloading file %i/%i: %s",
            _links.index(_link)+1,
            len(_links),
            _link
        )
        download_file(_link, overwrite=options.dl_overwrite)


def cli():
    """
    This functions initializes the CLI interface
    """
    global LOG_LEVEL
    (options, args) = parse_options()

    # set logging level
    logging.basicConfig()
    if options.generic_debug:
        LOG_LEVEL = logging.DEBUG
    else:
        LOG_LEVEL = logging.INFO
    LOGGER.setLevel(LOG_LEVEL)

    main(options, args)


if __name__ == "__main__":
    cli()
