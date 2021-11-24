# Hill Climbing

For this analysis, we want to be able to understand the contribution of each flag,
so we are going to stupidly loop through them and measure it, and also collect 10 samples of runtimes
to know the variance. This process can be called [hill climbing](https://web.cs.hacettepe.edu.tr/~ilyas/Courses/VBM688/lec05_localsearch.pdf).

## Usage

```bash
$ python -m venv env
$ source env/bin/activate
$ pip install -r ../requirements.txt
```

Make sure examples (code) are cloned one directory up!

### Generate Flags

The flags should already have been generated two folders up in [data](../../data). Note that we are using
the set without warnings (high 700s).

### Run Analyses!

Provide a path to the flags, and the root directory defaults to pwd, and give the filename to look for to compile:

```bash
$ python hill-climb.py run ../../data/gpp_flags_filtered.json Prog.cpp
```
for a specific example:

```bash
$ python hill-climb.py run ../../data/gpp_flags_filtered.json ../code/Aliases/Prog.cpp
```

In practice, I found that using parallel made more sense (no workers in Python).
Here is how to test a single script:

```bash
$ python hill-climb.py run ../../data/gpp_flags.json "../code/sizeof Operator/Prog.cpp" --outdir-num 1
```

And then to run using parallel (`apt-get install -y parallel`)

```bash
$ find ../code -name "*Prog.cpp" | parallel -I% --max-args 1 python hill-climb.py run ../../data/gpp_flags.json "%" --outdir-num 1
```

There is a [run.sh](run.sh) script that I used, and ultimately ran between a range of 0 and 29 (to generate 30 runs of the same predictions for 100 iterations each). Finally, to run on a SLURM cluster:

```bash
# We only need one run!
for iter in {0..0}; do
   sbatch run_slurm.sh $iter
done
```

Note that [montecarlo-parallel.py](../montecarlo) considers flags in groups, while this hill-climb tests each flag separately.
I started with the first and moved to the latter because the first does not allow for truly understanding the marginal contribution of each
flag. I also wanted to run the binary multiple times to get a sense of the variance of running times.


## Post Analysis

### Data Preparation

First let's read in the data, and prepare a matrix of percent changes. E.g., if we have a mean runtime for a compiled program
(N=100 times run) we can subtract the runtime without any flags (also N=100) to get an percent change.

```bash
$ python flag_clustering.py run data/results/hill-climb-analysis/0
```

This generates the pdf in [data](data) to show a basic clustering of flags, where the mapping of times is the following:

```bash
failure -> 0
no change -> 1
slower -> between 0 and 1
faster -> greater than 1
time = 0 -> infinitely large
```
E.g., given a baseline time (running without any flags) and a runtime with one flag, we calculate the value
by doing:

```
1 + (baseline - runtime) / runtime
```

### Linear Regression

The goal here would be to predict the importance of a flag based on tokens, or breaking the code up into tiny pieces.
This will require using the [tokens](../tokens).

```bash
$ python linear_regression.py data/flags-delta-times.csv ../tokens/data/
```

TODO:

this is overfitting up the wazoo! Let's look at the flags pdf and find the few flags that do a LOT better and try to understand why.
