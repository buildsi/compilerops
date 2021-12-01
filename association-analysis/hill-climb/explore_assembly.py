#!/usr/bin/env python3

# python explore_assembly.py run data/flags-times-flat.csv

import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import seaborn as sns
import numpy as np
import pandas
import shlex

import argparse
from glob import glob
import fnmatch
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
    run.add_argument("csv", help="flags-times-flat.csv")
    return parser


def generate_assembly(df, outdir):

    # For each program and flag we want to compile!
    for _, row in df.iterrows():
        flag, program, value, filename = row
        if not filename.startswith(os.sep):
            filename = os.sep + filename
        out_dir = os.path.join(outdir, program, flag.strip("-").strip("-"))
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # Continue if we've done it already
        filemarker = os.path.join(out_dir, "filename.txt")
        if os.path.exists(filemarker):
            continue

        # Save filename there
        with open(filemarker, "w") as fd:
            fd.write(filename)
        with open(os.path.join(out_dir, "flag.txt"), "w") as fd:
            fd.write(flag)
        try:
            compile_program(flag, filename, out_dir)
        except:
            pass

def read_file(filename):
    with open(filename, 'r') as fd:
        content = fd.read()
    return content

def explore_assembly(df, outdir):
    """
    Can we tokenize instructions to understand how they change?

    E.g., Adding this flag changes tokens in this way, increases
    runtime by this much for this script."
    """
    # Keep a record of token counts and unique tokens
    unique_tokens = {}
    filenames = set()
    counts = {}

    # Helper function to count
    def count_tokens(content):
        tokens = {}
        for line in content.split('\n'):
            line = line.replace("\t", " ")
            for tok in line.split(' '):
                tok = tok.replace(" ", "")
                tok = tok.strip('"')
                if ":" in tok:
                   tok = tok.split(':')[0]
                if "0x" in tok:
                    continue
                if tok:
                    if tok not in tokens:
                        tokens[tok] = 0
                    tokens[tok] += 1
                    if tok not in unique_tokens: 
                        unique_tokens[tok] = 0                    
                    unique_tokens[tok] +=1
        return tokens

    # For each program and flag we want to compile!
    for _, row in df.iterrows():
        flag, program, value, filename = row
        if not filename.startswith(os.sep):
            filename = os.sep + filename
        out_dir = os.path.join(outdir, program, flag.strip("-").strip("-"))
            
        # Do we have Prog.S and ProgFlagged.S?
        flagged = os.path.join(out_dir, "ProgFlagged.s")
        prog = os.path.join(out_dir, "Prog.s")
        
        if os.path.exists(flagged) and os.path.exists(prog):
            filenames.add(flagged)
            filenames.add(prog)
            try:
                counts[flagged] = count_tokens(read_file(flagged))
                counts[prog] = count_tokens(read_file(prog))
            except:
                pass
            
    # We have to filter the tokens otherwise the data frame is too big!
    keepers = set()    
    counts = {}
    for tok, count in unique_tokens.items():
        if count >= 1000:
            keepers.add(tok)

    # Save to plot
    tokens = pandas.DataFrame(0, columns=list(keepers), index=list(filenames))
    for filename, toks in counts.items():
        for token_name, count in toks.items():
            if token_name not in keepers:
                continue
            tokens.loc[filename, token_name] += 1


    # Save tokens to file
    tokens.to_csv("data/assembly-tokens.csv")

    # For each one, look at differences (plot)
    prefixes = set([os.path.dirname(x) for x in filenames])    
    for prefix in prefixes:
        flagged = os.path.join(prefix, "ProgFlagged.s")
        prog = os.path.join(prefix, "Prog.s") 
        changed_columns = tokens.loc[[prog]].values != tokens.loc[[flagged]].values
        df_filtered = tokens.loc[[prog, flagged], changed_columns[0]]
        if df_filtered.shape[1] == 0:
            continue

        labels = list(df_filtered.columns)
        x = np.arange(len(labels))  # the label locations
        diff = df_filtered.loc[flagged] - df_filtered.loc[prog]

        # sort based on value
        diff = diff.sort_values()

        values_pos = diff.values.copy()
        values_neg = diff.values.copy()
        values_pos[values_pos < 0] = 0
        values_neg[values_neg > 0] = 0
        fig, ax = plt.subplots()
        width = 0.35
        rects_pos = ax.bar(x - width/2, values_pos, width, label='Additions')
        rects_neg = ax.bar(x - width/2, values_neg, width, label='Subtractions')
        
        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_ylabel('Difference in Count')
        ax.set_title('Change in program adding the flag for %s' % prefix)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=90)
        ax.legend()
        plt.savefig(os.path.join(prefix, "diffs.png"))
        plt.close()

    # Useful for the next function - the code is terrible yes! It's ok.
    return filenames

def recursive_find(base, pattern="*"):
    for root, _, filenames in os.walk(base):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)

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


def compile_program(flag, filename, out_dir):

    # Copy the file to the new directory in tmp
    basename = os.path.basename(filename)
    shutil.copyfile(filename, os.path.join(out_dir, basename))

    os.chdir(out_dir)

    # Generate assembly for program without flags
    cmd = "g++ -S " + basename + " -o Prog.s"
    os.system(cmd)

    cmd = "g++ " + flag + " -S " + basename + " -o ProgFlagged.s"
    os.system(cmd)

    if os.path.exists("Prog.s") and os.path.exists("ProgFlagged.s"):
        os.system("diff Prog.s ProgFlagged.s >> Prog.diff")

    os.chdir(here)

def color_by_different_assembly(df, filenames):

    # For each diff performed, figure out if the assembly is actually different.
    folders = list(set([os.path.dirname(x) for x in filenames]))
    diffs = pandas.DataFrame(0, index=folders, columns=['is_different'])
    for diff in recursive_find("data/compiled", "Prog.diff"):
       stat = os.stat(diff)
       if stat.st_size > 0:
           diffs.loc[os.path.dirname(diff), "is_different"] = 1

    diffs.to_csv("data/assembly-is-different.csv")

    # Create a colored manhatten plot based on this
    # Add a row for the same "is it different" value
    df["is_different"] = np.zeros(df.shape[0])
    missing = 0
    found = 0
    for idx, row in df.iterrows():
        flag, program, value, filename, _ = row
        if not filename.startswith(os.sep):
            filename = os.sep + filename
        out_dir = os.path.join(outdir, program, flag.strip("-").strip("-"))
        if out_dir in diffs.index:
            df.loc[idx, "is_different"] = diffs.loc[out_dir, "is_different"]
            found +=1
        else:
            missing += 1
            print("%s not in index" % out_dir)

    df.to_csv("data/flag-times-flag-with-diffs.csv")

    df.loc[:, "ind"] = range(len(df))
    df_grouped = df.groupby(("flag"))

    # manhattan plot
    fig = plt.figure(figsize=(20, 10))  # Set the figure size
    ax = fig.add_subplot(111)

    # Create vector of colors
    colors = []
    for x in df.iterrows():
        if x[1].is_different == 0:
            colors.append("darkblue")
        else:
            colors.append("gold")
    df['colors'] = colors        

    x_labels = []
    x_labels_pos = []
    for num, (name, group) in enumerate(df_grouped):
        if group.empty:
            continue
        group.plot(
            kind="scatter", x="ind", y="value", color=group["colors"], ax=ax
        )
        x_labels.append(name)
        x_labels_pos.append(
            (group["ind"].iloc[-1] - (group["ind"].iloc[-1] - group["ind"].iloc[0]) / 2)
        )
    ax.set_xticks(x_labels_pos)
    #ax.set_xticklabels(x_labels, rotation=45)

    # set axis limits
    ax.set_xlim([0, len(df)])
    ax.set_ylim([0, 3])

    # x axis label
    ax.set_xlabel("Flag")

    # show the graph
    plt.savefig("data/manhattan-flags-by-diff.pdf")
    plt.savefig("data/manhattan-flags-by-diff.png")


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

    # Create an output directory in data
    outdir = os.path.join("data", "compiled")
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    df = pandas.read_csv(args.csv, index_col=0)

    import IPython
    IPython.embed()

    # Try coloring by different assembly
    generate_assembly(df, outdir)
    filenames = explore_assembly(df, outdir)    
    color_by_different_assembly(df, filenames)
    # Filter to values >= 1.3
    #df = df[df.value >= 1.3]



if __name__ == "__main__":
    main()
