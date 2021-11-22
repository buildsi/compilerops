# Association Analysis

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

And then clone examples:

```bash
$ git clone https://github.com/sinairv/Cpp-Tutorial-Samples examples
```

And then proceed with [montecarlo](montecarlo) or [hill-climb](hill-climb).
