import logging
import os
from socket import gethostname, gethostbyname
from fastapi import FastAPI, Query

from consul_service_registry import ConsulServiceRegistry
from precomputed_report_data_retrieve_service import PrecomputedReportDataRetrieveService

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

consul = ConsulServiceRegistry(consul_host="consul-server", consul_port=8500)
precomputed_report_data_retrieve_service = PrecomputedReportDataRetrieveService(consul=consul)


@app.get("/hourly_transactions")
async def get_hourly_transactions():
    return precomputed_report_data_retrieve_service.get_hourly_transactions()


@app.get("/total_volume")
async def get_total_volume(volume_type: str = Query("foreignNotional")):
    if volume_type not in ("foreignNotional", "homeNotional"):
        return {"error": f"Invalid volume_type: {volume_type}"}
    return precomputed_report_data_retrieve_service.get_total_volume(volume_type=volume_type)


@app.get("/hourly_trades_volume")
async def get_hourly_trades_volume(volume_type: str = Query("foreignNotional")):
    if volume_type not in ("foreignNotional", "homeNotional"):
        return {"error": f"Invalid volume_type: {volume_type}"}
    return precomputed_report_data_retrieve_service.get_hourly_trades_volume(volume_type=volume_type)


@app.get('/health')
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("SERVICE_PORT"))
    consul.register_service("precomputed_report_data_retrieve_service", gethostbyname(gethostname()), port)
    uvicorn.run(app, host=gethostbyname(gethostname()), port=port)
