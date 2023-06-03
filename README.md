# dae-equiv-judge
This is a Python3 implementation of the paper, "**Simple Algorithm for Judging Equivalence of Differential-Algebraic Equation Systems**".


## System requirements

* Python 3 (3.10 or later)
* sympy==1.7.1
* antlr4-python3-runtime==4.7

## Installation

The dependencies related to python library will be installed with one shot using [Poetry](https://github.com/python-poetry/poetry):

```shell
poetry install
```

You can also use `requirements.txt`.
```shell
python -m pip install -r requirements.txt
```


## Usage
### Run equivalence judgment in all cases:
```shell
python test_all.py
```

### Run equivalence judgment in one case
```shell
python test_one_case.py
```

### Prepare the input data
You can also use your own file to perform the synonymity determination.

Note that in the input latex file, **each equation that make up an equation group must be contained in a single line**.

It does not work well when a single equation spans multiple lines or when a single line contains multiple equations, because such cases are not expected.

## License
Copyright 2023 Shota KATO

This software is licenced under [the MIT License](./LICENSE)

---

Shota KATO