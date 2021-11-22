#!/bin/bash
for iter in {0..9}; do
  find ../examples -name "*Prog.cpp" | parallel -I% --max-args 1 python hill-climb.py run ../../data/gpp_flags.json "%" --outdir-num $iter
done
