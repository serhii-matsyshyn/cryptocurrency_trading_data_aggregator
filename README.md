# Cryptocurrency trading data aggregator

Author: Serhii Matsyshyn (https://github.com/serhii-matsyshyn) <br>

## System architecture diagram
![Cryptocurrency_trading_data_aggregator_system_architecture_2.drawio.png](data%2Fimages%2FCryptocurrency_trading_data_aggregator_system_architecture_2.drawio.png)

## 🖥 Usage

### ws_live_data_retrieve_service
```shell
cd ws_live_data_retrieve_service
sudo docker-compose -f docker-compose-cassandra-cluster.yml up
cat schema_creation.cql | sudo docker exec -i cassandra1 cqlsh
python3 ws_live_data_retrieve_service.py
```

### sheduled_report_compute_service
```shell
cd sheduled_report_compute_service
docker-compose -f docker-compose-mongodb-spark.yml up
python3 sheduled_report_compute_service.py
```

### precomputed_report_data_retrieve_service
```shell
cd precomputed_report_data_retrieve_service
python3 precomputed_report_data_retrieve_controller.py
```

### live_data_retrieve_service
```shell
cd live_data_retrieve_service
docker-compose -f docker-compose-hazelcast.yml up
python3 live_data_retrieve_controller.py
```

### facade_service
```shell
cd facade_service
python3 facade_controller.py
```

## REST API
The following REST APIs are available:  

Part A: A set of REST APIs that will return the precomputed report data. The data for these reports would be prepared in advance with batch processing operations:
1. Return the aggregated statistics containing the number of transactions for each cryptocurrency for each hour in the last 6 hours, excluding the previous hour.
2. Return the statistics about the total trading volume for each cryptocurrency for the last 6 hours, excluding the previous hour.
3. Return aggregated statistics containing the number of trades and their total volume for each hour in the last 12 hours, excluding the current hour.

Part B: A set of REST APIs that will return the results of ad-hoc queries. User provides parameters to the API and it should respond according to the specified values:
1. Return the number of trades processed in a specific cryptocurrency in the last N minutes, excluding the last minute.
2. Return the top N cryptocurrencies with the highest trading volume in the last hour.
3. Return the cryptocurrency’s current price for «Buy» and «Sell» sides based on its symbol.

## Services ports

- facade_service: 8000
- sheduled_report_compute_service: 8001
- precomputed_report_data_retrieve_service: 8002
- ws_live_data_retrieve_service: 8003
- live_data_retrieve_service: 8004
and other services ports
- Hazelcast: 5701
- Hazelcast Management Center: 8180