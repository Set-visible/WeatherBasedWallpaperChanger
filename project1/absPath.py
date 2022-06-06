import struct
import ctypes
from pathlib import Path

SPI_SETDESKWALLPAPER = 20



def is_64_windows():
    """Find out how many bits is OS. """
    return struct.calcsize('P') * 8 == 64


def get_sys_parameters_info():
    """Based on if this is 32bit or 64bit returns correct version of SystemParametersInfo function. """
    return ctypes.windll.user32.SystemParametersInfoW if is_64_windows() \
        else ctypes.windll.user32.SystemParametersInfoA


def change_wallpaper(path):
    sys_parameters_info = get_sys_parameters_info()
    r = sys_parameters_info(SPI_SETDESKWALLPAPER, 0, path, 3)
    if not r:
        print(ctypes.WinError())


def getAbsolutePath():
    abspath = Path.cwd()
    abspath = str(abspath).replace("\\", '/', -1)
    return abspath



