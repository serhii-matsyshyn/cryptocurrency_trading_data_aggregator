import asyncio
import logging

import pandas as pd
import ujson as json
import websockets

from ws_live_data_retrieve_repository import WSLiveDataRetrieveRepository
from consul_service_registry import ConsulServiceRegistry


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CryptoSpotExchangeWsAsync:
    def __init__(self, uri='wss://ws.bitmex.com/realtime?subscribe=tradeBin1m,quote'):
        self.consul = ConsulServiceRegistry()
        self.repository = WSLiveDataRetrieveRepository(self.consul)
        self.uri = uri

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
                            result = await self.repository.check_cassandra_minute_already_present(timestamp, symbol)
                            if result:
                                logger.info("Data already present in Cassandra.")
                                return
                        await self.repository.insert_cassandra_tradeBin1m(data)
                    elif table == 'quote':
                        await self.repository.insert_cassandra_quote(data)
                elif action == 'insert':
                    if table == 'tradeBin1m':
                        await self.repository.insert_cassandra_tradeBin1m(data)
                    elif table == 'quote':
                        await self.repository.insert_cassandra_quote(data)

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
        self.consul.deregister_service()


if __name__ == "__main__":
    while True:
        try:
            data_receive_service = CryptoSpotExchangeWsAsync()
            asyncio.run(data_receive_service.main())
        except Exception as e:
            logger.error(e)
            continue
