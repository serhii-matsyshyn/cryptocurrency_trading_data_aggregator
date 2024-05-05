import logging
from precomputed_report_data_retrieve_repository import PrecomputedReportDataRetrieveRepository


logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PrecomputedReportDataRetrieveService:
    def __init__(self, consul):
        self.consul = consul
        self.repository = PrecomputedReportDataRetrieveRepository(consul=self.consul)

    def get_hourly_transactions(self):
        data = self.repository.get_hourly_transactions()
        if not data:
            return {"error": "No data found! Wait for the next computation cycle!"}
        return {"report_date": data["report_date"], "report_name": 'hourly_transactions', "data": data["data"]}

    def get_total_volume(self, volume_type: str):
        data = self.repository.get_total_volume(volume_type=volume_type)
        if not data:
            return {"error": "No data found! Wait for the next computation cycle!"}
        return {"report_date": data["report_date"], 'report_name': f"total_volume_{volume_type}", "data": data["data"]}

    def get_hourly_trades_volume(self, volume_type: str):
        data = self.repository.get_hourly_trades_volume(volume_type=volume_type)
        if not data:
            return {"error": "No data found! Wait for the next computation cycle!"}
        return {"report_date": data["report_date"], 'report_name': f"hourly_trades_volume_{volume_type}", "data": data["data"]}

    def __del__(self):
        try:
            self.consul.deregister_service()
        except Exception as e:
            logger.error(e)
