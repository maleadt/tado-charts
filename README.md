tado charts
-----------

This repo contains scripts to chart data from tado hardware. See [this example
chart](res/example.png).

NOTE: this software is not official, and makes use of (currently) undocumented APIs.


## Installation

Python 3.0 (See [`requirements.txt`](requirements.txt) for the required packages).

For example, using `pip` and a `virtualenv` (after having cloned this repo to `tado-charts`):

```
$ virtualenv --python=python3 env
$ . env/bin/activate
$ pip install -r tado-charts/requirements.txt
```

Note that you need to activate the virtual environment every time you want to use it, or
explicitly use one of the `python` binaries in the `bin` subfolder.


## Usage

- create `private.py` with information about your set-up (see
  [`private.py.sample`](private.py.sample) for an example)
- run `collect.py` every minute or so to gather information for each zone
- run `plot.py` to generate a chart for today's state of each zone
