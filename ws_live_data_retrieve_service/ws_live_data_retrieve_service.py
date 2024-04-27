import asyncio
import logging

import pandas as pd
import ujson as json
import websockets
from cassandra.query import BatchStatement

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

# Cassandra connection details
CASSANDRA_CONTACT_POINTS = ['localhost']
CASSANDRA_USERNAME = 'cassandra'
CASSANDRA_PASSWORD = 'cassandra'
CASSANDRA_KEYSPACE = 'crypto_project'


class CryptoSpotExchangeWsAsync:
    def __init__(self):
        self.uri = "wss://ws.bitmex.com/realtime?subscribe=tradeBin1m,quote"  # tradeBin1m,quote

        # self.auth_provider = PlainTextAuthProvider(username=CASSANDRA_USERNAME, password=CASSANDRA_PASSWORD)
        # self.cluster = Cluster(contact_points=CASSANDRA_CONTACT_POINTS, auth_provider=self.auth_provider)
        # self.session = self.cluster.connect(keyspace=CASSANDRA_KEYSPACE)

    async def insert_cassandra_tradeBin1m(self, data):
        batch = BatchStatement()

        for trade in data:
            timestamp = pd.Timestamp(trade['timestamp']).to_pydatetime()
            symbol = trade['symbol']
            open_price = trade['open']
            high_price = trade['high']
            low_price = trade['low']
            close_price = trade['close']
            trades = trade['trades']
            volume = trade['volume']
            last_size = trade['lastSize']
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
                    pass
                    # TODO: insert bulk.
                    #  quote is safe, tradeBin1m - need to check if not already present
                elif action == 'insert':
                    pass

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
