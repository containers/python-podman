"""Models for accessing details from varlink server."""
import collections

import pkg_resources

from . import cached_property


class System():
    """Model for accessing system resources."""

    def __init__(self, client):
        """Construct system model."""
        self._client = client

    @cached_property
    def versions(self):
        """Access versions."""
        with self._client() as podman:
            vers = podman.GetVersion()

        client = '0.0.0'
        try:
            client = pkg_resources.get_distribution('podman').version
        except Exception:  # pylint: disable=broad-except
            pass
        vers['client_version'] = client
        return collections.namedtuple('Version', vers.keys())(**vers)

    def info(self):
        """Return podman info."""
        with self._client() as podman:
            info = podman.GetInfo()['info']
        return collections.namedtuple('Info', info.keys())(**info)

    def ping(self):
        """Return True if server awake."""
        with self._client() as podman:
            response = podman.GetVersion()
        return 'version' in response

    def receive_file(self, path, delete=True):
        """Allows the host to send a remote client a file."""
        with self._client() as podman:
            response = podman.ReceiveFile(path, delete)
        return response['len']

    def get_events(self, filters=[], since=None, until=None):
        """Returns known libpod events filtered by the options provided."""
        with self._client() as podman:
            response = podman.GetEvent(filters, since, until)
        return response['events']
