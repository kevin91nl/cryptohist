# CryptoHist

A scraper written in Python 3 for scraping cryptocurrency historical data.

## Usage

Use this script at your own risk! The following functions are available:

### CoinMarketCap fetcher

Fetches historical data from https://coinmarketcap.com/

```
from cryptohist.coinmarketcap import CoinMarketCapFetcher

# Import Bitcoin historical data
fetcher = CoinMarketCapFetcher()
df_btc = fetcher.fetch_by_symbol('BTC')
print(df_btc)
```

#### List all currencies

Get all symbols:

```
from cryptohist.coinmarketcap import CoinMarketCapFetcher

fetcher = CoinMarketCapFetcher()
print(fetcher.get_symbols())
```

Or get all symbol names:

```
from cryptohist.coinmarketcap import CoinMarketCapFetcher

fetcher = CoinMarketCapFetcher()
print(fetcher.get_names())
```

#### Fetch historical data

Fetch by symbol:

```
from cryptohist.coinmarketcap import CoinMarketCapFetcher

# Import Bitcoin historical data
fetcher = CoinMarketCapFetcher()
df_btc = fetcher.fetch_by_symbol('BTC')
print(df_btc)
```

Fetch by name:

```
from cryptohist.coinmarketcap import CoinMarketCapFetcher

# Import Bitcoin historical data
fetcher = CoinMarketCapFetcher()
df_btc = fetcher.fetch_by_name('Bitcoin')
print(df_btc)
```

#### Fetch partial historical data

You can even specify a start and end time:

```
import datetime
from cryptohist.coinmarketcap import CoinMarketCapFetcher

# Import Bitcoin partial historical data
fetcher = CoinMarketCapFetcher(start=datetime.datetime(2014, 1, 1), end=datetime.datetime(2015, 1, 1))
df_btc = fetcher.fetch_by_symbol('BTC')
print(df_btc)
```

#### Force rebuilding cache

All data is cached by default (on disk and in-memory). You can force to rebuild this cache as follows:

```
import datetime
from cryptohist.coinmarketcap import CoinMarketCapFetcher

# Force rebuilding the cache
fetcher = CoinMarketCapFetcher(force=True)
df_btc = fetcher.fetch_by_symbol('BTC')
print(df_btc)
```

## Contributing

Feel free to contribute! If you have any questions, you can send me an e-mail at mail@kevinjacobs.nl.