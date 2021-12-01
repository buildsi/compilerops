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
This will require using the [tokens](../tokens). Note that I tried this (script not preserved) and there was serious overfitting,
but I did notice in the PDF that some flags have HUGE performance improvements, so it might make sense to just look at them.

### Manhattan

What I quickly saw with linear regression was overfitting up the wazoo (like, a perfectly straight line, nope!) So I decided to look at the flags pdf and filter out some set of flags that had a huge increase in performance, and then I'd look at the assembly before and after. But first I thought I'd try a visualization that is usually used for showing significant gene p-values - the manhatten plot! For compiler flags!

```bash
$ python manhattan.py run data/flags-delta-times.csv ../tokens/data/cpp-tokens.csv
```

This generates a manhatten plot for all the flags, and then a filtered one with values > 1.3. As a reminder, a value of 1 is the baseline time for the program, so anything above 1 is faster. I like this visualization because it shows a nice little row of flags that are clearly better! But I wanted to filter it a bit more to better look at the actual flags, and that's the second pdf.

### Assembly

Okay - now we can filter down to a set of flags and scripts that have a bit better performance. What I want to do is to look at the assemly of the program with and without the flag, and try to understand what is being optimized.

```bash
$ python explore_assembly.py run data/flags-times-flat.csv
```

A basic question we can ask is if the assembly is different for programs that run faster with a flag, and then how.


Once I did this I realized there was a cool opportunity here - we not only might be interested in how the assembly differs with/without a flag (and how that maps to performance) but also which flags might have similar influence, or no influence at all. E.g.,

 - Generate assembly for the main program without flags, and then across flags
 - For each, break into tokens (features) with counts
 - Compare differences in tokens with/witout flags
 - be able to say "this flag changes the program in this way"
