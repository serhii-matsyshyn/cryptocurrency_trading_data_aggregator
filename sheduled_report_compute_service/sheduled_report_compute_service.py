import time
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd

from consul_service_registry import ConsulServiceRegistry

pd.set_option('display.min_rows', 1000)
pd.set_option('display.max_rows', 1000)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CryptoStatistics:
    def __init__(self, consul):
        self.consul = consul
        self.spark = SparkSession.builder \
            .appName("CryptoStatistics") \
            .config("spark.master", self.consul.get_config("spark/master")) \
            .config('spark.jars.packages', "com.datastax.spark:spark-cassandra-connector_2.12:3.5.0") \
            .config("spark.cassandra.connection.host", self.consul.get_config("cassandra/contact_point")) \
            .config("spark.sql.session.timeZone", "UTC") \
            .getOrCreate()

        self.client = MongoClient(self.consul.get_config("mongodb/uri"))
        self.db = self.client[self.consul.get_config("mongodb/database")]

        self.compute_and_save_statistics()  # Compute and save statistics for the first time
        self.scheduler = BackgroundScheduler()

        # self.scheduler.add_job(self.compute_and_save_statistics, 'interval', minutes=5)
        self.scheduler.add_job(self.compute_and_save_statistics, 'cron', minute=0, second=1)

        self.scheduler.start()

    def compute_and_save_statistics(self):
        df = self.load_data_from_cassandra()

        result = {
            "hourly_transactions": self.compute_hourly_transactions(df),
            "total_volume_foreignNotional": self.compute_total_volume(df, "foreignNotional"),
            "hourly_trades_volume_foreignNotional": self.compute_hourly_trades_volume(df, "foreignNotional"),
            "total_volume_homeNotional": self.compute_total_volume(df, "homeNotional"),
            "hourly_trades_volume_homeNotional": self.compute_hourly_trades_volume(df, "homeNotional")
        }

        self.save_to_mongodb(result)

    def load_data_from_cassandra(self):
        df = self.spark.read \
            .format("org.apache.spark.sql.cassandra") \
            .options(table="tradebin1m", keyspace=consul.get_config("cassandra/keyspace")) \
            .load()
        return df

    def compute_hourly_transactions(self, df):
        hourly_transactions = df \
            .withColumn("hour", F.hour("timestamp")) \
            .groupBy("symbol", "hour") \
            .agg(F.sum("trades").alias("transaction_count")) \
            .filter(
            (F.col("hour") >= F.hour(F.current_timestamp()) - 6)
            & (F.col("hour") != F.hour(F.current_timestamp()))
        ).sort(
            F.col("transaction_count").desc()
        ).toPandas()
        return hourly_transactions

    def compute_total_volume(self, df, volume_type="foreignnotional"):
        start_hour = F.date_trunc("hour", F.current_timestamp() - F.expr("INTERVAL 6 HOURS"))

        df_filtered = df.filter(
            (F.date_trunc("hour", F.col("timestamp")) >= start_hour)
            & (F.date_trunc("hour", F.col("timestamp")) < F.date_trunc("hour", F.current_timestamp()))
        )

        # Calculate total trading volume for each symbol
        total_volume = df_filtered \
            .groupBy("symbol") \
            .agg(F.sum(volume_type).alias("total_volume")) \
            .sort(  # by total_volume
            F.col("total_volume").desc()
        ).toPandas()

        return total_volume

    def compute_hourly_trades_volume(self, df, volume_type="foreignnotional"):
        start_hour = F.date_trunc("hour", F.current_timestamp() - F.expr("INTERVAL 12 HOURS"))

        hourly_trades_volume = df \
            .withColumn("hour", F.hour("timestamp")) \
            .filter((F.col("timestamp") >= start_hour)
                    & (F.col("hour") != F.hour(F.current_timestamp()))
                    ) \
            .groupBy("hour") \
            .agg(F.sum("trades").alias("trade_count"), F.sum(volume_type).alias("total_volume")) \
            .sort(F.col("trade_count").desc()).toPandas()
        return hourly_trades_volume

    def save_to_mongodb(self, result):
        for key, value in result.items():
            collection = self.db[key]
            data = {
                "report_date": pd.Timestamp.utcnow(),
                "data": value.to_dict(orient='records')
            }

            logger.debug(f"Result for {key}:")
            logger.debug(data)

            collection.insert_one(data)

    def __del__(self):
        try:
            self.spark.stop()
            self.scheduler.shutdown()
            self.client.close()
            self.consul.deregister_service()
        except Exception as e:
            logger.error(e)


if __name__ == "__main__":
    consul = ConsulServiceRegistry(consul_host="consul-server",
                                   consul_port=8500)
    crypto_statistics = CryptoStatistics(consul=consul)
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        crypto_statistics.scheduler.shutdown()
