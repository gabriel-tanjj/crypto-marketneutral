import numpy as np
import requests
import lzma
import pandas as pd
from datetime import datetime, timedelta
import dill as pickle
import matplotlib.pyplot as plt


period_start = "2021-01-01"
period_end = "2024-04-19"

years = [2021, 2022, 2023, 2024]
def load_pickle(filepath):
    with lzma.open(filepath, 'rb') as fp:
        data = pickle.load(fp)
    return data

def save_pickle(filepath, obj):
    with lzma.open(filepath, 'wb') as fp:
        pickle.dump(obj, fp)
# def get_binance_ohlc(symbol, interval="1d", start_date=period_start, end_date=period_end):
#
#     end_time = datetime.strptime(end_date, "%Y-%m-%d")
#     start_time = datetime.strptime(start_date, "%Y-%m-%d")
#
#     end_time_str = int(end_time.timestamp() * 1000)
#     start_time_str = int(start_time.timestamp() * 1000)
#
#     url = "https://api.binance.com/api/v3/klines"
#     params = {
#         "symbol": symbol,
#         "interval": interval,
#         "startTime": start_time_str,
#         "endTime": end_time_str
#     }
#
#     response = requests.get(url, params=params)
#     if response.status_code != 200:
#         print(f"Error fetching data for {symbol}: {response.status_code}")
#         return pd.DataFrame()
#
#     data = response.json()
#
#     df = pd.DataFrame(data, columns=[
#         "datetime", "open", "high", "low", "close", "volume",
#         "close_time", "quote_asset_volume", "number_of_trades",
#         "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
#     ])
#
#     df["datetime"] = pd.to_datetime(df["datetime"], unit="ms")
#
#     df.set_index("datetime", inplace=True)
#
#     df["open"] = pd.to_numeric(df["open"], errors='coerce')
#     df["high"] = pd.to_numeric(df["high"], errors='coerce')
#     df["low"] = pd.to_numeric(df["low"], errors='coerce')
#     df["close"] = pd.to_numeric(df["close"], errors='coerce')
#     df["volume"] = pd.to_numeric(df["volume"], errors='coerce')
#
#     df = df[["open", "high", "low", "close", "volume"]]
#
#     return df
#
# def get_crypto_data():
#     pairs = ["ETHUSDT", "ETCUSDT", "BCHUSDT", "ADAUSDT",
#              "LTCUSDT", "XRPUSDT", "SOLUSDT", "BTCUSDT", "SNXUSDT", "RUNEUSDT",
#              "AAVEUSDT", "COMPUSDT", "BNBUSDT", "LINKUSDT", "TRXUSDT",
#              "DOGEUSDT", "MATICUSDT", "AVAXUSDT", "NEARUSDT",
#              "UNIUSDT", "FILUSDT", "ALGOUSDT", "NEOUSDT", "AXSUSDT",
#              "SANDUSDT", "MANAUSDT", "SUSHIUSDT", "KAVAUSDT", "DOTUSDT"]
#
#     dfs = {pair: [] for pair in pairs}
#
#     for year in years:
#         if year != 2024:
#             period_start = f"{year}-01-01"
#             period_end = f"{year}-12-31"
#         else:
#             period_start = f"{year}-01-01"
#             period_end = "2024-04-19"
#
#         for pair in pairs:
#             dfs[pair].append(get_binance_ohlc(symbol=pair, start_date=period_start, end_date=period_end))
#
#     tickers = list(dfs.keys())
#     merged_data_dfs = {ticker: pd.concat(data) for ticker, data in dfs.items()}
#     return tickers, merged_data_dfs
#
# tickers, crypto_data_dfs = get_crypto_data()

try:
    tickers, crypto_data_dfs = load_pickle("crypto_data.obj")
except Exception as err:
    save_pickle("crypto_data.obj", (tickers, crypto_data_dfs))

from sample import testAlpha
from main_alpha import Alpha
alpha = Alpha(insts=tickers, dfs=crypto_data_dfs, start=period_start, end="2024-04-18")
test = alpha.run_simulation()
print(test)





