# Montecarlo Association Analysis

> People don't which flags to use in different scenarios.

This is a more scaled version of the original montecarlo simulation. For this small
analysis we have updated [montecarlo.py](montecarlo.py) so that it can run in parallel,
each time with a different script to run some number of iterations over. We have
also moved this processing to happen in temporary directories to keep the repository
a bit neater.

0. Make so montecarlo can run in parallel
1. Run MonteCarlo on all analyses here: https://github.com/sinairv/Cpp-Tutorial-Samples
2. Extract "features" of each with GoSmeagle (or similar to get code structure), turn into matrices
3. Make assocations between features and compile flags or compile time

## Usage

```bash
$ python -m venv env
$ source env/bin/activate
$ pip install -r requirements.txt
```

Make sure examples (code) is cloned one directory up!

### Generate Flags

The flags should already have been generated two folders up in [data](../../data). Note that we are using
the set without warnings (high 700s).

### Run Analyses!

Provide a path to the flags, and the root directory defaults to pwd, and give the filename to look for to compile:

```bash
$ python montecarlo.py run ../../data/gpp_flags.json Prog.cpp
```

In practice, I found that using parallel made more sense (no workers in Python).
Here is how to test a single script:

```bash
$ python montecarlo-parallel.py run ../../data/gpp_flags.json "../code/sizeof Operator/Prog.cpp" --outdir-num 1 --num-iter 2000
```

And then to run using parallel (`apt-get install -y parallel`)

```bash
$ find ../code -name "*Prog.cpp" | parallel -I% --max-args 1 python montecarlo-parallel.py run ../../data/gpp_flags.json "%" --outdir-num 1 --num-iter 2000
```

There is a [run.sh](run.sh) script that I used, and ultimately ran between a range of 0 and 29 (to generate 30 runs of the same predictions for 100 iterations each). Finally, to run on a SLURM cluster:

```bash
for iter in {11..30}; do
   sbatch run_slurm.sh $iter
done
```

Note that montecarlo-parallel.py considers flags in groups, while hill-climbing.py tests each flag separately.
I started with the first and moved to the latter because the first does not allow for truly understanding the marginal contribution of each
flag. I also wanted to run the binary multiple times to get a sense of the variance of running times.

### Find common flags

After we've run this many times, we'd want to see some kind of signal of common flags across runs. We can calculate the percentage
of time that we see each flag for each result file.

```bash
$ pip install -r requirements.txt
```

```bash
$ python flag_popularity.py assess data/results/montecarlo-association-analysis
```

Also, we want to see if there is clustering within runs:

```bash
$ python flag_clustering.py assess data/results/montecarlo-association-analysis
```

and

```bash
$ python group_flag_clustering.py assess data/results/montecarlo-association-analysis
```

At this point we didn't find much useful clustering, and went on to try a different approach.
[Hill climbing](../hill-climb) attempts to look at the impact of each flag and then compare with
[tokens](../tokens) in te source code.

