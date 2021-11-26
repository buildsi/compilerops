#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import seaborn as sns
import numpy as np
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


def manhattan(csv, tokens):
    flags = pandas.read_csv(csv, index_col=0)
    tokens = pandas.read_csv(tokens, index_col=0)

    # Keep a lookup of index names to paths
    paths = list(tokens.index)

    # Replace tokens paths with same pattern as flags
    tokens.index = [
        x.replace("home/vanessa/Desktop/Code/compilerop/association-analysis/code/", "")
        .replace(" ", "-")
        .replace("/", "-")
        .rstrip(".cpp")
        for x in tokens.index
    ]

    lookup = {}
    for idx in range(len(paths)):
        lookup[tokens.index[idx]] = paths[idx]

    # Flatten the entire flags matrix
    print("Flattening flags data frame...")
    flat = pandas.DataFrame(columns=["flag", "program", "value", "filename"])
    count = 0
    for index, row in flags.iterrows():
        filename = lookup[index]
        for idx, value in enumerate(row):
            flag = flags.columns[idx]
            flat.loc[count] = [flag, index, value, filename]
            count += 1

    flat.to_csv("data/flags-times-flat.csv")

    # -log_10(pvalue)
    flat["minuslog10pvalue"] = -np.log10(flat.value)
    flat.flag = flat.flag.astype("category")
    flat = flat.sort_values("flag")
    flat["ind"] = range(len(flat))
    df_grouped = flat.groupby(("flag"))

    # manhattan plot
    fig = plt.figure(figsize=(40, 10))  # Set the figure size
    ax = fig.add_subplot(111)
    colors = ["darkred", "darkgreen", "darkblue", "gold"]
    x_labels = []
    x_labels_pos = []
    for num, (name, group) in enumerate(df_grouped):
        group.plot(
            kind="scatter", x="ind", y="value", color=colors[num % len(colors)], ax=ax
        )
        x_labels.append(name)
        x_labels_pos.append(
            (group["ind"].iloc[-1] - (group["ind"].iloc[-1] - group["ind"].iloc[0]) / 2)
        )
    ax.set_xticks(x_labels_pos)
    ax.set_xticklabels(x_labels, rotation=45)

    # set axis limits
    ax.set_xlim([0, len(flat)])
    ax.set_ylim([0, 3])

    # x axis label
    ax.set_xlabel("Flag")

    # show the graph
    plt.savefig("data/manhattan-flags.pdf")
    plt.savefig("data/manhattan-flags.png")

    # Finally let's filter down to those >= 1.3
    # Yes this code is redundant and terrible don't judge sometimes I do data science too!
    filtered = flat[flat.value >= 1.3]
    filtered.loc[:, "ind"] = range(len(filtered))
    df_grouped = filtered.groupby(("flag"))

    # manhattan plot
    fig = plt.figure(figsize=(20, 10))  # Set the figure size
    ax = fig.add_subplot(111)
    colors = ["darkred", "darkgreen", "darkblue", "gold"]
    x_labels = []
    x_labels_pos = []
    for num, (name, group) in enumerate(df_grouped):
        if group.empty:
            continue
        group.plot(
            kind="scatter", x="ind", y="value", color=colors[num % len(colors)], ax=ax
        )
        x_labels.append(name)
        x_labels_pos.append(
            (group["ind"].iloc[-1] - (group["ind"].iloc[-1] - group["ind"].iloc[0]) / 2)
        )
    ax.set_xticks(x_labels_pos)
    ax.set_xticklabels(x_labels, rotation=45)

    # set axis limits
    ax.set_xlim([0, len(filtered)])
    ax.set_ylim([0, 3])

    # x axis label
    ax.set_xlabel("Flag")

    # show the graph
    plt.savefig("data/manhattan-flags-filtered.pdf")
    plt.savefig("data/manhattan-flags-filtered.png")


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

    manhattan(args.csv, args.tokens)


if __name__ == "__main__":
    main()
