#!/usr/bin/env python3

# This script does the following.
# 1. Detects the system g++ compiler
# 2. Parses all possible options
# 3. Saves data to file (eventually can be done in container to save multiple types)

import argparse
import os
import sys
import re
import subprocess
import shlex
import json


def get_parser():
    parser = argparse.ArgumentParser(description="compilerops")

    description = "Figure out what compilerops to use"
    subparsers = parser.add_subparsers(
        help="actions",
        title="actions",
        description=description,
        dest="command",
    )

    gen = subparsers.add_parser(
        "gen", help="generate a data structure with compilers options"
    )
    gen.add_argument("executable", help="executable to use", choices=["g++"])
    return parser


def parse_gpp(exc):
    opts = {}

    # {common|optimizers|params|target|warnings|[^]{joined|separate|undocumented}
    for group in [
        "common",
        "optimizers",
        "params",
        "target",
        "warnings",
        "joined",
        "separate",
        "undocumented",
    ]:
        res = run_command("%s --help=%s" % (exc, group))
        for pair in res.split("\n"):
            try:
                flag, desc = pair.strip().split(" ", 1)
                if "-" in flag:
                    opts[flag.strip()] = desc.strip()
            except:
                pass
    return opts


def run_command(cmd, nofail=True):
    cmd = shlex.split(cmd)
    try:
        output = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    except FileNotFoundError:
        cmd.pop(0)
        output = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

    t = output.communicate()[0]
    output.returncode
    if output.returncode != 0 and nofail:
        sys.exit("Issue running command: %s: %s" % (t[0], t[1]))

    if isinstance(t, bytes):
        t = t.decode("utf-8")
    return t.strip()


def filter_opts(data):
    """
    filter down flags to those we can predict
    """
    flags = set()
    for flag, desc in data["opts"].items():
        if "help" in flag:
            continue
        # Skip those we can't predict
        if flag.endswith("="):
            continue
        if flag.endswith("<number>"):
            for num in range(0, 4):
                flags.add(flag.replace("<number>", str(num)))
        elif flag.endswith("]") and "|" in flag:
            args = flag.split("[", 1)[-1].strip("]")
            flag = flag.split("[")[0]
            for arg in args.split("|"):
                flags.add("%s%s" % (flag, arg))
        elif flag.endswith(">") and "|" in flag:
            args = flag.split("<", 1)[-1].strip(">")
            flag = flag.split("<")[0]
            for arg in args.split("|"):
                flags.add("%s%s" % (flag, arg))
        elif re.search("(>|])$", flag):
            continue
        elif not flag.startswith("-"):
            continue
        else:
            flags.add(flag)
    data["opts"] = list(flags)
    return data


def main():
    parser = get_parser()

    def help(return_code=0):
        parser.print_help()
        sys.exit(return_code)

    args, extra = parser.parse_known_args()
    if not args.command:
        help()

    data = {}
    opts = {}
    data["executable"] = run_command("which %s" % args.executable)
    data["version"] = run_command("%s --version" % data["executable"])

    if args.executable == "g++":
        data["opts"] = parse_gpp(data["executable"])

    args.executable = args.executable.replace("+", "p")
    with open(os.path.join("data", "%s_opts.json" % args.executable), "w") as fd:
        fd.write(json.dumps(data, indent=4))

    # Now filter down to those we can reasonably use
    filtered = filter_opts(data)
    with open(os.path.join("data", "%s_flags.json" % args.executable), "w") as fd:
        fd.write(json.dumps(filtered, indent=4))


if __name__ == "__main__":
    main()
