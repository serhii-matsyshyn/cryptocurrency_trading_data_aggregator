import json
import logging
import random
import threading
import time
import uuid

import hazelcast
import requests

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DataReceiver:
    def __init__(self, hazelcast_client):
        self.client = hazelcast_client
        self.received_message = None
        self.message_event = threading.Event()

        self.receive_topic_name = f"get_live_data_topic_{uuid.uuid4()}"
        self.topic = self.client.get_topic(self.receive_topic_name).blocking()
        self.topic.add_listener(self.message_listener)

    def message_listener(self, message):
        self.received_message = json.loads(message.message)
        self.message_event.set()

    def wait_for_message(self, timeout=60):
        self.message_event.wait(timeout)
        return self.received_message


class FacadeService:
    def __init__(self, consul):
        self.consul = consul

        self.client = hazelcast.HazelcastClient(cluster_name=consul.get_config("hazelcast/cluster_name"))
        self.distributed_queue = self.client.get_queue(consul.get_config("hazelcast/live_data_queue")).blocking()

    @property
    def get_precomputed_report_data_service(self):
        url = [f"http://{i}:{j}" for i, j in self.consul.get_service_addresses("precomputed_report_data_retrieve_service")]
        logger.info(f"precomputed_report_data_retrieve_service - from CONSUL - {url}")
        return url[0]

    def get_precomputed_report_data(self, report_name: str, params: dict):
        precomputed_report_service_url = self.get_precomputed_report_data_service
        response = requests.get(f"{precomputed_report_service_url}/{report_name}", params=params)
        response.raise_for_status()
        logger.debug("Get precomputed report data successful!")
        logger.debug(response.json())
        return response.json()

    def get_live_data(self, report_name: str, params: dict):
        data_receiver = DataReceiver(self.client)

        data = {
            'topic': data_receiver.receive_topic_name,
            'type': report_name,
            **params
        }
        self.distributed_queue.offer(json.dumps(data), timeout=5)

        return data_receiver.wait_for_message()

    def __del__(self):
        self.consul.deregister_service()
