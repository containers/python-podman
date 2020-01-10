"""Models for manipulating containers and storage."""
import collections
import getpass
import json
import logging
import signal
import time

from . import fold_keys
from ._containers_attach import Mixin as AttachMixin
from ._containers_start import Mixin as StartMixin


class Container(AttachMixin, StartMixin, collections.UserDict):
    """Model for a container."""

    def __init__(self, client, ident, data, refresh=True):
        """Construct Container Model."""
        super(Container, self).__init__(data)
        self._client = client
        self._id = ident

        if refresh:
            with client() as podman:
                self._refresh(podman)
        else:
            for k, v in self.data.items():
                setattr(self, k, v)
            if 'containerrunning' in self.data:
                setattr(self, 'running', self.data['containerrunning'])
                self.data['running'] = self.data['containerrunning']

        assert self._id == data['id'],\
            'Requested container id({}) does not match store id({})'.format(
                self._id, data['id']
            )

    def _refresh(self, podman, tries=1):
        try:
            ctnr = podman.GetContainer(self._id)
        except BrokenPipeError:
            logging.debug('Failed GetContainer(%s) try %d/3', self._id, tries)
            if tries > 3:
                raise
            else:
                with self._client() as pman:
                    self._refresh(pman, tries + 1)
        else:
            super().update(ctnr['container'])

            for k, v in self.data.items():
                setattr(self, k, v)
            if 'containerrunning' in self.data:
                setattr(self, 'running', self.data['containerrunning'])
                self.data['running'] = self.data['containerrunning']

            return self

    def refresh(self):
        """Refresh status fields for this container."""
        with self._client() as podman:
            return self._refresh(podman)

    def processes(self):
        """Show processes running in container."""
        with self._client() as podman:
            results = podman.ListContainerProcesses(self._id)
        yield from results['container']

    def changes(self):
        """Retrieve container changes."""
        with self._client() as podman:
            results = podman.ListContainerChanges(self._id)
        return results['container']

    def kill(self, sig=signal.SIGTERM, wait=25):
        """Send signal to container.

        default signal is signal.SIGTERM.
        wait n of seconds, 0 waits forever.
        """
        with self._client() as podman:
            podman.KillContainer(self._id, sig)
            timeout = time.time() + wait
            while True:
                self._refresh(podman)
                if self.status != 'running':  # pylint: disable=no-member
                    return self

                if wait and timeout < time.time():
                    raise TimeoutError()

                time.sleep(0.5)

    def inspect(self):
        """Retrieve details about containers."""
        with self._client() as podman:
            results = podman.InspectContainer(self._id)
        obj = json.loads(results['container'], object_hook=fold_keys())
        return collections.namedtuple('ContainerInspect', obj.keys())(**obj)

    def export(self, target):
        """Export container from store to tarball.

        TODO: should there be a compress option, like images?
        """
        with self._client() as podman:
            results = podman.ExportContainer(self._id, target)
        return results['tarfile']

    def commit(self, image_name, **kwargs):
        """Create image from container.

        Keyword arguments:
            author -- change image's author
            message -- change image's message, docker format only.
            pause -- pause container during commit
            change -- Additional properties to change

        Change examples:
            CMD=/usr/bin/zsh
            ENTRYPOINT=/bin/sh date
            ENV=TEST=test_containers.TestContainers.test_commit
            EXPOSE=8888/tcp
            LABEL=unittest=test_commit
            USER=bozo:circus
            VOLUME=/data
            WORKDIR=/data/application

        All changes overwrite existing values.
          See inspect() to obtain current settings.
        """
        author = kwargs.get('author', None) or getpass.getuser()
        change = kwargs.get('change', None) or []
        message = kwargs.get('message', None) or ''
        pause = kwargs.get('pause', None) or True

        for c in change:
            if c.startswith('LABEL=') and c.count('=') < 2:
                raise ValueError(
                    'LABEL should have the format: LABEL=label=value, not {}'.
                    format(c))

        with self._client() as podman:
            results = podman.Commit(self._id, image_name, change, author,
                                    message, pause)
        return results['reply']['id']

    def stop(self, timeout=25):
        """Stop container, return id on success."""
        with self._client() as podman:
            podman.StopContainer(self._id, timeout)
            return self._refresh(podman)

    def remove(self, force=False):
        """Remove container, return id on success.

        force=True, stop running container.
        """
        with self._client() as podman:
            results = podman.RemoveContainer(self._id, force)
        return results['container']

    def restart(self, timeout=25):
        """Restart container with timeout, return id on success."""
        with self._client() as podman:
            podman.RestartContainer(self._id, timeout)
            return self._refresh(podman)

    def pause(self):
        """Pause container, return id on success."""
        with self._client() as podman:
            podman.PauseContainer(self._id)
            return self._refresh(podman)

    def unpause(self):
        """Unpause container, return id on success."""
        with self._client() as podman:
            podman.UnpauseContainer(self._id)
            return self._refresh(podman)

    def update_container(self, *args, **kwargs):  \
            # pylint: disable=unused-argument
        """TODO: Update container..., return id on success."""
        with self._client() as podman:
            podman.UpdateContainer()
            return self._refresh(podman)

    def wait(self):
        """Wait for container to finish, return 'returncode'."""
        with self._client() as podman:
            results = podman.WaitContainer(self._id)
        return int(results['exitcode'])

    def stats(self):
        """Retrieve resource stats from the container."""
        with self._client() as podman:
            results = podman.GetContainerStats(self._id)
        obj = results['container']
        return collections.namedtuple('StatDetail', obj.keys())(**obj)

    def logs(self, *args, **kwargs):  # pylint: disable=unused-argument
        """Retrieve container logs."""
        with self._client() as podman:
            results = podman.GetContainerLogs(self._id)
        yield from results['container']

    def health_check_run(self):
        """Executes defined container's healthcheck command
        and returns the container's health status.."""
        with self._client() as podman:
            result = podman.HealthCheckRun(self._id)
        yield result['healthCheckStatus']

    def get_stats_with_history(self, previous_stats):
        """Takes a previous set of container statistics and uses
        libpod functions to calculate the containers statistics based on
        current and previous measurements."""
        with self._client() as podman:
            results = podman.GetContainerStatsWithHistory(previous_stats)
        return results['container']

    def init(self):
        """Initializes the container."""
        with self._client() as podman:
            results = podman.InitContainer(self._id)
        return results['container']

    def attach_control(self):
        """Sets up the ability to remotely attach to the container console."""
        with self._client() as podman:
            podman.AttachControl(self._id)

    def checkpoint(self, keep=True, leaveRunning=True, tcpEstablished=True):
        """performs a checkpopint on the container."""
        with self._client() as podman:
            results = podman.ContainerCheckpoint(
                self._id,
                keep,
                leaveRunning,
                tcpEstablished)
        return results['id']

    def restore(self, keep=True, tcpEstablished=True):
        """Restores a container that has been checkpointed."""
        with self._client() as podman:
            results = podman.ContainerRestore(
                self._id,
                keep,
                tcpEstablished)
        return results['id']

    def run_label(self, runlabel):
        """Executes a command as described by a given container image label."""
        with self._client() as podman:
            podman.ContainerRunlabel(runlabel)

    def exec(self, opts):
        """Executes a command in the container."""
        with self._client() as podman:
            podman.ExecContainer(opts)

    def mount(self):
        """Mounts the container."""
        with self._client() as podman:
            results = podman.MountContainer(self._id)
        return results['path']

    def umount(self, force=False):
        """Mounts the container."""
        with self._client() as podman:
            podman.UnmountContainer(self._id, force)

    def config(self):
        """Returns container's config in string form."""
        with self._client() as podman:
            results = podman.ContainerConfig(self._id)
        return results['config']

    def artifacts(self, artifactName):
        """Returns the container's artifacts in string form."""
        with self._client() as podman:
            results = podman.ContainerArtifacts(self._id, artifactName)
        return results['config']

    def inspect_data(self, size=True):
        """Returns the container's inspect data in string form."""
        with self._client() as podman:
            results = podman.ContainerInspectData(self._id, size)
        return results['config']

    def state_data(self):
        """Returns the container's state config in string form."""
        with self._client() as podman:
            results = podman.ContainerStateData(self._id)
        return results['config']


class Containers():
    """Model for Containers collection."""

    def __init__(self, client):
        """Construct model for Containers collection."""
        self._client = client

    def list(self):
        """List of containers in the container store."""
        with self._client() as podman:
            results = podman.ListContainers()
        for cntr in results['containers']:
            yield Container(self._client, cntr['id'], cntr, refresh=False)

    def delete_stopped(self):
        """Delete all stopped containers."""
        with self._client() as podman:
            results = podman.DeleteStoppedContainers()
        return results['containers']

    def get(self, id_):
        """Retrieve container details from store."""
        with self._client() as podman:
            cntr = podman.GetContainer(id_)
        return Container(self._client, cntr['container']['id'],
                         cntr['container'])

    def get_by_status(self, status):
        """Get containers by status"""
        with self._client() as podman:
            results = podman.GetContainersByStatus(status)
        for cntr in results['containers']:
            yield Container(self._client, cntr['id'], cntr, refresh=False)

    def get_by_context(self, all=True, latest=False, args=[]):
        """Get containers ids or names depending on all, latest, or a list of
        container names"""
        with self._client() as podman:
            results = podman.GetContainersByContext(all, latest, args)
        for cntr in results['containers']:
            yield Container(self._client, cntr['id'], cntr, refresh=False)

    def logs(self,
             names,
             follow=True,
             latest=True,
             since="",
             tail=None,
             timestamps=True):
        """Get containers ids or names and returns the logs
        of these containers"""
        with self._client() as podman:
            results = podman.GetContainersLogs(
                names,
                follow,
                latest,
                since,
                tail,
                timestamps
            )
        return results['log']

    def exists(self, id_):
        """Returns a bool as to whether the container exists in
        local storage."""
        with self._client() as podman:
            exist = podman.ContainerExists(id_)
            if exist['exists'] == 0:
                return True
        return False

    def list_mounts(self):
        """gathers all the mounted container mount points and returns
        them as an array of strings."""
        with self._client() as podman:
            results = podman.ListContainerMounts()
        return results['mounts']
