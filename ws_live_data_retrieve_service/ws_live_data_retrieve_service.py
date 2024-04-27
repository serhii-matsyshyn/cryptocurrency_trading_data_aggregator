import asyncio
import logging

import pandas as pd
import ujson as json
import websockets
from cassandra.policies import DCAwareRoundRobinPolicy, HostDistance
from cassandra.query import BatchStatement
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


class CryptoSpotExchangeWsAsync:
    def __init__(self,
                 uri='wss://ws.bitmex.com/realtime?subscribe=tradeBin1m,quote',  # tradeBin1m,quote
                 cassandra_keyspace='crypto_project'):
        self.uri = uri
        self.cassandra_keyspace = cassandra_keyspace

        self.auth_provider = PlainTextAuthProvider(username=CASSANDRA_USERNAME, password=CASSANDRA_PASSWORD)
        self.cluster = Cluster(contact_points=CASSANDRA_CONTACT_POINTS, auth_provider=self.auth_provider,
                               load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1'),
                               protocol_version=3)
        self.session = self.cluster.connect(keyspace=self.cassandra_keyspace)

    async def check_cassandra_minute_already_present(self, timestamp, symbol):
        query = "SELECT * FROM tradeBin1m WHERE timestamp = %s AND symbol = %s"
        result = self.session.execute(query, (timestamp, symbol))

        logger.debug(result)

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

    async def process_message(self, message_raw):
        logger.debug(message_raw)
        message = json.loads(message_raw)

        table = message.get("table")
        action = message.get("action")

        try:
            if 'subscribe' in message:
                logger.debug("Subscribed to %s." % message['subscribe'])
            elif action:
                # 'partial' - full table image
                # 'insert'  - new row
                # 'update'  - update row
                # 'delete'  - delete row
                data = message['data']
                if action == 'partial':
                    if table == 'tradeBin1m':
                        if len(data) > 0:
                            timestamp = pd.Timestamp(data[0]['timestamp']).to_pydatetime()
                            symbol = data[0]['symbol']
                            result = await self.check_cassandra_minute_already_present(timestamp, symbol)
                            if result:
                                logger.info("Data already present in Cassandra.")
                                return
                        await self.insert_cassandra_tradeBin1m(data)
                    elif table == 'quote':
                        await self.insert_cassandra_quote(data)
                elif action == 'insert':
                    if table == 'tradeBin1m':
                        await self.insert_cassandra_tradeBin1m(data)
                    elif table == 'quote':
                        await self.insert_cassandra_quote(data)

        except Exception as err:
            logger.error(str(err))

    async def subscribe_to_bitmex(self):
        async with websockets.connect(self.uri) as websocket:
            while True:
                message = await websocket.recv()
                processed = await self.process_message(message)

    async def main(self):
        await self.subscribe_to_bitmex()

    def __del__(self):
        self.session.shutdown()
        self.cluster.shutdown()


if __name__ == "__main__":
    data_receive_service = CryptoSpotExchangeWsAsync()
    asyncio.run(data_receive_service.main())
