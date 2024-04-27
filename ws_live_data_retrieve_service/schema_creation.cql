CREATE KEYSPACE IF NOT EXISTS crypto_project WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3};

CREATE TABLE IF NOT EXISTS tradeBin1m (
    timestamp TIMESTAMP,
    symbol TEXT,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    trades INT,
    volume DOUBLE,
    lastSize DOUBLE,
    turnover DOUBLE,
    homeNotional DOUBLE,
    foreignNotional DOUBLE,
    PRIMARY KEY (timestamp, symbol)
);

CREATE TABLE IF NOT EXISTS quote (
    timestamp TIMESTAMP,
    symbol TEXT,
    bidSize INT,
    bidPrice DOUBLE,
    askPrice DOUBLE,
    askSize INT,
    PRIMARY KEY (timestamp, symbol)
);


