#!/usr/bin/env python3

# This script does the following.
# 1. Loads in data file (with flags) and a command string
# 2. Runs a tabu search model to add flags to them
# 3. Save to file

import numpy as np
import matplotlib.pyplot as plt
import itertools
import functools
import tempfile
import shutil

import multiprocessing
import signal
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

global data
global func
global extra


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
    gen.add_argument("--num-iter", help="number iterations", default=20, type=int)
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


class TabuSet(set):
    """
    A set with maximum size.
    """

    def __init__(self, max_size):
        super().__init__()
        self._max_size = max_size

    def add(self, val):
        super().add(val)
        if len(self) > self._max_size:
            return super().pop()


def argmax(iterable):
    return max(enumerate(iterable), key=lambda x: x[1])[0]


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


class TabuSearch:
    def __init__(self, func, x_init, cache_size=10000, tabu_size=1000):
        """
        Initialize the optimizer.

        Args:
          func: The function whose value we want to minimize, e.g. runtime.
          x_init: The initial values to use.
          data: data to pass to function
          cache_size: Maximum number of function values to keep in the cache.
          tabu_size: Maximum number of values in the Tabu set.
        """
        cached_func = functools.lru_cache(maxsize=cache_size)(func)
        self._func = lambda x: cached_func(tuple(x))
        self._dim = len(x_init)

        self._x_best = x_init
        self._x_current = x_init

        self._tabu_set = TabuSet(max_size=tabu_size)
        self._tabu_set.add(tuple(self._x_current))

    def get_neighbors(self, max_flip=1):
        """
        Get the neighbors in 0-1 space, excluding Tabu neighbors.

        Args:
          max_flip: The maximum number of bits to flip.
        Yields:
          A tuple (neighbor, value)
        """
        # prepare tasks and functions
        funcs = {}
        tasks = {}

        workers = Workers()
        flip_indices_iter = itertools.combinations(range(self._dim), max_flip)
        for flip_indices in flip_indices_iter:
            flip = np.zeros(self._dim, dtype=int)
            flip[flip_indices] = 1
            x = np.logical_xor(self._x_current, flip).astype(int)
            if tuple(x) not in self._tabu_set:
                funcs[tuple(x)] = func
                tasks[tuple(x)] = {"idx": x}

        return workers.run(funcs, tasks)

    def tabu_step(self, max_flip=1):
        neighbors = self.get_neighbors(max_flip=max_flip)
        self._x_current = min(neighbors, key=lambda x: x[1])[0]

        if self._func(self._x_current) < self._func(self._x_best):
            self._x_best = self._x_current
        self._tabu_set.add(tuple(self._x_current))
        return self._func(self._x_best)

    def tabu_search(self, num_iter=20, max_flip=1):
        values = [self._func(self._x_best)]
        for _ in range(num_iter):
            values.append(self.tabu_step(max_flip=max_flip))
        return values


# Function to randomly select flags and return runtime
def func(idx):
    """
    Take in full array of 0/1 to select flags
    """
    # Work in a temporary directory
    tmpdir = tempfile.mkdtemp()
    here = os.getcwd()

    def clean_up():
        os.chdir(here)
        shutil.rmtree(tmpdir)

    for filename in extra:
        shutil.copyfile(filename, os.path.join(tmpdir, filename))

    flags = [data["opts"][i] for i, x in enumerate(idx) if x == 1]
    cmd = data["executable"] + " " + " ".join(flags) + " " + " ".join(extra)
    print(cmd)
    os.chdir(tmpdir)
    out, err, _ = run_command(cmd)

    # Case 1: build fails off the bat
    if err != 0:
        results.append(["Build failure", np.inf, flags])
        clean_up()
        return np.inf

    # Case 2: Output not generated
    if not os.path.exists("a.out"):
        results.append(["Build failure", np.inf, flags])
        clean_up()
        return np.inf
    res = run_command("./a.out")

    # Case 3: Does not run
    if res[1] != 0:
        results.append(["Runtime error", np.inf, flags])
        clean_up()
        return np.inf

    runtime = res[-1]
    results.append(["Run success", runtime, flags])

    # Clean up for next run
    if os.path.exists("a.out"):
        os.remove("a.out")
    clean_up()
    return runtime


def main():
    parser = get_parser()

    # baaad practice
    global data
    global func
    global extra

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

    # Initialize x to all zero (start with no flags)
    x_init = np.zeros(len(data["opts"]))
    ts = TabuSearch(func, x_init)
    losses = ts.tabu_search(num_iter=args.num_iter)

    results_dir = os.path.join("data", "results", "tabu")
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


    items = [x[1] for x in final['results']]
    items.reverse()
    plt.plot(items)
    plt.savefig(
        os.path.join(
            results_dir, os.path.basename(args.flags.replace(".json", "_results.png"))
        )
    )


if __name__ == "__main__":
    main()
