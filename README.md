# Compilerops

How do different compiler flags lead to different optimizations and performance results?

1. Write a simple program with two loops.
2. The architecture is pinned, but we can eventually try on different machines.
3. The version of g++ is important - to start we will pin with my host (and then vary)
4. Create a container with some version of g++ (as stated we can eventually vary)
5. We need to programatically derive flags.
6. Once we have flags, we need to randomly choose a set, compile, and save if it worked, and how fast it runs.
7. Try different models to select for flags that work, and record time on successful run!

For the last point, the easiest thing to do is have the script time itself.

## Included

 - In this directory includes [compilerops.py](compilerops.py) to generate compiler flags to use across different analyses.
 - [simple](simple): includes my first attempts at a montecarlo and tabu search
 - [association-analysis/montecarlo](association-analysis/montecarlo): was a second shot to choose groups of flags
 - [association-analysis/hill-climb](association-analysis/hill-climb): was another effort to try and distinguish the impact of each flag, and add a more substantial linking of flags with tokens.
 - [association-analysis/tokens](association-analysis/tokens): tokenizes the example scripts.

### Dependencies

```bash
$ python -m venv env
$ source env/bin/activate
$ pip install -r requirements.txt
```

### Generate Flags

```bash
$ python compilerops.py gen g++
```

Will generate filtered [data/gpp_flags.json](data/gpp_flags.json)

**important** the first two times I ran monte carlo and the tabu search I included warnings, and later removed these.
The original data (suffix _warnings.json) is included in the data folder.
