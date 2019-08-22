import unittest
from varlink import mock
import varlink

import podman
from podman.libs.pods import Pod


pod_id_1 = "135d71b9495f7c3967f536edad57750bfdb569336cd107d8aabab45565ffcfb6"
short_pod_id_1 = "135d71b9495f"
pod_id_2 = "49a5cce72093a5ca47c6de86f10ad7bb36391e2d89cef765f807e460865a0ec6"
short_pod_id_2 = "49a5cce72093"
pods = {
    short_pod_id_1: pod_id_1,
    short_pod_id_2: pod_id_2,
}

types = """
type ListPodData (
    id: string,
    name: string,
    createdat: string,
    cgroup: string,
    status: string,
    labels: [string]string,
    numberofcontainers: string,
    containersinfo: []ListPodContainerInfo
)

type ListPodContainerInfo (
    name: string,
    id: string,
    status: string
)
"""


class ServicePod():

    def StartPod(self, name: str) -> str:
        """return pod"""
        return {
            "pod": "135d71b9495f7c3967f536edad57750bfdb569336cd107d8aabab45565ffcfb6"
        }

    def GetPod(self, name: str) -> str:
        """return pod: ListPodData"""
        return  {
            "pod": {
                "cgroup": "machine.slice",
                "containersinfo": [
                  {
                    "id": "1840835294cf076a822e4e12ba4152411f131bd869e7f6a4e8b16df9b0ea5c7f",
                    "name": "1840835294cf-infra",
                    "status": "running"
                  },
                  {
                    "id": "49a5cce72093a5ca47c6de86f10ad7bb36391e2d89cef765f807e460865a0ec6",
                    "name": "upbeat_murdock",
                    "status": "running"
                  }
                ],
                "createdat": "2018-12-07 13:10:15.014139258 -0600 CST",
                "id": "135d71b9495f7c3967f536edad57750bfdb569336cd107d8aabab45565ffcfb6",
                "name": "foobar",
                "numberofcontainers": "2",
                "status": "Running"
            }
        }

    def GetVersion(self) -> str:
        """return version"""
        return {"version": "testing"}


class TestPod(unittest.TestCase):

    @mock.mockedservice(
        fake_service=ServicePod,
        fake_types=types,
        name='io.podman',
        address='unix:@podmantests'
    )
    def test_start(self):
        client = podman.Client(uri="unix:@podmantests")
        pod = Pod(client._client, short_pod_id_1, {"foo": "bar"})
        self.assertEqual(pod.start()["numberofcontainers"], "2")
