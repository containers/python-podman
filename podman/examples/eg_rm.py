#!/usr/bin/env python3
"""Example: Remove containers by name."""

import podman

print('{}\n'.format(__doc__))

with podman.Client() as client:
    image = client.image.get('alpine:latest')
    for _ in range(1000):
        ctnr = image.container()
        ctnr.start()
        ctnrs = client.containers.list()
        ctnr.remove()
        ctnrs = client.containers.list()
        ctnr.remove(force=True)
        ctnrs = client.containers.list()
