#!/bin/bash
for iter in {0..9}; do
  find ./examples -name "*Prog.cpp" | parallel -I% --max-args 1 python montecarlo-parallel.py run ../data/gpp_flags.json "%" --outdir-num $iter --num-iter 2000
done
