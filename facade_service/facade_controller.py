import logging
import os
from socket import gethostname, gethostbyname
from fastapi import FastAPI, Query, Request

from consul_service_registry import ConsulServiceRegistry
from facade_service import FacadeService

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

consul = ConsulServiceRegistry(consul_host="consul-server", consul_port=8500)
facade_service = FacadeService(consul=consul)


@app.get("/precomputed_report_data/{report_name}")
async def get_precomputed_report_data(report_name: str, request: Request):
    return facade_service.get_precomputed_report_data(report_name, dict(request.query_params))


@app.get("/live_data/{report_name}")
async def get_live_data(report_name: str, request: Request):
    return facade_service.get_live_data(report_name, dict(request.query_params))


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("SERVICE_PORT"))
    consul.register_service("facade_service", gethostbyname(gethostname()), port)
    uvicorn.run(app, host=gethostbyname(gethostname()), port=port)
