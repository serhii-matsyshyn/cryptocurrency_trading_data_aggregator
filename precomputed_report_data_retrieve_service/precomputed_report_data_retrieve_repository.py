from pymongo import MongoClient


class PrecomputedReportDataRetrieveRepository:
    def __init__(self, consul):
        self.consul = consul
        self.client = MongoClient(self.consul.get_config("mongodb/uri"))
        self.db_main = self.client[self.consul.get_config("mongodb/database")]

    def get_hourly_transactions(self):
        db_table = self.db_main['hourly_transactions']
        latest_data = db_table.find_one({}, sort=[('report_date', -1)])

        return latest_data

    def get_total_volume(self, volume_type: str):
        db_table = self.db_main[f"total_volume_{volume_type}"]
        latest_data = db_table.find_one({}, sort=[('report_date', -1)])

        return latest_data

    def get_hourly_trades_volume(self, volume_type: str):
        db_table = self.db_main[f"hourly_trades_volume_{volume_type}"]
        latest_data = db_table.find_one({}, sort=[('report_date', -1)])

        return latest_data

    def __del__(self):
        self.client.close()
