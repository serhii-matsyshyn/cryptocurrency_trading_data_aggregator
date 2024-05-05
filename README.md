# Cryptocurrency trading data aggregator

Author: Serhii Matsyshyn (https://github.com/serhii-matsyshyn) <br>

## System architecture diagram
![Cryptocurrency_trading_data_aggregator_system_architecture_2.drawio.png](data%2Fimages%2FCryptocurrency_trading_data_aggregator_system_architecture_2.drawio.png)

[//]: # (## 🖥 Usage)

[//]: # ()
[//]: # (### consul)

[//]: # (```shell)

[//]: # (cd consul)

[//]: # (sudo docker-compose -f docker-compose-consul.yml up)

[//]: # (```)

[//]: # ()
[//]: # (### ws_live_data_retrieve_service)

[//]: # (```shell)

[//]: # (cd ws_live_data_retrieve_service)

[//]: # (sudo docker-compose -f docker-compose-cassandra-cluster.yml up)

[//]: # (cat schema_creation.cql | sudo docker exec -i cassandra1 cqlsh)

[//]: # (python3 ws_live_data_retrieve_service.py)

[//]: # (```)

[//]: # ()
[//]: # (### sheduled_report_compute_service)

[//]: # (```shell)

[//]: # (cd sheduled_report_compute_service)

[//]: # (docker-compose -f docker-compose-mongodb-spark.yml up)

[//]: # (python3 sheduled_report_compute_service.py)

[//]: # (```)

[//]: # ()
[//]: # (### precomputed_report_data_retrieve_service)

[//]: # (```shell)

[//]: # (cd precomputed_report_data_retrieve_service)

[//]: # (python3 precomputed_report_data_retrieve_controller.py)

[//]: # (```)

[//]: # ()
[//]: # (### live_data_retrieve_service)

[//]: # (```shell)

[//]: # (cd live_data_retrieve_service)

[//]: # (docker-compose -f docker-compose-hazelcast.yml up)

[//]: # (python3 live_data_retrieve_controller.py -p 8004)

[//]: # (python3 live_data_retrieve_controller.py -p 8005)

[//]: # (python3 live_data_retrieve_controller.py -p 8006)

[//]: # (```)

[//]: # ()
[//]: # (### facade_service)

[//]: # (```shell)

[//]: # (cd facade_service)

[//]: # (python3 facade_controller.py)

[//]: # (```)

## 🖥 Usage

### Requirements
- Docker
- Docker-compose
- Python 3.10 or higher
- Pip

It is necessary to install the required Python packages on the host machine (for easy deployment):
```shell
pip3 install -r infrastructure_services/requirements.txt
```

### infrastructure_services
```shell
cd infrastructure_services
./start-infrastructure-services.sh
```

To stop infrastructure services:
```shell
sudo docker-compose -f docker-compose-infrastructure.yml down
```

### ws_live_data_retrieve_service
```shell
cd ws_live_data_retrieve_service
python3 ws_live_data_retrieve_service.py
```

### sheduled_report_compute_service
```shell
cd sheduled_report_compute_service
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
python3 live_data_retrieve_controller.py -p 8004
python3 live_data_retrieve_controller.py -p 8005
python3 live_data_retrieve_controller.py -p 8006
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

**You can find example requests [here](facade_service/Requests.http)**

## Services ports

- facade_service: 8000
- sheduled_report_compute_service: 8001
- precomputed_report_data_retrieve_service: 8002
- ws_live_data_retrieve_service: 8003
- live_data_retrieve_service: 8004 - 8006
and other services ports
- Hazelcast: 5701
- Hazelcast Management Center: 8180

## 📌 Nota bene
Project was developed and tested on Ubuntu 22.04.3 LTS.  

### Information on volume type
The reason for having separate endpoints params (`foreignNotional`, `homeNotional`) is Bitmex's unique method of reporting trading volume. Bitmex doesn't provide a unified volume value in a fixed currency like USD (or BTC); instead, it offers volume data in various forms such as home, foreign, or relative points based on the specific cryptocurrency pairs being traded.

Sorting by volume can present challenges in interpretation. For instance, if using `volume` value (that is, relative points) or `homeNotional`, cryptocurrencies like PEPE with a high number of digits may appear to have a higher volume than BTC, despite BTC being a more widely traded asset. This discrepancy arises due to the differing digit counts in their respective representations (and mixed `volume` representation across pairs).

Using `foreignNotional` as the volume type offers a more stable calculation. This is because most cryptocurrencies on Bitmex are paired with USD-based assets like USD, USDT, or USDC. However, there are exceptions such as BTCETH pairs, which can introduce some complexity.

Unfortunately, it's impractical to split pairs or calculate a relative volume value due to the limitations of Bitmex's data reporting. As a result, separate endpoints params are necessary to provide clarity on trading volume metrics based on different volume types, and still, there are several pairs that will be incorrectly sorted, if their `foreignNotional` is not USD-based.