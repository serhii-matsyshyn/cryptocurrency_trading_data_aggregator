import logging
from datetime import datetime, timedelta

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

    def sum_trades_last_n_minutes(self, symbol, n_minutes):
        end_timestamp = datetime.utcnow().replace(second=0, microsecond=0)
        start_timestamp = end_timestamp - timedelta(minutes=n_minutes)

        query = f"""
            SELECT SUM(trades) AS total_trades
            FROM tradeBin1m
            WHERE symbol = '{symbol}'
            AND timestamp >= '{start_timestamp.strftime('%Y-%m-%d %H:%M:%S')}'
            AND timestamp < '{end_timestamp.strftime('%Y-%m-%d %H:%M:%S')}'
            ALLOW FILTERING
        """

        result = self.session.execute(query)
        total_trades = 0
        if result:
            total_trades = result.one().total_trades
        return {
            'symbol': symbol,
            'total_trades': total_trades,
            'start_timestamp': start_timestamp,
            'end_timestamp': end_timestamp
        }

    def top_n_cryptos_last_hour(self, n, volume_type='foreignNotional'):
        end_timestamp = datetime.utcnow().replace(second=0, microsecond=0)
        start_timestamp = end_timestamp - timedelta(hours=1)

        query = f"""
            SELECT symbol, SUM({volume_type}) AS total_volume
            FROM tradeBin1m
            WHERE timestamp >= '{start_timestamp.strftime('%Y-%m-%d %H:%M:%S')}'
            AND timestamp < '{end_timestamp.strftime('%Y-%m-%d %H:%M:%S')}'
            GROUP BY symbol
            ALLOW FILTERING
        """

        result = self.session.execute(query)

        top_cryptos = []
        for row in result:
            top_cryptos.append((row.symbol, row.total_volume))

        top_cryptos = sorted(top_cryptos, key=lambda x: x[1], reverse=True)[:n]

        return {
            'top_cryptos': {symbol: total_volume for symbol, total_volume in top_cryptos},
            'volume_type': volume_type,
            'start_timestamp': start_timestamp,
            'end_timestamp': end_timestamp
        }


if __name__ == '__main__':
    from consul_service_registry import ConsulServiceRegistry

    consul = ConsulServiceRegistry()
    precomputed_report_data_retrieve_repository = LiveDataRetrieveRepository(consul=consul)

    print(precomputed_report_data_retrieve_repository.get_latest_prices('XBTUSD'))
    print(precomputed_report_data_retrieve_repository.sum_trades_last_n_minutes('XBTUSD', 5))
    print(precomputed_report_data_retrieve_repository.top_n_cryptos_last_hour(5))
