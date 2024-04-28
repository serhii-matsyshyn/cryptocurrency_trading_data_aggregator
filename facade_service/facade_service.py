import logging
import random

import hazelcast
import requests


logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FacadeService:
    def __init__(self, consul):
        self.consul = consul

        # self.client = hazelcast.HazelcastClient(cluster_name='dev') # cluster_name=consul.get_config("hazelcast/settings/cluster_name"))
        # self.distributed_queue = self.client.get_queue(consul.get_config("hazelcast/settings/queue_name")).blocking()

    # @property
    # def logging_services(self):
    #     url = [f"http://{i}:{j}" for i, j in self.consul.get_service_addresses("logging_service")]
    #     logger.info(f"logging_services - from CONSUL - {url}")
    #     return url

    def get_precomputed_report_data(self, report_name: str, params: dict):
        precomputed_report_service_url = "http://localhost:8002"
        response = requests.get(f"{precomputed_report_service_url}/{report_name}", params=params)
        response.raise_for_status()
        logger.debug("Get precomputed report data successful!")
        logger.debug(response.json())
        return response.json()

    def __del__(self):
        self.consul.deregister_service()
