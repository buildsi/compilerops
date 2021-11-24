#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
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

    description = (
        "Run a linear regression to predict time improvement given a flag and tokens."
    )
    subparsers = parser.add_subparsers(
        help="actions",
        title="actions",
        description=description,
        dest="command",
    )
    run = subparsers.add_parser("run", help="run")
    run.add_argument("csv", help="flags-delta-times.csv")
    run.add_argument("tokens", help="tokens.csv")
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


def linear_regression(csv, tokens):
    flags = pandas.read_csv(csv, index_col=0)
    tokens = pandas.read_csv(tokens, index_col=0)

    # Replace tokens paths with same pattern as flags
    tokens.index = [
        x.replace("home/vanessa/Desktop/Code/compilerop/association-analysis/code/", "")
        .replace(" ", "-")
        .replace("/", "-")
        .rstrip(".cpp")
        for x in tokens.index
    ]

    import IPython

    IPython.embed()


# X = np.array([[1, 1], [1, 2], [2, 2], [2, 3]])
# >>> # y = 1 * x_0 + 2 * x_1 + 3
# >>> y = np.dot(X, np.array([1, 2])) + 3
# >>> reg = LinearRegression().fit(X, y)
# >>> reg.score(X, y)
# 1.0
# >>> reg.coef_
# array([1., 2.])
# >>> reg.intercept_
# 3.0...
# >>> reg.predict(np.array([[3, 5]]))
# array([16.])
#


def main():
    parser = get_parser()

    def help(return_code=0):
        parser.print_help()
        sys.exit(return_code)

    args, extra = parser.parse_known_args()
    if not args.command:
        help()

    # Load data
    if not args.csv or not os.path.exists(args.csv):
        sys.exit("%s missing or does not exist." % args.csv)

    linear_regression(args.csv, args.tokens)


if __name__ == "__main__":
    main()
