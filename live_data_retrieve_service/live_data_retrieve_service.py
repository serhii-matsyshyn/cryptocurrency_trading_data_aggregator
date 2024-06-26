import datetime
import json
import logging
from threading import Thread

import hazelcast

from live_data_retrieve_repository import LiveDataRetrieveRepository


logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class LiveDataRetrieveService:
    def __init__(self, consul):
        self.consul = consul
        self.repository = LiveDataRetrieveRepository(consul)

        self.client = hazelcast.HazelcastClient(
            cluster_members=[consul.get_config("hazelcast/cluster_host")],
            cluster_name=consul.get_config("hazelcast/cluster_name")
        )

        self.distributed_queue = self.client.get_queue(consul.get_config("hazelcast/live_data_queue")).blocking()
        self.running = True

        self.consumer = Thread(target=self.consume_messages)
        self.consumer.start()

    def get_latest_prices(self, symbol):
        return self.repository.get_latest_prices(symbol)

    def sum_trades_last_n_minutes(self, symbol, n_minutes):
        return self.repository.sum_trades_last_n_minutes(symbol, n_minutes)

    def top_n_cryptos_last_hour(self, n, volume_type='foreignNotional'):
        return self.repository.top_n_cryptos_last_hour(n, volume_type)

    @staticmethod
    def default(o):
        """Default JSON serializer for dates and datetimes."""
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()

    def consume_messages(self):
        while self.running:
            data = self.distributed_queue.poll(3)
            if data:
                try:
                    json_data = json.loads(data)
                    logger.info(f"Consuming {json_data}")
                    if volume_type := json_data.get('volume_type'):
                        if volume_type not in ('homeNotional', 'foreignNotional', 'volume'):
                            raise ValueError(f"Invalid volume_type: {volume_type}")
                    if json_data['type'] == 'sum_trades_last_n_minutes':
                        result = self.sum_trades_last_n_minutes(json_data['symbol'], int(json_data['n_minutes']))
                        logger.info(f"Result: {result}")
                    elif json_data['type'] == 'top_n_cryptos_last_hour':
                        result = self.top_n_cryptos_last_hour(int(json_data['n']), json_data['volume_type'])
                        logger.info(f"Result: {result}")
                    elif json_data['type'] == 'get_latest_prices':
                        result = self.get_latest_prices(json_data['symbol'])
                        logger.info(f"Result: {result}")
                    else:
                        logger.error(f"Invalid message type '{json_data['type']}'")
                        result = {}
                    self.client.get_topic(json_data['topic']).publish(json.dumps(result, default=self.default))
                except Exception as e:
                    logger.error(f"Error consuming message: {e}")
                    try:
                        self.client.get_topic(json_data['topic']).publish(json.dumps({'error': str(e)}, default=self.default))
                    except:
                        pass

    def __del__(self):
        try:
            self.consul.deregister_service()
            self.running = False
            self.consumer.join()
        except Exception as e:
            logger.error(e)
