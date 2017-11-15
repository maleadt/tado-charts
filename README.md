tado charts
-----------

This repo contains scripts to chart data from tado hardware. See [this example
chart](res/example.png).

NOTE: this software is not official, and makes use of (currently) undocumented APIs.


## Set-up and usage

### With Docker

1. create `bin/private.py` from
   [`bin/private.py.sample`](bin/private.py.sample), ignoring the database
   variables (these are provisioned differently with Docker)
2. run `docker-compose up`

By default, data is collected every minute and plots are generated in the
`output` folder every five minutes (see [`crontab`](crontab)), with default
database settings provided by [`db.env`](db.env).

**NOTE**: after an update, or when modifying files like `private.py`, first run
`docker-compose build` to rebuild the image and include the modified files
before starting the container again.


### Manual

Set-up:
1. install `python3` as well as all required packages as listed in
   [`requirements.txt`](requirements.txt). Use a virtual environment for
   convenience:

    ```
    $ virtualenv --python=python3 env
    $ . env/bin/activate
    $ pip install -r $THIS_REPO/requirements.txt
    ```
2. install and configure MySQL, creating a user and granting it permissions on a
   database.
3. create `bin/private.py` from
   [`bin/private.py.sample`](bin/private.py.sample).

Usage:
- activate the virtual environment with `. env/bin/activate` or use the `python`
  binary from the `bin` subfolder of the environment.
- run `collect.py` every minute or so to gather information for each zone
- run `plot.py` to generate a chart for today's state of each zone
