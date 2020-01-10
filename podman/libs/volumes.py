"""Models for manipulating containers and storage."""


class Volumes():
    """Model for Volumes collection."""

    def __init__(self, client):
        """Construct model for Volume collection."""
        self._client = client

    def create(self, options):
        """Creates a volume on a remote host."""
        with self._client() as podman:
            results = podman.VolumeCreate(options)
        return results['volumeName']

    def remove(self, options):
        """Remove a volume on a remote host."""
        with self._client() as podman:
            results = podman.VolumeRemove(options)
        return results['successes'], results['failures']

    def get(self, args, all=True):
        """Gets slice of the volumes on a remote host."""
        with self._client() as podman:
            results = podman.GetVolumes(args, all)
        return results['volumes']

    def prunes(self):
        """Removes unused volumes on the host."""
        with self._client() as podman:
            results = podman.VolumesPrune()
        return results['prunedNames'], results['prunedErrors']
