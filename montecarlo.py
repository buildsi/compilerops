#!/usr/bin/env python3

# This script does the following.
# 1. Loads in data file (with flags) and a command string
# 2. Runs a model to add flags to them
# 3. Save to file

import numpy as np
import matplotlib.pyplot as plt

import argparse
import os
import sys
import re
import subprocess
import shlex
import json
from operator import itemgetter
import time

# keep global results
results = []


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
    gen.add_argument("--num-iter", help="number iterations", default=100, type=int)
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

    if isinstance(t, bytes):
        t = t.decode("utf-8")
    return t.strip(), output.returncode, end - start


class MonteCarloOptimizer:
    def __init__(self, func, x_init, data):
        """Initialize the optimizer.

        Args:
          func: The function whose value we want to minimize, e.g. runtime.
          x_init: The initial values to use.
        """
        self._func = func
        self._data = data
        self._dim = len(x_init)
        self._x_current = x_init
        self._func_val_current = None

    def get_func_val(self):
        """
        Lazily evaluate the current function value.
        """
        if self._func_val_current is None:
            self._func_val_current = self._func(self._x_current, self._data)
        return self._func_val_current

    def monte_carlo_step(self, num_change):
        """
        Take one step to try to improve the function value.

        Args:
          num_change: The number of bits to flip.
        Returns:
          The function value after possibly changing the state.
        """
        # Flip num_change values of the current x for the candidate.
        flip_indices = np.random.choice(self._dim, size=num_change)
        flip = np.zeros(self._dim)
        flip[flip_indices] = 1
        x = np.logical_xor(self._x_current, flip)

        func_val_candidate = self._func(x, self._data)
        # If the candidate function value is smaller (better), then update
        # the current x and current function value
        if func_val_candidate < self.get_func_val():
            self._x_current = x
            self._func_val_current = func_val_candidate
        return self._func_val_current

    def serial_monte_carlo(self, num_change, num_iter):
        """
        Use the Monte Carlo step with only one candidate at a time.

        Args:
          num_change: The number of bits to flip.
          num_iter: The number of iterations to take
        Returns:
          A list with the function values at each step taken.
        """
        values = [self.get_func_val()]
        for _ in range(num_iter):
            values.append(self.monte_carlo_step(num_change))
        return values


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

    # Extra is required with scripts to compile
    if not extra:
        sys.exit("Please include a script (e.g., main.cpp) to compile")

    with open(args.flags, "r") as fd:
        data = json.loads(fd.read())

    print("Found %s flags for the model." % len(data["opts"]))

    # Function to randomly select flags and return runtime
    def func(idx, data):
        """
        Take in full array of 0/1 to select flags
        """
        flags = [data["opts"][i] for i, x in enumerate(idx) if x == 1]
        cmd = data["executable"] + " " + " ".join(flags) + " " + " ".join(extra)
        print(cmd)
        out, err, _ = run_command(cmd)

        # Case 1: build fails off the bat
        if err != 0:
            results.append(["Build failure", np.inf, flags])
            return np.inf

        # Case 2: Output not generated
        if not os.path.exists("a.out"):
            results.append(["Build failure", np.inf, flags])
            return np.inf
        res = run_command("./a.out")

        # Case 3: Does not run
        if res[1] != 0:
            results.append(["Runtime error", np.inf, flags])
            return np.inf

        runtime = res[-1]
        results.append(["Run success", runtime, flags])

        # Clean up for next run
        if os.path.exists("a.out"):
            os.remove("a.out")
        return runtime

    # Initialize x to all zero (start with no flags)
    x_init = np.zeros(len(data["opts"]))
    mc = MonteCarloOptimizer(func, x_init, data)
    losses = mc.serial_monte_carlo(num_change=1, num_iter=args.num_iter)

    results_dir = os.path.join("data", "results", "montecarlo")
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    # If we don't have any output folders:
    if not os.listdir(results_dir):
        results_dir = os.path.join(results_dir, "0")
    else:
        dirs = [int(x) for x in os.listdir(results_dir)]
        dirs.sort()
        results_dir = os.path.join(results_dir, str(dirs[-1] + 1))

    # The directory should not exist!
    os.makedirs(results_dir)

    # Sort by times
    final = {"results": sorted(results, key=itemgetter(1)), "iters": args.num_iter}

    with open(
        os.path.join(
            results_dir, os.path.basename(args.flags.replace(".json", "_results.json"))
        ),
        "w",
    ) as fd:
        fd.write(json.dumps(final, indent=4))

    plt.plot(losses)
    plt.savefig(
        os.path.join(
            results_dir, os.path.basename(args.flags.replace(".json", "_results.png"))
        )
    )


if __name__ == "__main__":
    main()
