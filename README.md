# Cryptocurrency trading data aggregator

Author: Serhii Matsyshyn (https://github.com/serhii-matsyshyn) <br>

## System architecture diagram
![Cryptocurrency_trading_data_aggregator_system_architecture_3.drawio.png](data%2Fimages%2FCryptocurrency_trading_data_aggregator_system_architecture_3.drawio.png)


## Roles of microservices:

- WS live data retrieve service - constantly, in real time, receives data from the websocket of the cryptocurrency exchange (data received with a high frequency). Stores data in Cassandra Cluster.

Part A:
- Scheduled report compute service - uses Apache Spark connected to Cassandra Cluster to generate advanced data reports every hour. Stores advanced reports in MongoDB. MongoDB (rather than Cassandra) is chosen here because MongoDB is optimized and more efficient for heavy read loads, while Cassandra is better for heavy write loads.
- Precomputed report data retrieve service - a microservice that receives advanced reports from MongoDB. The Facade Service and the Precomputed Report Data Retrieve Service are separated because it contributes to modularity, scalability, and facilitates independent maintenance and upgrade of microservices.

Part B:
- Streaming (live) data retrieve service -  
  The service responsible for getting the latest data from the Cassandra Cluster.  
  Since sum trades last n minutes and top n cryptos last hour have a specific behavior (necessary in trading), namely, they return the result excluding the data of the last minute (since it is not yet considered "closed"), then these queries and responses are cached using Hazelcast.  
  Thus, the unnecessary load on the Cassandra Cluster is reduced and the speed of operation is increased, which is quite critical, since Part B is a highly loaded (with a possible large number of requests from clients).  
<br><br>
  Facade Service and Streaming (live) data retrieve service exchange data based on the Publish-Subscribe pattern. That is, there is one queue where Facade Service clients send the necessary requests, one of the free Streaming (live) data retrieve microservices processes it and returns a response to the Hazelcast Topic, which was previously defined and provided together with the Facade Service client.  
  The Publish-Subscribe pattern is used to reduce latency during the internal interaction of microservices - since, in the case of HTTP, you need to constantly establish and stop connections, this implementation can avoid this.  
  This microservice can be scaled as simply and quickly as possible by launching additional instances of the microservice.  

- Facade Service - provides an HTTP Rest API to the client. You can find example requests [here](facade_service/Requests.http).

## REST API
**Note: you should get acquainted with the [`Information on volume type` section](#information-on-volume-type) beforehand**  

The following REST APIs are available:  

Part A: A set of REST APIs that will return the precomputed report data. The data for these reports would be prepared in advance with batch processing operations:
1. Return the aggregated statistics containing the number of transactions for each cryptocurrency for each hour in the last 6 hours, excluding the previous hour.
2. Return the statistics about the total trading volume for each cryptocurrency for the last 6 hours, excluding the previous hour.
3. Return aggregated statistics containing the number of trades and their total volume for each hour in the last 12 hours, excluding the current hour.

Part B: A set of REST APIs that will return the results of ad-hoc queries. User provides parameters to the API and it should respond according to the specified values:
1. Return the number of trades processed in a specific cryptocurrency in the last N minutes, excluding the last minute.
2. Return the top N cryptocurrencies with the highest trading volume in the last hour.
3. Return the cryptocurrency’s current price for «Buy» and «Sell» sides based on its symbol.

**You can find example requests [here - facade_service/Requests.http](facade_service/Requests.http)**

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

### Infrastructure services
```shell
cd infrastructure_services
./start-infrastructure-services.sh
```

### Docker compose run all services
It is possible to use the following command to run all services, but it may cause docker-compose and build merge issues:
```shell
sudo docker-compose -f ws_live_data_retrieve_service/docker-compose.yml \
                    -f sheduled_report_compute_service/docker-compose.yml \
                    -f precomputed_report_data_retrieve_service/docker-compose.yml \
                    -f live_data_retrieve_service/docker-compose.yml \
                    -f facade_service/docker-compose.yml \
up
```

For an easy debug, you can run each service separately (it is recommended to use this method):
```shell
sudo docker-compose -f ws_live_data_retrieve_service/docker-compose.yml up -d
sudo docker-compose -f sheduled_report_compute_service/docker-compose.yml up -d
sudo docker-compose -f precomputed_report_data_retrieve_service/docker-compose.yml up -d
sudo docker-compose -f live_data_retrieve_service/docker-compose.yml up -d
sudo docker-compose -f facade_service/docker-compose.yml up -d
```

### To attach to logs of service:
```shell
sudo docker container logs -f ws-live-data-retrieve-service
```

### To stop a certain service only (useful for debugging):
```shell
sudo docker stop live-data-retrieve-service-1
```

### To stop all services:
```shell
sudo docker-compose -f ws_live_data_retrieve_service/docker-compose.yml down
sudo docker-compose -f sheduled_report_compute_service/docker-compose.yml down
sudo docker-compose -f precomputed_report_data_retrieve_service/docker-compose.yml down
sudo docker-compose -f live_data_retrieve_service/docker-compose.yml down
sudo docker-compose -f facade_service/docker-compose.yml down
sudo docker-compose -f infrastructure_services/docker-compose-infrastructure.yml down
```
### To rebuild all services:
```shell
sudo docker-compose -f ws_live_data_retrieve_service/docker-compose.yml build --no-cache
sudo docker-compose -f sheduled_report_compute_service/docker-compose.yml build --no-cache
sudo docker-compose -f precomputed_report_data_retrieve_service/docker-compose.yml build --no-cache
sudo docker-compose -f live_data_retrieve_service/docker-compose.yml build --no-cache
sudo docker-compose -f facade_service/docker-compose.yml build --no-cache
```

### Services ports

- facade_service: 8000
- sheduled_report_compute_service: 8001
- precomputed_report_data_retrieve_service: 8002
- ws_live_data_retrieve_service: 8003
- live_data_retrieve_service: 8004 - 8006
and other services ports
- Hazelcast: 5701
- Hazelcast Management Center: 8180
- Consul: 8500
- Spark: 8080
- MongoDB: 27017

## Demonstration of the system
The system was up and running for 5 hours before the demonstration. The demonstration was run at 17:25 UTC (20:25 Kyiv time).
You can see active services in docker ps:
![img.png](data/images/demonstration_1/img.png)
The health checks (Consul by HashiCorp) of the API-available services are successful:
![img_1.png](data/images/demonstration_1/img_1.png)
![img_2.png](data/images/demonstration_1/img_2.png)
The following requests were made to the facade service: [see this Requests.http file](facade_service/Requests.http)

Execution time of the requests:
![img_3.png](data/images/demonstration_1/img_3.png)
Subsequent requests time (within 1 minute):
![img_4.png](data/images/demonstration_1/img_4.png)
We can see that using distributed cache (Hazelcast) significantly reduces the response time of the live service (that have 1 minute cache - `top_n_cryptos_last_hour`, `sum_trades_last_n_minutes`).

Please find attached the responses to the requests in the [data/demonstration](data/demonstration) folder. The files are named a_1.json, a_2.1.json, etc. as per the request number in the [facade_service/Requests.http](facade_service/Requests.http) file.  
Note, that responses data is sorted by transactions number and volume in descending order (where applicable).

## 📌 Nota bene
Project was developed and tested on Ubuntu 22.04.3 LTS.  
UTC time is used in the project.  

### Information on volume type
The reason for having separate endpoints params (`foreignNotional`, `homeNotional`) is input data format - Bitmex's unique method of reporting trading volume. Bitmex doesn't provide a unified volume value in a fixed currency like USD (or BTC); instead, it offers volume data in various forms such as home, foreign, or relative points based on the specific cryptocurrency pairs being traded.

Sorting by volume can present challenges in interpretation. For instance, if using `volume` value (that is, relative points) or `homeNotional`, cryptocurrencies like PEPE with a high number of digits may appear to have a higher volume than BTC, despite BTC being a more widely traded asset. This discrepancy arises due to the differing digit counts in their respective representations (and mixed `volume` representation across pairs).

Using `foreignNotional` as the volume type offers a more stable calculation. This is because most cryptocurrencies on Bitmex are paired with USD-based assets like USD, USDT, or USDC. However, there are exceptions such as BTCETH pairs, which can introduce some complexity.

Unfortunately, it's impractical to split pairs or calculate a relative volume value due to the limitations of Bitmex's data reporting. As a result, separate endpoints params are necessary to provide clarity on trading volume metrics based on different volume types, and still, there are several pairs that will be incorrectly sorted, if their `foreignNotional` is not USD-based.
