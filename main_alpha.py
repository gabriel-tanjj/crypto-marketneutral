import pytz
import lzma
import dill as pickle
import pandas as pd
from copy import deepcopy
from pandas import to_datetime
import matplotlib.pyplot as plt


def load_pickle(filepath):
    with lzma.open(filepath, 'rb') as fp:
        data = pickle.load(fp)
    return data

def save_pickle(filepath, obj):
    with lzma.open(filepath, 'wb') as fp:
        pickle.dump(obj, fp)

def get_pnl_stats(idx, prev, portfolio_df, insts, dfs, date):
    nominal_ret = 0
    day_pnl = 0
    for inst in insts:
        units = portfolio_df.loc[idx-1, "{} units".format(inst)]
        if units != 0:
            delta = dfs[inst].loc[date, "close"] - dfs[inst].loc[prev, "close"]
            inst_pnl = delta * units
            day_pnl += inst_pnl
            nominal_ret += portfolio_df.loc[idx-1, "{} w".format(inst)] * dfs[inst].loc[date, "ret"]
    capital_ret = nominal_ret * portfolio_df.loc[idx-1, "leverage"]
    portfolio_df.loc[idx, "capital"] = portfolio_df.loc[idx-1, "capital"] + day_pnl
    portfolio_df.loc[idx, "day_pnl"] = day_pnl
    portfolio_df.loc[idx, "nominal_return"] = nominal_ret
    portfolio_df.loc[idx, "capital_ret"] = capital_ret
    portfolio_df.loc[idx, "mult x ret"] = (portfolio_df.loc[idx, "capital"]/portfolio_df.loc[0, "capital"])
    return day_pnl, capital_ret

class Alpha():
    def __init__(self, insts, dfs, start, end):
        self.insts = insts
        self.dfs = deepcopy(dfs)
        self.period_start = start
        self.period_end = end

    def init_portfolio_settings(self, trade_range):
        dates_to_remove = to_datetime(["2021-12-31", "2022-12-31", "2023-12-31"])
        portfolio_df = pd.DataFrame(index=trade_range).\
            reset_index().\
            rename(columns={"index": "datetime"})
        index_mask = portfolio_df['datetime'].dt.date.isin(dates_to_remove.date)
        indices = portfolio_df.loc[index_mask].index.tolist()
        portfolio_df.drop(indices, inplace=True)
        portfolio_df.loc[0, "capital"] = 10000
        portfolio_df.reset_index(drop=True, inplace=True)
        for inst in self.insts:
            portfolio_df["{} units".format(inst)] = 0
            portfolio_df["{} w".format(inst)] = 0

        return portfolio_df

    def compute_meta_info(self, trade_range):
        for inst in self.insts:
            inst_df = self.dfs[inst]
            self.dfs[inst]["x-y values"] = (inst_df["low"]/inst_df["close"] + inst_df["high"]/inst_df["open"])/2
            self.dfs[inst]["alpha"] = self.dfs[inst]["x-y values"].diff(periods=3)
            self.dfs[inst]["ret"] = self.dfs[inst]["close"]/self.dfs[inst]["close"].shift(1) + -1
            self.dfs[inst]["vol"] = (self.dfs[inst]["close"]/self.dfs[inst]["close"].shift(1) + -1).rolling(5).std()
            self.dfs[inst]["cret"] = (1 + self.dfs[inst]["ret"]).cumprod()
            self.dfs[inst]["eligible"] = (self.dfs[inst]["close"] > 0).astype(int) & (~pd.isna(self.dfs[inst]["alpha"]))
        return

    def plot_cumulative_returns(self, portfolio_df):

        plt.figure(figsize=(12, 8))
        selected_insts = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "ADAUSDT", "LTCUSDT", "SOLUSDT"]
        for inst in self.insts:
            if inst in selected_insts:
                inst_df = self.dfs[inst]
                cumulative_returns = (1 + inst_df['ret']).cumprod()
                line = plt.plot(inst_df.index, cumulative_returns, label=inst)
                plt.text(inst_df.index[-1], cumulative_returns.iloc[-1], inst,
                         color=line[-1].get_color(), fontsize=10, verticalalignment='center')

        line = plt.plot(portfolio_df["datetime"], portfolio_df['mult x ret'], label="strategy")

        text_x = portfolio_df["datetime"].values[-1]
        text_y = portfolio_df['mult x ret'].values[-1]
        plt.text(text_x, text_y, 'strategy', fontsize=10, verticalalignment='center')

        plt.ylabel('Cumulative Returns (X Multiple)')
        plt.legend(loc='upper left')
        plt.title("Market-Neutral Alpha")

        frame1 = plt.gca()
        frame1.axes.get_xaxis().set_ticks([])

        plt.show()

    def run_simulation(self):
        date_range = pd.date_range(start=self.period_start, end=self.period_end, freq="D")
        portfolio_df = self.init_portfolio_settings(date_range)
        self.compute_meta_info(date_range)


        print("running simulation")

        for i in portfolio_df.index:
            date = portfolio_df.loc[i, "datetime"]
            eligibles = [inst for inst in self.insts if self.dfs[inst].loc[date, "eligible"]]
            non_eligibles = [inst for inst in self.insts if inst not in eligibles]

            if i != 0:
                date_prev = portfolio_df.loc[i-1, "datetime"]
                day_pnl, capital_ret = get_pnl_stats(idx=i,
                                                     prev=date_prev,
                                                     portfolio_df=portfolio_df,
                                                     insts=self.insts,
                                                     dfs=self.dfs,
                                                     date=date)

            alpha_scores = {}
            for inst in eligibles:
                alpha_scores[inst] = self.dfs[inst].loc[date, "alpha"]
            alpha_scores = {k:v for k,v in sorted(alpha_scores.items(), key=lambda x: x[1])}
            alpha_long = list(alpha_scores.keys())[-int(len(eligibles)/4):]
            alpha_short = list(alpha_scores.keys())[:int(len(eligibles)/4)]

            for inst in non_eligibles:
                portfolio_df.loc[i, "{} w".format(inst)] = 0
                portfolio_df.loc[i, "{} units".format(inst)] = 0

            nominal_tot = 0
            leverage = 3
            for inst in eligibles:
                forecast = 1 if inst in alpha_long else (-1 if inst in alpha_short else 0)
                dollar_allocation = portfolio_df.loc[i, "capital"] / (len(alpha_long) + len(alpha_short))
                inst_units = (forecast * leverage * dollar_allocation) / self.dfs[inst].loc[date, "close"]
                portfolio_df.loc[i, inst + " units"] = inst_units
                nominal_tot += abs(inst_units * self.dfs[inst].loc[date, "close"])
                nominal_inst = inst_units * self.dfs[inst].loc[date, "close"]
                if nominal_tot != 0:
                    inst_w = nominal_inst / nominal_tot
                else:
                    inst_w = 0
                portfolio_df.loc[i, inst + " w"] = inst_w

            portfolio_df.loc[i, "nominal"] = nominal_tot
            portfolio_df.loc[i, "leverage"] = nominal_tot / portfolio_df.loc[i, "capital"]
            print(portfolio_df.loc[i])
        self.plot_cumulative_returns(portfolio_df=portfolio_df)
        return portfolio_df