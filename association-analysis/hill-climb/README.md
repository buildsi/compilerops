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
for iter in {1..29}; do
   sbatch run_slurm.sh $iter
done
```

Note that [montecarlo-parallel.py](../montecarlo) considers flags in groups, while this hill-climb tests each flag separately.
I started with the first and moved to the latter because the first does not allow for truly understanding the marginal contribution of each
flag. I also wanted to run the binary multiple times to get a sense of the variance of running times.


## Post Analysis

This is the plan! This will require using the [tokens](../tokens). This is also subject to change!

**Preparation**: Take the union of all the tokens. Encode the token counts in each dimension.

## One token and one flag

This is the simpleset approach, but there will likely be spurious correlations found.

```
For each flag:
  If the flag doesn't appear more than a threshold number of times for any program, skip it
  For each token:
    Split the programs into sets depending on the frequency of the token. If there is only one category, skip it.
    Determine value of flag for each program (e.g., counts of the flag in optimal solutions, or expected improvement in program runtime when adding the flag)
    Find the correlation of <X, Y>  = <token count, flag value>.
```

We could also do this with a binary value (0/1) to say if the flag was chosen or not.

## Multiple tokens and one flag

Instead of looping through the tokens (second loop) do multiple regression where X is all the token counts. In other words, try to predict the 'flag values' from the tokens. This gives us the recovering impact of adding each flag, without having to re-run (without sorting, or keeping track of iteration):

```
For each experiment (i.e. 5000-steps), find the union of all flags across all steps. Store it as a set S.

Make a dictionary D mapping tuples of sorted flag names to values (i.e. runtimes).

Make another dictionary D_deltas whose keys are (single) flags. Each value will be a list of 2-tuples representing the elements of D before and after adding the flag. Or, optionally, if we just want the average runtime at the end, it could just be a list of times.

Iterate through D:
  Iterate through S:
    try to add (or remove if present) value in S from each element of D. If the result is again in D, update D_deltas
