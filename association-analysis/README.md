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

And then clone code examples:

```bash
$ git clone https://github.com/sinairv/Cpp-Tutorial-Samples code
$ rm -rf code/.git
# preserve links
$ ln -s code examples
```

Note that two of the scripts have an interactive prompt, and you'll want to delete (or just
use the files stored here). I also removed a few that were input heavy, and adjusted any with
cin to use hard coded values.

```bash
$ grep -R ENTER
Aliases/Prog.cpp:	cout << "\n\nPress ENTER to exit.\n";
Arrays/Array in Functions/Prog.cpp:	cout <<"\n\nPress ENTER to exit.\n";
```

And then proceed with [montecarlo](montecarlo) or [hill-climb](hill-climb).
