"""A client for communicating with a Podman server."""

from pbr.version import VersionInfo

from .client import Client
from .libs import FoldedString, datetime_format, datetime_parse
from .libs.errors import (ContainerNotFound, ErrorOccurred, ImageNotFound,
                          InvalidState, NoContainerRunning, NoContainersInPod,
                          PodContainerError, PodmanError, PodNotFound)

assert FoldedString

try:
    __version__ = VersionInfo("podman")
except Exception:  # pylint: disable=broad-except
    __version__ = '0.0.0'

__all__ = [
    'Client',
    'ContainerNotFound',
    'datetime_format',
    'datetime_parse',
    'ErrorOccurred',
    'ImageNotFound',
    'InvalidState',
    'NoContainerRunning',
    'NoContainersInPod',
    'PodContainerError',
    'PodmanError',
    'PodNotFound',
]
