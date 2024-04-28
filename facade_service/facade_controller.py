import logging
from fastapi import FastAPI, Query, Request

from consul_service_registry import ConsulServiceRegistry
from facade_service import FacadeService

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

consul = ConsulServiceRegistry()
facade_service = FacadeService(consul=consul)


@app.get("/precomputed_report_data/{report_name}")
async def get_precomputed_report_data(report_name: str, request: Request):
    return facade_service.get_precomputed_report_data(report_name, dict(request.query_params))


@app.get("/live_data/{report_name}")
async def get_live_data(report_name: str, request: Request):
    return facade_service.get_live_data(report_name, dict(request.query_params))


if __name__ == "__main__":
    import uvicorn

    # consul.register_service("facade_service", "127.0.0.1", 8000)
    uvicorn.run(app, host="127.0.0.1", port=8000)
