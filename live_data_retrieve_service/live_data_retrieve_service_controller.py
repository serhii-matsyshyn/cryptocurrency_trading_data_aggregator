import argparse
import logging
from fastapi import FastAPI, Query, Request

from consul_service_registry import ConsulServiceRegistry
from live_data_retrieve_service import LiveDataRetrieveService

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

consul = ConsulServiceRegistry()
live_data_retrieve_service = LiveDataRetrieveService(consul=consul)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == '__main__':
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, help="Specify the port number", default=8004)
    args = parser.parse_args()

    # consul.register_service("facade_service", "127.0.0.1", 8000)
    uvicorn.run(app, host="127.0.0.1", port=args.port)
