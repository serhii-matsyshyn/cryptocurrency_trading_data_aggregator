import pandas as pd
from cassandra.policies import DCAwareRoundRobinPolicy, HostDistance
from cassandra.query import BatchStatement
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider


class WSLiveDataRetrieveRepository:
    def __init__(self, consul):
        self.auth_provider = PlainTextAuthProvider(username=consul.get_config("cassandra/credentials/username"),
                                                   password=consul.get_config("cassandra/credentials/password"))
        self.cluster = Cluster(contact_points=[consul.get_config("cassandra/contact_point")],
                               auth_provider=self.auth_provider,
                               load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1'),
                               protocol_version=3)
        self.session = self.cluster.connect(keyspace=consul.get_config("cassandra/keyspace"))

    async def check_cassandra_minute_already_present(self, timestamp, symbol):
        query = "SELECT * FROM tradeBin1m WHERE timestamp = %s AND symbol = %s"
        result = self.session.execute(query, (timestamp, symbol))

        return result

    async def insert_cassandra_tradeBin1m(self, data):
        batch = BatchStatement()

        for trade in data:
            if trade['symbol'][0] == '.':
                # This is index value, not a cryptocurrency, no need to store
                continue
            timestamp = pd.Timestamp(trade['timestamp']).to_pydatetime()
            symbol = trade['symbol']
            open_price = trade['open']
            high_price = trade['high']
            low_price = trade['low']
            close_price = trade['close']
            trades = trade['trades']
            volume = trade['volume']
            last_size = trade.get('lastSize', 0)
            turnover = trade['turnover']
            home_notional = trade['homeNotional']
            foreign_notional = trade['foreignNotional']

            query = "INSERT INTO tradeBin1m (timestamp, symbol, open, high, low, close, trades, volume, lastSize, turnover, homeNotional, foreignNotional) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            batch.add(
                query,
                (timestamp, symbol, open_price, high_price, low_price, close_price, trades,
                 volume, last_size, turnover, home_notional, foreign_notional)
            )

        self.session.execute(batch)

    async def insert_cassandra_quote(self, data):
        batch = BatchStatement()

        for quote in data:
            timestamp = pd.Timestamp(quote['timestamp']).to_pydatetime()
            symbol = quote['symbol']
            bid_size = quote['bidSize']
            bid_price = quote['bidPrice']
            ask_price = quote['askPrice']
            ask_size = quote['askSize']

            query = "INSERT INTO quote (timestamp, symbol, bidSize, bidPrice, askPrice, askSize) VALUES (%s, %s, %s, %s, %s, %s)"
            batch.add(query, (timestamp, symbol, bid_size, bid_price, ask_price, ask_size))

        self.session.execute(batch)

    def __del__(self):
        self.session.shutdown()
        self.cluster.shutdown()
