"""Base for podman tests."""
import contextlib
import functools
import itertools
import logging
import os
import subprocess
import time
import unittest
from os import getenv

from varlink import VarlinkError

MethodNotImplemented = "org.varlink.service.MethodNotImplemented"


class LogTestCase(type):
    """LogTestCase wires in a logger handler to handle logging during tests."""

    def __new__(cls, name, bases, dct):
        setup = dct["setUp"] if "setUp" in dct else lambda self: None

        def wrapped_setUp(self):
            self.hdlr = logging.StreamHandler(sys.stdout)
            self.logger.addHandler(self.hdlr)

        dct["setUp"] = wrapped_setUp

        tearDown = dct["tearDown"] if "tearDown" in dct else lambda self: None

        def wrapped_tearDown(self):
            tearDown(self)
            self.logger.removeHandler(self.hdlr)

        dct["tearDown"] = wrapped_tearDown

        return type.__new__(cls, name, bases, dct)


class PodmanTestCase(unittest.TestCase):
    """Hide the sausage making of initializing storage."""

    __metaclass__ = LogTestCase
    logger = logging.getLogger("unittestLogger")
    level = os.environ.get("PODMAN_LOG_LEVEL")
    if level is not None:
        logger.setLevel(logging.getLevelName(level.upper()))

    @classmethod
    def setUpClass(cls):
        """Fixture to setup podman test case."""
        if hasattr(PodmanTestCase, "alpine_process"):
            PodmanTestCase.tearDownClass()

        def run_cmd(*args):
            cmd = list(itertools.chain(*args))
            try:
                pid = subprocess.Popen(
                    cmd,
                    close_fds=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                out, err = pid.communicate()
            except OSError as e:
                print("{}: {}({})".format(cmd, e.strerror, e.returncode))
            except ValueError as e:
                print("{}: {}".format(cmd, e.message))
                raise
            else:
                return out.strip()

        tmpdir = os.environ.get("TMPDIR", "/tmp")
        podman_args = [
            "--storage-driver=vfs",
            "--cgroup-manager=cgroupfs",
            "--root={}/crio".format(tmpdir),
            "--runroot={}/crio-run".format(tmpdir),
            "--cni-config-dir={}/cni/net.d".format(tmpdir),
        ]

        run_podman = functools.partial(run_cmd, ["podman"], podman_args)

        id = run_podman(["pull", "alpine"])
        setattr(PodmanTestCase, "alpine_id", id)

        run_podman(["pull", "busybox"])
        run_podman(["images"])

        run_cmd(["rm", "-f", "{}/alpine_gold.tar".format(tmpdir)])
        run_podman(
            ["save", "--output", "{}/alpine_gold.tar".format(tmpdir), "alpine"]
        )

        PodmanTestCase.alpine_log = open(
            os.path.join("/tmp/", "alpine.log"), "w"
        )

        cmd = ["podman"]
        cmd.extend(podman_args)
        # cmd.extend(['run', '-d', 'alpine', 'sleep', '500'])
        cmd.extend(["run", "-dt", "alpine", "/bin/sh"])
        PodmanTestCase.alpine_process = subprocess.Popen(
            cmd, stdout=PodmanTestCase.alpine_log, stderr=subprocess.STDOUT
        )

        PodmanTestCase.busybox_log = open(
            os.path.join("/tmp/", "busybox.log"), "w"
        )

        cmd = ["podman"]
        cmd.extend(podman_args)
        cmd.extend(["create", "busybox"])
        PodmanTestCase.busybox_process = subprocess.Popen(
            cmd, stdout=PodmanTestCase.busybox_log, stderr=subprocess.STDOUT
        )
        # give podman time to start ctnr
        time.sleep(2)

        # Close our handle of file
        PodmanTestCase.alpine_log.close()
        PodmanTestCase.busybox_log.close()

    @classmethod
    def tearDownClass(cls):
        """Fixture to clean up after podman unittest."""
        try:
            PodmanTestCase.alpine_process.kill()
            assert 0 == PodmanTestCase.alpine_process.wait(500)
            delattr(PodmanTestCase, "alpine_process")

            PodmanTestCase.busybox_process.kill()
            assert 0 == PodmanTestCase.busybox_process.wait(500)
        except Exception as e:
            print("Exception: {}".format(e))
            raise

    @contextlib.contextmanager
    def assertRaisesNotImplemented(self):
        """Sugar for unimplemented varlink methods."""
        with self.assertRaisesRegex(VarlinkError, MethodNotImplemented):
            yield
