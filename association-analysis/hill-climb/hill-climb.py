#!/usr/bin/env python3

# This script does the following.
# 1. Loads in data file (with flags) and a command string
# 2. Runs a model to add flags to them
# 3. Save to file

import numpy as np
import statistics
import matplotlib.pyplot as plt

import multiprocessing
import argparse
import fnmatch
import itertools
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile

from operator import itemgetter
import time

# keep global results
results = []

here = os.path.dirname(os.path.abspath(__file__))


def get_parser():
    parser = argparse.ArgumentParser(description="run")

    description = "Run compile, keep track of outcomes and speed to run"
    subparsers = parser.add_subparsers(
        help="actions",
        title="actions",
        description=description,
        dest="command",
    )
    gen = subparsers.add_parser("run", help="run compiler with flags")
    gen.add_argument("flags", help="flags")
    gen.add_argument("script", help="path to filename of script to compile")
    gen.add_argument("--outdir-num", help="outdir number", default=0, type=int)
    gen.add_argument(
        "--root", help="root to discover programs to compile", default=os.getcwd()
    )
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


class HillClimber:
    def __init__(self, filename, data, results_dir):
        """
        Test each flag separately - "hill climbing"
        """
        self._data = data
        self.filename = filename
        self.results = []
        self.results_dir = results_dir

    def step(self, idx):
        """
        Test a specific flag
        """
        x_init = np.zeros(len(self._data["opts"]))
        x_init[idx] = 1
        self._func(x_init)

    # Function to randomly select flags and return runtime
    def _func(self, x_init):
        """
        Take in full array of 0/1 to select flags
        """
        # Work in a temporary directory
        tmpdir = tempfile.mkdtemp()
        here = os.getcwd()
        os.chdir(tmpdir)

        def clean_up():
            os.chdir(here)
            shutil.rmtree(tmpdir)

        # Copy the file to the new directory in tmp
        basename = os.path.basename(self.filename)
        shutil.copyfile(self.filename, os.path.join(tmpdir, basename))

        flags = [self._data["opts"][i] for i, x in enumerate(x_init) if x == 1]
        cmd = self._data["executable"] + " " + " ".join(flags) + " " + basename
        print(cmd)
        _, err, _ = run_command(cmd)

        # Case 1: build fails off the bat
        if err != 0:
            self.results.append(["Build failure", np.inf, flags])
            return

        # Case 2: Output not generated
        if not os.path.exists("a.out"):
            self.results.append(["Build failure", np.inf, flags])
            return

        # Run 10 times
        results = []
        for _ in range(100):
            res = run_command("./a.out")

            # Case 3: Does not run
            if res[1] != 0:
                self.results.append(["Runtime error", np.inf, flags])
                return

            runtime = res[-1]
            results.append(runtime)

        # If we get here, all success!
        # Calculate mean and sd
        self.results.append(
            [
                "Run success",
                [statistics.mean(results), statistics.stdev(results)],
                flags,
            ]
        )

        # Clean up for next run
        if os.path.exists("a.out"):
            os.remove("a.out")
        clean_up()
        return

    def climb(self):
        """
        Use the Monte Carlo step with only one candidate at a time.

        Args:
          num_change: The number of bits to flip.
        Returns:
          A list with the function values at each step taken.
        """
        # Test each flag! These are the indices
        for idx in range(len(self._data["opts"])):
            self.step(idx)
        self.save_results()

    def save_results(self):
        """
        Save results to file
        """
        identifier = (
            self.filename.replace(here, "")
            .replace(" ", "-")
            .replace(os.sep, "-")
            .strip("-")
        )
        result = {"filename": self.filename, "results": self.results}
        results_dir = os.path.join(here, self.results_dir)
        with open(os.path.join(results_dir, "%s.json" % identifier), "w") as fd:
            fd.write(json.dumps(result, indent=4))


def mkdirp(dirname):
    try:
        os.makedirs(dirname)
    except:
        pass


def func(filename, data, results_dir):
    climber = HillClimber(filename, data, results_dir)
    return climber.climb()


def main():
    parser = get_parser()

    def help(return_code=0):
        parser.print_help()
        sys.exit(return_code)

    args, extra = parser.parse_known_args()
    if not args.command:
        help()

    # Load data
    if not args.flags or not os.path.exists(args.flags):
        sys.exit("%s missing or does not exist." % args.flags)

    # A script is required
    if not args.script:
        sys.exit("Please include a script filename to compile across flags.")

    with open(args.flags, "r") as fd:
        data = json.loads(fd.read())

    print("Found %s flags for the model." % len(data["opts"]))

    results_dir = os.path.join("data", "results", "hill-climb-analysis")
    if not os.path.exists(results_dir):
        mkdirp(results_dir)

    # If we don't have any output folders:
    results_dir = os.path.join(results_dir, str(args.outdir_num))
    if not os.path.exists(results_dir):
        mkdirp(results_dir)

    # prepare tasks and functions for workers
    funcs = {}
    tasks = {}

    # Find files that match script, run a montecarlo in parallel for each
    kwargs = {
        "filename": os.path.abspath(args.script),
        "data": data,
        "results_dir": results_dir,
    }
    func(**kwargs)


if __name__ == "__main__":
    main()
