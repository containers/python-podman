"""Model for accessing details of Pods from podman service."""
import collections
import json
import signal
import time

from . import ConfigDict, FoldedString, fold_keys


class Pod(collections.UserDict):
    """Model for a Pod."""

    def __init__(self, client, ident, data):
        """Construct Pod model."""
        super().__init__(data)

        self._ident = ident
        self._client = client

        with client() as podman:
            self._refresh(podman)

    def _refresh(self, podman):
        pod = podman.GetPod(self._ident)
        super().update(pod['pod'])

        for k, v in self.data.items():
            setattr(self, k, v)
        return self

    def inspect(self):
        """Retrieve details about pod."""
        with self._client() as podman:
            results = podman.InspectPod(self._ident)
        obj = json.loads(results['pod'], object_hook=fold_keys())
        obj['id'] = obj['config']['id']
        return collections.namedtuple('PodInspect', obj.keys())(**obj)

    def kill(self, signal_=signal.SIGTERM, wait=25):
        """Send signal to all containers in pod.

        default signal is signal.SIGTERM.
        wait n of seconds, 0 waits forever.
        """
        with self._client() as podman:
            podman.KillPod(self._ident, signal_)
            timeout = time.time() + wait
            while True:
                # pylint: disable=maybe-no-member
                self._refresh(podman)
                running = FoldedString(self.status)
                if running != 'running':
                    break

                if wait and timeout < time.time():
                    raise TimeoutError()

                time.sleep(0.5)
        return self

    def pause(self):
        """Pause all containers in the pod."""
        with self._client() as podman:
            podman.PausePod(self._ident)
            return self._refresh(podman)

    def refresh(self):
        """Refresh status fields for this pod."""
        with self._client() as podman:
            return self._refresh(podman)

    def remove(self, force=False):
        """Remove pod and its containers returning pod ident.

        force=True, stop any running container.
        """
        with self._client() as podman:
            results = podman.RemovePod(self._ident, force)
        return results['pod']

    def restart(self):
        """Restart all containers in the pod."""
        with self._client() as podman:
            podman.RestartPod(self._ident)
            return self._refresh(podman)

    def stats(self):
        """Stats on all containers in the pod."""
        with self._client() as podman:
            results = podman.GetPodStats(self._ident)
        for obj in results['containers']:
            yield collections.namedtuple('ContainerStats', obj.keys())(**obj)

    def start(self):
        """Start all containers in the pod."""
        with self._client() as podman:
            podman.StartPod(self._ident)
            return self._refresh(podman)

    def stop(self):
        """Stop all containers in the pod."""
        with self._client() as podman:
            podman.StopPod(self._ident)
            return self._refresh(podman)

    def top(self):
        """Display stats for all containers."""
        with self._client() as podman:
            results = podman.TopPod(self._ident)
        return results['pod']

    def unpause(self):
        """Unpause all containers in the pod."""
        with self._client() as podman:
            podman.UnpausePod(self._ident)
            return self._refresh(podman)

    def generate_kub(self, service=True):
        """Generates a Kubernetes v1 Pod description of a Podman container"""
        with self._client() as podman:
            results = podman.GenerateKube(self._ident, service)
        return results['pod']

    def state_data(self):
        """Returns the container's state config in string form."""
        with self._client() as podman:
            results = podman.PodStateData(self._id)
        return results['config']


class Pods():
    """Model for accessing pods."""

    def __init__(self, client):
        """Construct pod model."""
        self._client = client

    def create(self,
               ident=None,
               cgroupparent=None,
               labels=None,
               share=None,
               infra=False):
        """Create a new empty pod."""
        config = ConfigDict(
            name=ident,
            cgroupParent=cgroupparent,
            labels=labels,
            share=share,
            infra=infra,
        )

        with self._client() as podman:
            result = podman.CreatePod(config)
            details = podman.GetPod(result['pod'])
        return Pod(self._client, result['pod'], details['pod'])

    def get(self, ident):
        """Get Pod from ident."""
        with self._client() as podman:
            result = podman.GetPod(ident)
        return Pod(self._client, result['pod']['id'], result['pod'])

    def list(self):
        """List all pods."""
        with self._client() as podman:
            results = podman.ListPods()
        for pod in results['pods']:
            yield Pod(self._client, pod['id'], pod)

    def get_by_status(self, statuses):
        """Get pods by statuses"""
        with self._client() as podman:
            results = podman.GetPodsByStatus(statuses)
        return results['containers']

    def get_by_context(self, all=True, latest=False, args=[]):
        """Get pods ids or names depending on all, latest, or a list of
        pods names"""
        with self._client() as podman:
            results = podman.GetPodsByContext(all, latest, args)
        for pod in results['pods']:
            yield Pod(self._client, pod['id'], pod)
