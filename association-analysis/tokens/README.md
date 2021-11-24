# Token Generation

We would want to say "It's common for code with arrays to have better performance when compiled with these flags." To
avoid the complexities of parsing assembly (or something like that) instead we are going to tokenize
the CPP code, and keep track of counts for the number of things that we find (e.g., strings, for loops, etc.).
To do that:

```bash
$ python create_token_features.py ../code Prog.cpp
```
