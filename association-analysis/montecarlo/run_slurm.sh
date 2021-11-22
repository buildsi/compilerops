#!/bin/bash
find ../examples -name "*Prog.cpp" | parallel -I% --max-args 1 python montecarlo-parallel.py run ../../data/gpp_flags.json "%" --outdir-num $1 --num-iter 5000
