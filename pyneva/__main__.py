import argparse
import sys

from . import __version__
from . import tools
from .core import NevaMT3
from .types import MeterConnectionError, ErrorMessageReceived, ResponseError


def is_property(attr: str) -> bool:
    return type(getattr(NevaMT3, attr)) == property


FUNCTIONS = frozenset(filter(is_property, dir(NevaMT3)))

parser_description = "\033[31mAttention! Raw OBIS commands are much slower than " \
                     "prepared values.\nCLI version does not support write mode!\033[0m"
parser = argparse.ArgumentParser(
    usage="%(prog)s -i INTERFACE [-a ADDRESS] [-p PASSWORD] [--obis [OBIS ...]] [--val [...]]",
    description=parser_description, prog='pyneva',
    formatter_class=argparse.RawDescriptionHelpFormatter
)

parser.add_argument("-v", "--version", action='version', version=f"%(prog)s {__version__}")
parser.add_argument("-i", "--interface", required=True,
                    help="serial interface (can be RFC2217 uri)")
parser.add_argument("-a", "--addr", dest="address", default="", help="meter address")
parser.add_argument("-p", "--password", dest="password", default="", help="meter password")
parser.add_argument("--obis", nargs='*', default="", help="raw OBIS code(-s), format: XX.XX.XX*FF")
val_help = f"prepared value(-s). Possible values are {', '.join(sorted(FUNCTIONS))}. But some " \
           f"may not be supported by your meter"
parser.add_argument("--val", nargs='*', default="", choices=FUNCTIONS, metavar="", help=val_help)

args = parser.parse_args()

if len(args.obis) == 0 and len(args.val) == 0:
    parser.error("at least one of --obis and --func required")

try:
    with NevaMT3(interface=args.interface, address=args.address, password=args.password) as meter:
        print(f"Connected to: {meter}")

        if len(args.val) != 0:
            print("\nValues:")
            for func in args.val:
                print(f"{func}\t", getattr(meter, func))

        if len(args.obis) != 0:
            print("\nOBIS:")
            for code in args.obis:
                meter.send(tools.make_cmd_msg(code))
                print(f"{code}\t", tools.parse_data_msg(meter.recv()).data)
except (MeterConnectionError, ErrorMessageReceived, ResponseError) as e:
    sys.stderr.write(f"\n\033[31m{e.__class__.__name__}: {e}\033[0m\n")
