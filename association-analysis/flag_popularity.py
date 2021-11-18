#!/usr/bin/env python3

# This script does the following.
# 1. Loads in results files
# 2. calculates percentage of time we see each flag for each file type
# 3. Save results to file

import numpy as np
import matplotlib.pyplot as plt
import pandas

import argparse
from glob import glob
import json
import os
import re
import shutil
import sys

import time

# keep global results
results = []

here = os.path.dirname(os.path.abspath(__file__))


def get_parser():
    parser = argparse.ArgumentParser(description="run")

    description = "Assess flag popularity"
    subparsers = parser.add_subparsers(
        help="actions",
        title="actions",
        description=description,
        dest="command",
    )
    assess = subparsers.add_parser("assess", help="run flag popularity")
    assess.add_argument("results_dir", help="root of results directory with numbered subfolders")
    return parser


def run_command(cmd):
    """
    A modified run command to return output and error code
    """
    cmd = shlex.split(cmd)
    try:
        start = time.time()
        output = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        end = time.time()
    except:
        return "", 1, np.inf
    t = output.communicate()[0]
    return "", output.returncode, end - start

def read_json(filename):
    with open(filename, 'r') as fd:
        content = json.loads(fd.read())
    return content

def assess_popularity(results_dirs):
    """
    Given a list of result directories, assess flag popularity.
    """
    flags = {}
    fails = {}
    # TODO should we count the number per run?
    for result_dir in results_dirs:
        results = glob("%s/*.json" % result_dir)
        for result in results:
            result_id = os.path.basename(result).split('.')[0]
            if result_id not in flags:
                flags[result_id] = {}
            result = read_json(result)
            # Last result is fastest
            fastest = result['results'][-1]
            if fastest[0] != "Run success":
                fails[result_id] = result['filename']
                continue
            for flag in fastest[2]:
                if flag not in flags[result_id]:
                    flags[result_id][flag] = 0
                else:
                   print("Duplicate flag %s found for %s" % (flag, result_id))
                flags[result_id][flag] += 1 
                            

def main():
    parser = get_parser()

    def help(return_code=0):
        parser.print_help()
        sys.exit(return_code)

    args, extra = parser.parse_known_args()
    if not args.command:
        help()

    # Load data
    if not args.results_dir or not os.path.exists(args.results_dir):
        sys.exit("%s missing or does not exist." % args.results_dir)

    results_dirs = sorted([int(x) for x in os.listdir(args.results_dir)])
    results_dirs = [os.path.join(args.results_dir, str(x)) for x in results_dirs]
    print("Found %s runs!" % len(results_dirs))    
    df = assess_popularity(results_dirs)


if __name__ == "__main__":
    main()
