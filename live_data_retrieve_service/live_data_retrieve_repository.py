import json
import logging
import datetime
from datetime import timedelta

import hazelcast
from cassandra.policies import DCAwareRoundRobinPolicy, HostDistance
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Cassandra connection details
CASSANDRA_CONTACT_POINTS = ['localhost']
CASSANDRA_USERNAME = 'cassandra'
CASSANDRA_PASSWORD = 'cassandra'


class LiveDataRetrieveRepository:
    def __init__(self, consul, cassandra_keyspace='crypto_project'):
        self.consul = consul

        self.cassandra_keyspace = cassandra_keyspace

        self.auth_provider = PlainTextAuthProvider(username=CASSANDRA_USERNAME, password=CASSANDRA_PASSWORD)
        self.cluster = Cluster(contact_points=CASSANDRA_CONTACT_POINTS, auth_provider=self.auth_provider,
                               load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1'),
                               protocol_version=3)
        self.session = self.cluster.connect(keyspace=self.cassandra_keyspace)

        self.client = hazelcast.HazelcastClient(
            cluster_name='dev')  # cluster_name=consul.get_config("hazelcast/settings/cluster_name"))

        self.hz_sum_trades_last_n_minutes_map = self.client.get_map("sum_trades_last_n_minutes").blocking()
        self.hz_top_n_cryptos_last_hour_map = self.client.get_map("top_n_cryptos_last_hour").blocking()

    def get_latest_prices(self, symbol):
        query = f"""
            SELECT bidPrice, askPrice, timestamp
            FROM quote
            WHERE symbol = '{symbol}'
            ORDER BY timestamp DESC
            LIMIT 1
        """

        result = self.session.execute(query)
        if result:
            result_value = result.one()
            return {
                'symbol': symbol,
                'bidPrice': result_value.bidprice,
                'askPrice': result_value.askprice,
                'timestamp': result_value.timestamp
            }
        return {'symbol': symbol, 'bidPrice': 'N/A', 'askPrice': 'N/A', 'timestamp': 'N/A'}

    @staticmethod
    def default(o):
        """Default JSON serializer for dates and datetimes."""
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()

    def check_and_get_if_cached(self, name, start_timestamp, end_timestamp, symbol, n, volume_type=None):
        if name == 'sum_trades_last_n_minutes':
            logger.debug(f"Checking cache for {symbol}_{n}_{start_timestamp}_{end_timestamp}")
            result = self.hz_sum_trades_last_n_minutes_map.get(f"{symbol}_{n}_{start_timestamp}_{end_timestamp}")
        elif name == 'top_n_cryptos_last_hour':
            logger.debug(f"Checking cache for {n}_{start_timestamp}_{end_timestamp}_{volume_type}")
            result = self.hz_top_n_cryptos_last_hour_map.get(f"{n}_{start_timestamp}_{end_timestamp}_{volume_type}")
        else:
            raise ValueError(f"Invalid name for check_and_get_if_cached: {name}")

        logger.debug(f"Cache result loaded from Hazelcast: {result}")
        return json.loads(result) if result else None

    def cache_result(self, name, start_timestamp, end_timestamp, symbol, n, result, volume_type=None):
        if name == 'sum_trades_last_n_minutes':
            logger.debug(f"Caching {symbol}_{n}_{start_timestamp}_{end_timestamp}")
            self.hz_sum_trades_last_n_minutes_map.put(
                f"{symbol}_{n}_{start_timestamp}_{end_timestamp}",
                json.dumps(result, default=self.default)
            )
        elif name == 'top_n_cryptos_last_hour':
            logger.debug(f"Caching {n}_{start_timestamp}_{end_timestamp}_{volume_type}")
            self.hz_top_n_cryptos_last_hour_map.put(
                f"{n}_{start_timestamp}_{end_timestamp}_{volume_type}",
                json.dumps(result, default=self.default)
            )
        else:
            raise ValueError(f"Invalid name for cache_result: {name}")

    def sum_trades_last_n_minutes(self, symbol, n_minutes):
        end_timestamp = datetime.datetime.utcnow().replace(second=0, microsecond=0)
        start_timestamp = end_timestamp - timedelta(minutes=n_minutes)

        if cached_result := self.check_and_get_if_cached(
                'sum_trades_last_n_minutes',
                start_timestamp,
                end_timestamp,
                symbol, n_minutes):
            logger.info(f"Returning cached result for {symbol} from {start_timestamp} to {end_timestamp}")
            return cached_result

        query = f"""
            SELECT SUM(trades) AS total_trades
            FROM tradeBin1m
            WHERE symbol = '{symbol}'
            AND timestamp >= '{start_timestamp.strftime('%Y-%m-%d %H:%M:%S')}'
            AND timestamp < '{end_timestamp.strftime('%Y-%m-%d %H:%M:%S')}'
            ALLOW FILTERING
        """

        query_result = self.session.execute(query)
        total_trades = 0
        if query_result:
            total_trades = query_result.one().total_trades
        result = {
            'symbol': symbol,
            'total_trades': total_trades,
            'start_timestamp': start_timestamp,
            'end_timestamp': end_timestamp
        }

        self.cache_result('sum_trades_last_n_minutes', start_timestamp, end_timestamp, symbol, n_minutes, result=result)
        return result

    def top_n_cryptos_last_hour(self, n, volume_type='foreignNotional'):
        end_timestamp = datetime.datetime.utcnow().replace(second=0, microsecond=0)
        start_timestamp = end_timestamp - timedelta(hours=1)

        if cached_result := self.check_and_get_if_cached(
                'top_n_cryptos_last_hour',
                start_timestamp,
                end_timestamp,
                None, n, volume_type):
            logger.info(f"Returning cached result for top {n} cryptos from {start_timestamp} to {end_timestamp}")
            return cached_result

        query = f"""
            SELECT symbol, SUM({volume_type}) AS total_volume
            FROM tradeBin1m
            WHERE timestamp >= '{start_timestamp.strftime('%Y-%m-%d %H:%M:%S')}'
            AND timestamp < '{end_timestamp.strftime('%Y-%m-%d %H:%M:%S')}'
            GROUP BY symbol
            ALLOW FILTERING
        """

        query_result = self.session.execute(query)

        top_cryptos = []
        for row in query_result:
            top_cryptos.append((row.symbol, row.total_volume))

        top_cryptos = sorted(top_cryptos, key=lambda x: x[1], reverse=True)[:n]

        result = {
            'top_cryptos': {symbol: total_volume for symbol, total_volume in top_cryptos},
            'volume_type': volume_type,
            'start_timestamp': start_timestamp,
            'end_timestamp': end_timestamp
        }

        self.cache_result('top_n_cryptos_last_hour', start_timestamp, end_timestamp, None, n, result=result, volume_type=volume_type)
        return result


if __name__ == '__main__':
    from consul_service_registry import ConsulServiceRegistry

    consul = ConsulServiceRegistry()
    precomputed_report_data_retrieve_repository = LiveDataRetrieveRepository(consul=consul)

    print(precomputed_report_data_retrieve_repository.get_latest_prices('XBTUSD'))
    print(precomputed_report_data_retrieve_repository.sum_trades_last_n_minutes('XBTUSD', 5))
    print(precomputed_report_data_retrieve_repository.top_n_cryptos_last_hour(5))
