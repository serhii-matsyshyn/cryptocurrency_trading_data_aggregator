CREATE KEYSPACE IF NOT EXISTS crypto_project WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3};

USE crypto_project;

CREATE TABLE IF NOT EXISTS tradeBin1m (
    timestamp TIMESTAMP,
    symbol TEXT,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    trades BIGINT,
    volume DOUBLE,
    lastSize DOUBLE,
    turnover DOUBLE,
    homeNotional DOUBLE,
    foreignNotional DOUBLE,
    PRIMARY KEY (symbol, timestamp)
);

CREATE TABLE IF NOT EXISTS quote (
    timestamp TIMESTAMP,
    symbol TEXT,
    bidSize BIGINT,
    bidPrice DOUBLE,
    askPrice DOUBLE,
    askSize BIGINT,
    PRIMARY KEY (symbol, timestamp)
);


