#!/usr/bin/env python3

# This script does the following.
# 1. Loads in data file (with flags) and a command string
# 2. Runs a model to add flags to them
# 3. Save to file

import numpy as np
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
    gen.add_argument("script", help="script to look for to compile")
    gen.add_argument("--num-iter", help="number iterations", default=100, type=int)
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

    if isinstance(t, bytes):
        t = t.decode("utf-8")
    return t.strip(), output.returncode, end - start


def recursive_find(base, pattern):
    for root, _, filenames in os.walk(base):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)


class Workers(object):
    def __init__(self, workers=9, show_progress=False):
        self.workers = workers

    def start(self):
        self.start_time = time.time()

    def end(self):
        self.end_time = time.time()
        self.runtime = self.runtime = self.end_time - self.start_time

    def run(self, funcs, tasks):
        """run will send a list of tasks, a tuple with arguments, through a function.
        the arguments should be ordered correctly.

        Parameters
        ==========
        funcs: the functions to run with multiprocessing.pool, a dictionary
               with lookup by the task name
        tasks: a dict of tasks, each task name (key) with a
               tuple of arguments to process
        """
        # Number of tasks must == number of functions
        assert len(funcs) == len(tasks)

        # Keep track of some progress for the user
        total = len(tasks)

        # if we don't have tasks, don't run
        if not tasks:
            return

        # results will also have the same key to look up
        finished = []
        results = []

        try:
            pool = multiprocessing.Pool(self.workers, init_worker)
            self.start()
            for key, params in tasks.items():
                func = funcs[key]
                result = pool.apply_async(multi_wrapper, multi_package(func, [params]))

                # Store the key with the result
                results.append((key, result))

            while len(results) > 0:
                pair = results.pop()
                key, result = pair
                result.wait()
                finished.append((key, result.get()))

            self.end()
            pool.close()
            pool.join()

        except (KeyboardInterrupt, SystemExit):
            pool.terminate()
            sys.exit(1)

        except:
            sys.exit("Error running task.")

        return finished


# Supporting functions for MultiProcess Worker
def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def multi_wrapper(func_args):
    function, kwargs = func_args
    return function(**kwargs)


def multi_package(func, kwargs):
    zipped = zip(itertools.repeat(func), kwargs)
    return zipped


class MonteCarloOptimizer:
    def __init__(self, filename, x_init, data, results_dir):
        """Initialize the optimizer.

        Args:
          func: The function whose value we want to minimize, e.g. runtime.
          x_init: The initial values to use.
        """
        self._data = data
        self._dim = len(x_init)
        self._x_current = x_init
        self._func_val_current = None
        self.filename = filename
        self.results = []
        self.results_dir = results_dir
        self.prefix = "mc"

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

    # Function to randomly select flags and return runtime
    def _func(self, idx, data):
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

        flags = [data["opts"][i] for i, x in enumerate(idx) if x == 1]
        cmd = data["executable"] + " " + " ".join(flags) + " " + basename
        print(cmd)
        out, err, _ = run_command(cmd)

        # Case 1: build fails off the bat
        if err != 0:
            self.results.append(["Build failure", np.inf, flags])
            return np.inf

        # Case 2: Output not generated
        if not os.path.exists("a.out"):
            self.results.append(["Build failure", np.inf, flags])
            return np.inf
        res = run_command("./a.out")

        # Case 3: Does not run
        if res[1] != 0:
            self.results.append(["Runtime error", np.inf, flags])
            return np.inf

        runtime = res[-1]
        self.results.append(["Run success", runtime, flags])

        # Clean up for next run
        if os.path.exists("a.out"):
            os.remove("a.out")
        clean_up()
        return runtime

    def serial_monte_carlo(self, num_change, num_iter):
        """
        Use the Monte Carlo step with only one candidate at a time.

        Args:
          num_change: The number of bits to flip.
          num_iter: The number of iterations to take
        Returns:
          A list with the function values at each step taken.
        """
        for _ in range(num_iter):
            self.monte_carlo_step(num_change)
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
        values = sorted(self.results, key=itemgetter(1), reverse=True)
        result = {"filename": self.filename, "results": values}
        results_dir = os.path.join(here, self.results_dir)
        with open(os.path.join(results_dir, "%s.json" % identifier), "w") as fd:
            fd.write(json.dumps(result, indent=4))
        losses = [x[1] for x in values]
        plt.plot(losses)
        plt.savefig(os.path.join(results_dir, "%s.png" % identifier))
        plt.close()


def func(filename, data, num_iter, results_dir):
    x_init = np.zeros(len(data["opts"]))
    mc = MonteCarloOptimizer(filename, x_init, data, results_dir)
    return mc.serial_monte_carlo(num_change=1, num_iter=num_iter)


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
        sys.exit(
            "Please include a script name (e.g., Prog.cpp) to discover from the root."
        )

    with open(args.flags, "r") as fd:
        data = json.loads(fd.read())

    print("Found %s flags for the model." % len(data["opts"]))

    results_dir = os.path.join("data", "results", "montecarlo-association-analysis")
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    # If we don't have any output folders:
    if not os.listdir(results_dir):
        results_dir = os.path.join(results_dir, "0")
    else:
        dirs = [int(x) for x in os.listdir(results_dir)]
        dirs.sort()
        results_dir = os.path.join(results_dir, str(dirs[-1] + 1))

    os.makedirs(results_dir)

    # prepare tasks and functions for workers
    funcs = {}
    tasks = {}

    # Find files that match script, run a montecarlo in parallel for each
    for filename in recursive_find(args.root, args.script):
        funcs[filename] = func
        tasks[filename] = {
            "filename": filename,
            "data": data,
            "num_iter": args.num_iter,
            "results_dir": results_dir,
        }

    # Create set of workers
    workers = Workers()
    workers.run(funcs, tasks)


if __name__ == "__main__":
    main()
