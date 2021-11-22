#!/usr/bin/env python
#

import argparse
import fnmatch
from sklearn.manifold import MDS
import pandas
import sys
import os

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)

from cpp_tokenize import ReadFile, GetTokens

def get_parser():
    parser = argparse.ArgumentParser(description="run")
    parser.add_argument("code_dir", help="root of directory with cpp files to be discovered")
    parser.add_argument("pattern", help="pattern of filename to look for")
    return parser

def tokenize_cpp(code_files):
    tokens = {}
    names = set()
    for code_file in code_files:
        code_file = os.path.abspath(code_file)
        tokens[code_file] = {}
        for token in GetTokens(ReadFile(code_file)): 
            if token.name not in tokens[code_file]:
                tokens[code_file][token.name] = 0
            tokens[code_file][token.name] += 1
            # We will add these to a table
            names.add(token.name)

    df = pandas.DataFrame(tokens)

    # We want filenames in rows, features in cols
    df = df.transpose().fillna(0)
    return df


def recursive_find(base, pattern="Prog.cpp"):
    for root, _, filenames in os.walk(base):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)


def main():
    parser = get_parser()

    def help(return_code=0):
        parser.print_help()
        sys.exit(return_code)

    args, extra = parser.parse_known_args()

    # Load data
    if not args.code_dir or not os.path.exists(args.code_dir):
        sys.exit("%s missing or does not exist." % args.code_dir)

    code_files = list(recursive_find(args.code_dir, args.pattern))
    print("Found %s matching code files!" % len(code_files))   
    df = tokenize_cpp(code_files)
    
    # Clean up column names
    df.index = [x.replace(here, "").strip(os.sep) for x in list(df.index)]
    #df.to_csv(os.path.join(here, "data/cpp-tokens.csv")

    # How to do a transform to visualize
    mds = MDS(n_components=2, metric=True, n_init=4, max_iter=300, verbose=0, eps=0.001, n_jobs=1, random_state=None, dissimilarity='euclidean')
    result = pandas.DataFrame(mds.fit_transform(df))
    result.index = df.index
    result.to_csv(os.path.join(here, "data/cpp-tokens-embedding.csv")) 
    result['name'] = list(result.index)
    result.columns = ["cx", "cy", "name"]
    result.to_json(os.path.join(here, "data/cpp-tokens-embedding.json"), orient="records")


if __name__ == "__main__":
    main()
