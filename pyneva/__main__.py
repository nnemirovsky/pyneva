import argparse
import sys

from . import __version__
from . import meters
from . import tools
from .types import MeterConnectionError, ResponseError


def is_property(klass, attr: str) -> bool:
    return type(getattr(klass, attr)) == property and "__" not in attr


connect_description = "\033[31mAttention! Raw OBIS commands are much slower than " \
                      "prepared values.\nCLI version does not support write mode!\033[0m"
parser = argparse.ArgumentParser(prog='pyneva',
                                 formatter_class=argparse.RawDescriptionHelpFormatter)

subparsers = parser.add_subparsers()

connect = subparsers.add_parser(
    'connect', help='connect help', description=connect_description,
    formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, max_help_position=40),
    usage="%(prog)s -i INTERFACE -m MODEL [-b BAUDRATE] [-a ADDRESS] [-p PASSWORD] "
          "[-v [value(-s)]] [--obis [code(-s)]]"
)
connect.set_defaults(parser=connect)
connect.add_argument("-v", "--version", action='version', version=f"%(prog)s {__version__}")

connect.add_argument("-i", "--interface", required=True,
                     help="serial interface (can be RFC2217 uri)")
connect.add_argument("-m", "--model", required=True,
                     help="meter class (can be obtained from the command `get-model`)")
connect.add_argument("-b", "--baudrate", default=300, type=int,
                     help="initial baudrate (default: 300), specify 9600 for RS485")
connect.add_argument("-a", "--addr", dest="address", default="", help="meter address")
connect.add_argument("-p", "--password", dest="password", default="", help="meter password")
connect.add_argument("-v", "--val", nargs='*', default="", metavar="",
                     help="prepared value(-s). The available values for your meter can be "
                          "obtained from the command `get-values`")
connect.add_argument("--obis", nargs='*', default="", metavar="",
                     help="raw OBIS code(-s), format: XX.XX.XX*XX")

get_model = subparsers.add_parser(
    'get-model', help='get-model help', usage="%(prog)s -i INTERFACE [-b BAUDRATE] [-a ADDRESS]",
    formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, max_help_position=40),
)
get_model.set_defaults(parser=get_model)
get_model.add_argument("-i", "--interface", required=True,
                       help="serial interface (can be RFC2217 uri)")
get_model.add_argument("-b", "--baudrate", default=300, type=int,
                       help="initial baudrate (default: 300), specify 9600 for RS485")
get_model.add_argument("-a", "--addr", dest="address", default="", help="meter address")

get_values = subparsers.add_parser(
    'get-values', help='get-values help',
    formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, max_help_position=40))
get_values.set_defaults(parser=get_values)
get_values.add_argument("-m", "--model", required=True,
                        help="meter class (can be obtained from the command `get-model`)")

args = parser.parse_args()

fn = args.parser.prog.split()[1]

cls = meters.NevaMT3R
if fn in ("connect", "get-values"):
    cls = vars(meters)[args.model]

if fn == "get-model":
    klass = tools.start_without_model(interface=args.interface, address=args.address,
                                      initial_baudrate=args.baudrate, do_not_open=True)
    print("Class that you need:", klass.__name__)

if fn == "get-values":
    values = frozenset(filter(lambda x: is_property(cls, x), dir(cls)))
    print(f"Possible values are {', '.join(sorted(values))}. But some may not be supported by "
          f"your meter")
if fn == "connect":
    if len(args.obis) == 0 and len(args.val) == 0:
        parser.error("at least one of --obis and --val required")

    try:
        with cls(interface=args.interface, address=args.address, password=args.password,
                 initial_baudrate=args.baudrate) as meter:
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
    except (MeterConnectionError, ResponseError, AttributeError) as e:
        # sys.stderr.write(f"\n\033[31m{e.__class__.__name__}: {e}\033[0m\n")
        sys.stderr.write(f"\n\033[31m{type(e).__name__}: {e}\033[0m\n")
