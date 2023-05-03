# Demo Scikit Build Core with Griffe

This repository demonstrates a bug with [Griffe](https://github.com/mkdocstrings/griffe) when building a project with [scikit-build-core](https://github.com/scikit-build/scikit-build-core). The issue is specifically when you build a project in editable mode: `pip install -e .`. If you build normally, `pip install .`, then griffe will be able to find modules within your package.


## Steps to reproduce

1. Clone this repo and change into its directory
2. Create some form of a virtual environment
    1. I use conda: `conda create --name bug python=3.10`
3. `pip install -e .`
