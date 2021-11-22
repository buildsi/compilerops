#!/usr/bin/env python3

# This script does the following.
# 1. Loads in results files
# 2. calculates percentage of time we see each flag for each file type
# 3. Save results to file

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
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
    assess.add_argument(
        "results_dir", help="root of results directory with numbered subfolders"
    )
    return parser


def plot_heatmap(df, save_to=None):
    sns.set_theme(style="white")

    f, ax = plt.subplots(figsize=(30, 30))
    # Generate a custom diverging colormap
    cmap = sns.color_palette()

    # Draw the heatmap with the mask and correct aspect ratio
    p = sns.clustermap(df, cmap=cmap)
    # used for heatmap
    # p.tick_params(labelsize=5)
    # p.set_xlabel("Splice", fontsize=12)
    # p.set_ylabel("Binary", fontsize=12)

    if save_to:
        plt.savefig(save_to)
    return plt


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
    with open(filename, "r") as fd:
        content = json.loads(fd.read())
    return content


def assess_popularity(results_dirs):
    """
    Given a list of result directories, assess flag popularity.
    """
    flags = {}
    fails = {}

    # Keep track of unique flags seen (can't be > 77x)
    unique_flags = set()

    # Number of times we've run the program
    counts = {}

    for result_dir in results_dirs:
        results = glob("%s/*.json" % result_dir)
        for result in results:
            result_id = os.path.basename(result).split(".")[0]
            for item in [flags, counts]:
                if result_id not in item:
                    item[result_id] = {}
            result = read_json(result)
            # Last result is fastest
            fastest_group = result["results"][-100:]
            for fastest in fastest_group:
                if fastest[0] != "Run success":
                    fails[result_id] = result["filename"]
                    continue
                for flag in fastest[2]:
                    unique_flags.add(flag)
                    if flag not in flags[result_id]:
                        flags[result_id][flag] = 0
                    flags[result_id][flag] += 1

    # For each entry, sort
    for name, result in flags.items():
        flags[name] = {
            k: v for k, v in sorted(result.items(), key=lambda item: item[1])
        }

    # All unique flags

    # Now we want a value for how many times the flag appears for a program
    df = pandas.DataFrame(0, index=list(flags.keys()), columns=list(unique_flags))
    for name, result in flags.items():
        for flag, count in result.items():
            df.loc[name, flag] += count

    return df


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
    df.to_csv("data/flag-popularity.csv")
    fig = plot_heatmap(df, "data/flag-popularity.svg")
    fig = plot_heatmap(df, "data/flag-popularity.png")
    fig = plot_heatmap(df, "data/flag-popularity.pdf")


if __name__ == "__main__":
    main()
