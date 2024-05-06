class TopNCryptosLastHourModel:
    def __init__(self, top_cryptos=None, volume_type="N/A", start_timestamp="N/A", end_timestamp="N/A"):
        self.top_cryptos = top_cryptos if top_cryptos is not None else {}
        self.volume_type = volume_type
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp

    def __str__(self):
        return f"TopNCryptosLastHour(top_cryptos={self.top_cryptos}, volume_type={self.volume_type}, start_timestamp={self.start_timestamp}, end_timestamp={self.end_timestamp})"

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {
            'top_cryptos': self.top_cryptos,
            'volume_type': self.volume_type,
            'start_timestamp': self.start_timestamp,
            'end_timestamp': self.end_timestamp
        }

    def __getitem__(self, key):
        return self.to_dict()[key]


class SumTradesLastNMinutesModel:
    def __init__(self, symbol="N/A", total_trades=0, start_timestamp="N/A", end_timestamp="N/A"):
        self.symbol = symbol
        self.total_trades = total_trades
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp

    def __str__(self):
        return f"SumTradesLastNMinutes(symbol={self.symbol}, total_trades={self.total_trades}, start_timestamp={self.start_timestamp}, end_timestamp={self.end_timestamp})"

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {
            'symbol': self.symbol,
            'total_trades': self.total_trades,
            'start_timestamp': self.start_timestamp,
            'end_timestamp': self.end_timestamp
        }

    def __getitem__(self, key):
        return self.to_dict()[key]


class LatestPricesModel:
    def __init__(self, symbol="N/A", bidPrice="N/A", askPrice="N/A", timestamp="N/A"):
        self.symbol = symbol
        self.bidPrice = bidPrice
        self.askPrice = askPrice
        self.timestamp = timestamp

    def __str__(self):
        return f"LatestPrices(symbol={self.symbol}, bidPrice={self.bidPrice}, askPrice={self.askPrice}, timestamp={self.timestamp})"

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {
            'symbol': self.symbol,
            'bidPrice': self.bidPrice,
            'askPrice': self.askPrice,
            'timestamp': self.timestamp
        }

    def __getitem__(self, key):
        return self.to_dict()[key]
