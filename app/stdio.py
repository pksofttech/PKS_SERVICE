# ! Config For Debug
# from colr import Colr as C
from datetime import datetime, timedelta, timezone

# FMT='# :{lineno} in function {name}, file: {filename}'
from printdebug import DebugPrinter


class DebugColor:
    """Class DebugColor"""

    Default = "\033[39m"
    Black = "\033[30m"
    Red = "\033[31m"
    Green = "\033[32m"
    Yellow = "\033[33m"
    Blue = "\033[34m"
    Magenta = "\033[35m"
    Cyan = "\033[36m"
    LightGray = "\033[37m"
    DarkGray = "\033[90m"
    LightRed = "\033[91m"
    LightGreen = "\033[92m"
    LightYellow = "\033[93m"
    LightBlue = "\033[94m"
    LightMagenta = "\033[95m"
    LightCyan = "\033[96m"
    White = "\033[97m"

    HEADER = "\033[95m"
    DEBUG = Cyan
    SUCCESS = Green
    WARNING = Yellow
    ERROR = Red
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    INFO = "\033[96m"

    I = "\033[3m"
    U = "\033[4m"


# debug_enable(False)

dp = DebugPrinter(
    fmt=DebugColor.DEBUG
    + DebugColor.I
    + "[DEBUG]\t\t:{lineno}\t{filename}:\t#{name}:\t\t"
    + DebugColor.ENDC
)
print_debug = dp.debug

wp = DebugPrinter(
    fmt=DebugColor.WARNING
    + "[WARN]\t\t:{lineno}\t{filename}:\t#{name}:\t\t"
    + DebugColor.ENDC
)
print_warning = wp.debug

ep = DebugPrinter(
    fmt=DebugColor.ERROR
    + "[ERROR]\t\t:{lineno}\t{filename}:\t#{name}:\t\t"
    + DebugColor.ENDC
)
print_error = ep.debug

sp = DebugPrinter(
    fmt=DebugColor.SUCCESS
    + "[SUCCESS]\t:{lineno}\t{filename}:\t#{name}:\t\t"
    + DebugColor.ENDC
)
print_success = sp.debug
tz = timezone(timedelta(hours=7))


def time_now(utc=7):
    """For time data"""
    if utc == 0:
        return datetime.now() + timedelta(hours=7)

    t = datetime.now(tz=tz)
    return t.replace(tzinfo=None)


print_debug("test console print")
print_success("test console print_success")
print_warning("test console print_warning")
print_error("test console print_error")
