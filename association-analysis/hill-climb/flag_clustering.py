#!/usr/bin/env python3

# This script does the following.
# 1. Loads in results files
# 2. calculates percent change in time across flags
# 3. saves to data frame
# 4. Also visualizes

import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import TruncatedSVD
from sklearn.manifold import MDS
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

    description = "Assess flag times and generate data frame"
    subparsers = parser.add_subparsers(
        help="actions",
        title="actions",
        description=description,
        dest="command",
    )
    run = subparsers.add_parser("run", help="run flag popularity")
    run.add_argument(
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


def get_matrix(results):
    """
    Given a list of result directories, create a data frame of percent change
    of times.
    """
    flags = {}
    fails = {}

    # Keep track of unique flags seen (can't be > 77x)
    unique_flags = set()
    unique_names = set()

    # First find unique flags
    for result in results:
        result_id = os.path.basename(result).split(".")[0]
        unique_names.add(result_id)
        result = read_json(result)
        for x in result["results"]:
            if x[2]:
                unique_flags.add(x[2][0])

    # SCALING: 0 means it didn't work, close to zero means it was a much worse time,
    # 1 means it was the same, and >> 1 means it was an improvement
    df = pandas.DataFrame(0, index=list(unique_names), columns=list(unique_flags))
    for result in results:
        result_id = os.path.basename(result).split(".")[0]
        result = read_json(result)

        # If the baseline doesn't run, no go!
        if result["results"][0][0] in ["Build failure", "Runtime error"]:
            continue

        # The first result is the baseline
        baseline = result["results"][0][1][0]
        for entry in result["results"][1:]:

            # Skip build failures
            if entry[0] in ["Build failure", "Runtime error"]:
                continue

            runtime = entry[1][0]
            flag = entry[2][0]
            df.loc[result_id, flag] = 1 + (baseline - runtime) / runtime

    # rowsums = df.sum(axis=1)
    # df = df[rowsums > 0]
    # df = df.transpose() / df.sum(axis=1)
    # Clear out flags that appear fewer than 10 times across scripts (noise?)
    # df = (df.transpose()[df.sum(axis=0) > 10]).transpose()
    return df  # df.transpose()


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

    results_dirs = sorted(
        [x for x in os.listdir(args.results_dir) if x.endswith("json")]
    )
    results_dirs = [os.path.join(args.results_dir, x) for x in results_dirs]
    print("Found %s runs!" % len(results_dirs))
    df = get_matrix(results_dirs)
    df.index = [
        x.replace("usr-WS2-sochat1-compilerops-association-analysis-code-", "")
        for x in df.index
    ]
    fig = plot_heatmap(df, "data/flag-times.pdf")
    df.to_csv("data/flags-delta-times.csv")


if __name__ == "__main__":
    main()
