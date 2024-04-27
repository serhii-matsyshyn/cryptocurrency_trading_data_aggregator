# Cryptocurrency trading data aggregator

Author: Serhii Matsyshyn (https://github.com/serhii-matsyshyn) <br>

## System architecture diagram
![Cryptocurrency_trading_data_aggregator_system_architecture_2.drawio.png](data%2Fimages%2FCryptocurrency_trading_data_aggregator_system_architecture_2.drawio.png)

## 🖥 Usage

### ws_live_data_retrieve_service
```shell
cd ws_live_data_retrieve_service
sudo docker-compose -f docker-compose-cassandra-cluster.yml up
python3 ws_live_data_retrieve_service.py
```