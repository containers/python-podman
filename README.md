# podman - pythonic library for working with varlink interface to Podman

[![Build Status](https://travis-ci.org/containers/python-podman.svg?branch=master)](https://travis-ci.org/containers/python-podman)
![PyPI](https://img.shields.io/pypi/v/podman.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/podman.svg)
![PyPI - Status](https://img.shields.io/pypi/status/podman.svg)

## Status: Active Development

See [libpod](https://github.com/containers/python-podman)

## Overview

Python podman library.

Provide a stable API to call into.

## Releases

### Requirements

* Python 3.5+
* OpenSSH 6.7+
* Python dependencies in requirements.txt

### Install

#### From pypi

Install `python-podman` to the standard location for third-party
Python modules:

```sh
python3 -m pip install podman
```

To use this method on Unix/Linux system you need to have permission to write
to the standard third-party module directory.

Else, you can install the latest version of python-podman published on
pypi to the Python user install directory for your platform.
Typically ~/.local/. ([See the Python documentation for site.USER_BASE for full
details.](https://pip.pypa.io/en/stable/user_guide/#user-installs))
You can install like this by using the `--user` option:

```sh
python3 -m pip install --user podman
```

This method can be useful in many situations, for example,
on a Unix system you might not have permission to write to the
standard third-party module directory. Or you might wish to try out a module
before making it a standard part of your local Python installation.
This is especially true when upgrading a distribution already present: you want
to make sure your existing base of scripts still works with the new version
before actually upgrading.

For further reading about how python installation works [you can read
this documentation](https://docs.python.org/3/install/index.html#how-installation-works).

#### By building from source

To build the podman egg and install as user:

```sh
cd ~/python-podman
python3 setup.py clean -a && python3 setup.py sdist bdist
python3 setup.py install --user
```

## Code snippets/examples:

### Show images in storage

```python
import podman

with podman.Client() as client:
  list(map(print, client.images.list()))
```

### Show containers created since midnight

```python
from datetime import datetime, time, timezone

import podman

midnight = datetime.combine(datetime.today(), time.min, tzinfo=timezone.utc)

with podman.Client() as client:
    for c in client.containers.list():
        created_at = podman.datetime_parse(c.createdat)

        if created_at > midnight:
            print('Container {}: image: {} created at: {}'.format(
                c.id[:12], c.image[:32], podman.datetime_format(created_at)))
```
