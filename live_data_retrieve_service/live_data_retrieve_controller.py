import argparse
import logging
import os
from socket import gethostname, gethostbyname
from fastapi import FastAPI, Query, Request

from consul_service_registry import ConsulServiceRegistry
from live_data_retrieve_service import LiveDataRetrieveService

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

consul = ConsulServiceRegistry(consul_host="consul-server", consul_port=8500)
live_data_retrieve_service = LiveDataRetrieveService(consul=consul)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == '__main__':
    import uvicorn

    port = int(os.environ.get("SERVICE_PORT"))
    consul.register_service("live_data_retrieve_service", gethostbyname(gethostname()), port)
    uvicorn.run(app, host=gethostbyname(gethostname()), port=port)
