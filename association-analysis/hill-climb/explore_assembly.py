#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import seaborn as sns
import numpy as np
import pandas
import shlex

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

        # Save filename there
        with open(os.path.join(out_dir, "filename.txt"), "w") as fd:
            fd.write(filename)
        with open(os.path.join(out_dir, "flag.txt"), "w") as fd:
            fd.write(flag)
        compile_program(flag, filename, out_dir)

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
    unique_tokens = set()
    filenames = set()
    counts = {}

    # For each program and flag we want to compile!
    for _, row in df.iterrows():
        flag, program, value, filename = row
        if not filename.startswith(os.sep):
            filename = os.sep + filename
        out_dir = os.path.join(outdir, program, flag.strip("-").strip("-"))

        # Do we have Prog.S and ProgFlagged.S?
        flagged = os.path.join(out_dir, "ProgFlagged.s")
        prog = os.path.join(out_dir, "Prog.s")

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
                        unique_tokens.add(tok)
            return tokens
        
        if os.path.exists(flagged) and os.path.exists(prog):
            filenames.add(flagged)
            filenames.add(prog)
            counts[flagged] = count_tokens(read_file(flagged))
            counts[prog] = count_tokens(read_file(prog))
            
    tokens = pandas.DataFrame(0, columns=list(unique_tokens), index=list(filenames))
    for filename, toks in counts.items():
        for token_name, count in toks.items():
            tokens.loc[filename, token_name] += 1

    # Save tokens to file
    tokens.to_csv("data/faster-assembly-tokens.csv")

    # For each one, look at differences
    prefixes = set([os.path.dirname(x) for x in filenames])    
    for prefix in prefixes:
        flagged = os.path.join(prefix, "ProgFlagged.s")
        prog = os.path.join(prefix, "Prog.s")
 
        # Find the column names where they aren't 0 or the same
        flagged_zeros = set(tokens.columns[tokens.loc[flagged] == 0])
        prog_zeros = set(tokens.columns[tokens.loc[flagged] == 0])
        to_remove = flagged_zeros.intersection(prog_zeros)

        # find where they are the same
        to_remove = to_remove.intersection(set(tokens.columns[tokens.loc[flagged] == tokens.loc[prog]]))
        to_keep = [x for x in tokens.columns if x not in to_remove]
        subset = pandas.DataFrame(index=[flagged, prog], columns=to_keep)
        subset.loc[flagged, to_keep] = tokens.loc[flagged, to_keep]
        subset.loc[prog, to_keep] = tokens.loc[prog, to_keep]

        diff = tokens.loc[flagged] tokens.loc[prog]
        newdf = pandas.DataFrame(columns)
        # TODO figure out what was added
        
    import IPython
    IPython.embed()

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

    # Filter to values >= 1.3
    df = df[df.value >= 1.3]

    #generate_assembly(df, outdir)
    explore_assembly(df, outdir)

if __name__ == "__main__":
    main()
