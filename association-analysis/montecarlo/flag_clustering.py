#!/usr/bin/env python3

# This script does the following.
# 1. Loads in results files
# 2. calculates percentage of time we see each flag for each file type
# 3. Save results to file

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


def get_matrix(results_dirs):
    """
    Given a list of result directories, create a data frame of 0/1 for each result
    row, and label based on name + number of result
    """
    flags = {}
    fails = {}

    # Keep track of unique flags seen (can't be > 77x)
    unique_flags = set()
    unique_names = set()

    # First find unique flags
    for result_dir in results_dirs:
        results = glob("%s/*.json" % result_dir)
        for result in results:
            result_id = os.path.basename(result).split(".")[0]
            result_dir = os.path.basename(os.path.dirname(result))
            result_id = result_id + "_" + result_dir
            unique_names.add(result_id)
            result = read_json(result)
            # Last result is fastest
            fastest = result["results"][-1]
            if fastest[0] != "Run success":
                continue
            for flag in fastest[2]:
                unique_flags.add(flag)

    df = pandas.DataFrame(0, index=list(unique_names), columns=list(unique_flags))
    for result_dir in results_dirs:
        results = glob("%s/*.json" % result_dir)
        for result in results:
            result_id = os.path.basename(result).split(".")[0]
            result_dir = os.path.basename(os.path.dirname(result))
            result_id = result_id + "_" + result_dir
            result = read_json(result)
            fastest = result["results"][-1]
            if fastest[0] != "Run success":
                continue
            for flag in fastest[2]:
                df.loc[result_id, flag] = 1

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

    results_dirs = sorted([int(x) for x in os.listdir(args.results_dir)])
    results_dirs = [os.path.join(args.results_dir, str(x)) for x in results_dirs]
    print("Found %s runs!" % len(results_dirs))
    df = get_matrix(results_dirs)

    # How to do a transform to visualize
    # mds = MDS(n_components=2, metric=True, n_init=4, max_iter=300, verbose=0, eps=0.001, n_jobs=1, random_state=None, dissimilarity='euclidean')
    # result = pandas.DataFrame(mds.fit_transform(df))
    svd = TruncatedSVD(n_components=2, n_iter=7, random_state=42)
    result = pandas.DataFrame(svd.fit_transform(df))
    result.index = df.index
    result.to_csv(os.path.join(here, "data/cpp-tokens-embedding.csv"))
    result["name"] = list(result.index)
    result["group"] = [x.split("_")[0] for x in result.index]
    result.columns = ["cx", "cy", "name", "group"]
    result.to_json(
        os.path.join(here, "data/flag-choice-embedding.json"), orient="records"
    )


if __name__ == "__main__":
    main()
