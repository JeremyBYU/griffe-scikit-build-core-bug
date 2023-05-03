# Demo Scikit Build Core with Griffe

This repository demonstrates a bug with [Griffe](https://github.com/mkdocstrings/griffe) when building a project with [scikit-build-core](https://github.com/scikit-build/scikit-build-core). The issue is specifically when you build a project in editable mode: `pip install -e .`. If you build normally, `pip install .`, then griffe will be able to find modules within your package.


## Steps to reproduce


1. Clone this repo and change into its directory
2. Create some form of a virtual environment
    1. I use conda: `conda create --name bug python=3.10; conda activate bug`

**Demo Local Install (Works)**   

1. `pip install .`
2. `griffe dump griffedemo`

Outputs:

```json
❯ griffe dump griffedemo
{
  "griffedemo": {
    "kind": "module",
    "name": "griffedemo",
    "labels": [],
    "members": [
      {
        "kind": "alias",
        "name": "__doc__",
        "target_path": "griffedemo._core.__doc__",
        "lineno": 1,
        "endlineno": 1
      },
      {
        "kind": "alias",
        "name": "__version__",
        "target_path": "griffedemo._core.__version__",
        "lineno": 1,
        "endlineno": 1
      },
      {
        "kind": "alias",
        "name": "add",
        "target_path": "griffedemo._core.add",
        "lineno": 1,
        "endlineno": 1
      },
      {
        "kind": "alias",
        "name": "subtract",
        "target_path": "griffedemo._core.subtract",
        "lineno": 1,
        "endlineno": 1
      },
      {
        "kind": "attribute",
        "name": "__all__",
        "lineno": 3,
        "endlineno": 3,
        "labels": [
          "module-attribute"
        ],
        "members": [],
        "value": "['__doc__', '__version__', 'add', 'subtract']"
      },
      {
        "kind": "module",
        "name": "purepython",
        "labels": [],
        "members": [
          {
            "kind": "alias",
            "name": "math",
            "target_path": "math",
            "lineno": 1,
            "endlineno": 1
          },
          {
            "kind": "alias",
            "name": "Tuple",
            "target_path": "typing.Tuple",
            "lineno": 2,
            "endlineno": 2
          },
          {
            "kind": "function",
            "name": "solve_quadratic",
            "lineno": 4,
            "endlineno": 18,
            "docstring": {
              "value": "Will solve the quadratic equation ax^2 + bx + c = 0\n\nArgs:\n    a (float): x^2 constant\n    b (float): x constant\n    c (float): constant\n\nReturns:\n    Tuple[float, float]: The roots of x",
              "lineno": 5,
              "endlineno": 14
            },
            "labels": [],
            "members": [],
            "decorators": [],
            "parameters": [
              {
                "name": "a",
                "annotation": {
                  "source": "float",
                  "full": "float"
                },
                "kind": "positional or keyword",
                "default": null
              },
              {
                "name": "b",
                "annotation": {
                  "source": "float",
                  "full": "float"
                },
                "kind": "positional or keyword",
                "default": null
              },
              {
                "name": "c",
                "annotation": {
                  "source": "float",
                  "full": "float"
                },
                "kind": "positional or keyword",
                "default": null
              }
            ],
            "returns": [
              {
                "source": "Tuple",
                "full": "typing.Tuple"
              },
              "[",
              [
                {
                  "source": "float",
                  "full": "float"
                },
                ", ",
                {
                  "source": "float",
                  "full": "float"
                }
              ],
              "]"
            ]
          }
        ],
        "filepath": "C:\\Users\\Jerem\\scoop\\apps\\mambaforge\\current\\lib\\site-packages\\griffedemo\\purepython\\__init__.py"
      }
    ],
    "filepath": "C:\\Users\\Jerem\\scoop\\apps\\mambaforge\\current\\lib\\site-packages\\griffedemo\\__init__.py"
  }
}
```

**Demo Editable Install (Doesn't Work)**

1. `pip install -e .`
2. `griffe dump griffedemo`

Output:

```
❯ griffe dump griffedemo
INFO       Loading package griffedemo
ERROR      Could not find package griffedemo: No module named 'griffedemo._core'
INFO       Finished loading packages
{}
```

## The problem?

scikit-build-core used an interesting way to do editable installs. The basic idea is they override MetaPathFinder to link your local files. Here are some of the files inside your site-packages folder:

**_griffedemo_editable.pth**
```
import _griffedemo_editable

```

**_griffedemo_editable.py**
```python
from __future__ import annotations

import importlib.abc
import importlib.machinery
import importlib.util
import os
import subprocess
import sys

DIR = os.path.abspath(os.path.dirname(__file__))
MARKER = "SKBUILD_EDITABLE_SKIP"
VERBOSE = "SKBUILD_EDITABLE_VERBOSE"

__all__ = ["install"]


def __dir__() -> list[str]:
    return __all__


class ScikitBuildRedirectingFinder(importlib.abc.MetaPathFinder):
    def __init__(
        self,
        known_source_files: dict[str, str],
        known_wheel_files: dict[str, str],
        path: str | None,
        rebuild: bool,
        verbose: bool,
    ):
        self.known_source_files = known_source_files
        self.known_wheel_files = known_wheel_files
        self.path = path
        self.rebuild_flag = rebuild
        self.verbose = verbose

    def find_spec(
        self,
        fullname: str,
        path: object = None,
        target: object = None,
    ) -> importlib.machinery.ModuleSpec | None:
        if fullname in self.known_wheel_files:
            redir = self.known_wheel_files[fullname]
            if self.rebuild_flag:
                self.rebuild()
            return importlib.util.spec_from_file_location(
                fullname, os.path.join(DIR, redir)
            )
        if fullname in self.known_source_files:
            redir = self.known_source_files[fullname]
            return importlib.util.spec_from_file_location(fullname, redir)

        return None

    def rebuild(self) -> None:
        # Don't rebuild if not set to a local path
        if not self.path:
            return

        env = os.environ.copy()
        # Protect against recursion
        if self.path in env.get(MARKER, "").split(os.pathsep):
            return

        env[MARKER] = os.pathsep.join((env.get(MARKER, ""), self.path))

        verbose = self.verbose or bool(env.get(VERBOSE, ""))
        if env.get(VERBOSE, "") == "0":
            verbose = False
        if verbose:
            print(f"Running cmake --build & --install in {self.path}")  # noqa: T201

        result = subprocess.run(
            ["cmake", "--build", "."],
            cwd=self.path,
            stdout=sys.stderr if verbose else subprocess.PIPE,
            env=env,
            check=False,
            text=True,
        )
        if result.returncode and verbose:
            print(  # noqa: T201
                f"ERROR: {result.stdout}",
                file=sys.stderr,
            )
        result.check_returncode()

        result = subprocess.run(
            ["cmake", "--install", ".", "--prefix", DIR],
            cwd=self.path,
            stdout=sys.stderr if verbose else subprocess.PIPE,
            env=env,
            check=False,
            text=True,
        )
        if result.returncode and verbose:
            print(  # noqa: T201
                f"ERROR: {result.stdout}",
                file=sys.stderr,
            )
        result.check_returncode()


def install(
    known_source_files: dict[str, str],
    known_wheel_files: dict[str, str],
    path: str | None,
    rebuild: bool = False,
    verbose: bool = False,
) -> None:
    """
    Install a meta path finder that redirects imports to the source files, and
    optionally rebuilds if path is given.

    :param known_source_files: A mapping of module names to source files
    :param known_wheel_files: A mapping of module names to wheel files
    :param path: The path to the build directory, or None
    :param verbose: Whether to print the cmake commands (also controlled by the
                    SKBUILD_EDITABLE_VERBOSE environment variable)
    """
    sys.meta_path.insert(
        0,
        ScikitBuildRedirectingFinder(
            known_source_files, known_wheel_files, path, rebuild, verbose
        ),
    )


install({'griffedemo': 'C:\\Users\\Jerem\\Documents\\Springfield\\Research\\griffe-scikit-build-core-bug\\src\\griffedemo\\__init__.py', 'griffedemo.purepython': 'C:\\Users\\Jerem\\Documents\\Springfield\\Research\\griffe-scikit-build-core-bug\\src\\griffedemo\\purepython\\__init__.py'}, {'cmake_example': 'cmake_example.cp310-win_amd64.pyd'}, None, False, True)


```