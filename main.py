
#   This script provides a framework for backtesting trading strategies using historical market data from Polygon.io.
#   It includes modules for loading strategy configurations, fetching and processing market data, computing technical indicators,
#   generating trading signals, simulating trades with risk management (stop loss and take profit), and generating PDF reports of results.
#   Modules and Functions:
#   - simulate_trades_with_risk(df, initial_cash=1000000, config={}):
#       Simulates trading based on buy/sell signals, with stop loss and take profit risk management.
#       Allocates all available cash to new positions and exits on signal, stop loss, or take profit.
#   - compute_indicators(df, config):
#       Computes technical indicators (moving averages, RSI, MACD, Bollinger Bands) for each ticker in the DataFrame.
#   - load_strategy_config(json_path: str):
#       Loads and parses a strategy configuration from a JSON file, extracting parameters for strategy logic, risk management, and capital allocation.
#   - get_credentials():
#       Loads API credentials from a local 'credentials.json' file.
#   - get_polygon_data(config):
#       Fetches historical aggregated bar data for specified tickers from Polygon.io using the provided configuration.
#   - evaluate_signals(df, logic):
#       Evaluates buy and sell signals for each ticker based on the strategy logic provided in the configuration.
#   - Main script execution:
#       Loads strategy configuration, fetches and processes data, computes indicators, evaluates signals, simulates trades,
#       saves results to CSV, and generates a PDF report.
#   Dependencies:
#   - polygon (Polygon.io API client)
#   - pandas
#   - ta (Technical Analysis library)
#   - json
#   - datetime
#   - pdfgen (custom PDF report generator)

# Imports
from polygon import RESTClient
import pandas as pd
import json
from datetime import datetime
import ta  # for technical indicators
from pdfgen import generate_pdf_report

# --- Trade Simulation with Risk Management ---
def simulate_trades_with_risk(df, initial_cash=1000000, config={}):
    """
    Simulates trading with stop loss and take profit.
    - Expects signals and prices in df.
    - Allocates all available cash to a new position.
    - Known limitations is a lack of a rebalancing methodology.
    - Exits on signal, stop loss, or take profit.
    """
    stop_loss_pct = config['risk']['stop_loss']
    take_profit_pct = config['risk']['take_profit']

    df = df.sort_values(['timestamp', 'ticker'])
    held_positions = {}
    trades = []
    cash = initial_cash

    for idx, row in df.iterrows():
        date = row['timestamp']
        ticker = row['ticker']
        signal = row['signal']
        current_price = row['close']

        # Exit logic: check for sell signal, stop loss, or take profit
        if ticker in held_positions:
            position = held_positions[ticker]
            pnl_pct = (current_price - position['entry_price']) / position['entry_price']
            stop_loss_hit = pnl_pct <= -stop_loss_pct
            take_profit_hit = pnl_pct >= take_profit_pct

            if signal == -1 or stop_loss_hit or take_profit_hit:
                exit_price = current_price
                pnl = pnl_pct * position['cash']
                trades.append({
                    'ticker': ticker,
                    'entry_datetime': position['entry_datetime'],
                    'exit_datetime': date,
                    'entry_price': round(position['entry_price'], 4),
                    'exit_price': round(exit_price, 4),
                    'return_pct': round(pnl_pct * 100, 4),
                    'pnl': round(pnl, 2),
                    'allocated_cash': round(position['cash'], 2),
                    'shares': round(position['shares'], 4),
                    'holding_ticks': (date - position['entry_datetime']).total_seconds() / (15 * 60),
                    'exit_reason': (
                        'Strategy logic' if signal == -1 else 
                        'Stop loss raised' if stop_loss_hit else 
                        'Stop gain raised'
                    )
                })
                cash += position['cash'] + pnl
                del held_positions[ticker]

        # Buy logic: only if not already holding and cash available
        if signal == 1 and ticker not in held_positions and cash > 0:
            cash_per_position = cash  # All-in allocation
            position_size = cash_per_position / current_price
            held_positions[ticker] = {
                'entry_price': current_price,
                'entry_datetime': date,
                'cash': cash_per_position,
                'shares': position_size,
            }
            cash -= cash_per_position

    return pd.DataFrame(trades).sort_values(by='entry_datetime')

# --- Indicator Computation ---
def compute_indicators(df, config):
    short_window = config['params'].get('short_window', 20)
    long_window = config['params'].get('long_window', 50)

    def compute_group_indicators(group):
        group = group.sort_index()
        # Moving Averages
        group['short_ma'] = group['close'].rolling(short_window).mean()
        group['long_ma'] = group['close'].rolling(long_window).mean()
        # RSI
        group['rsi'] = ta.momentum.RSIIndicator(close=group['close'], window=14).rsi()
        # MACD
        macd = ta.trend.MACD(close=group['close'])
        group['macd'] = macd.macd()
        group['macd_signal'] = macd.macd_signal()
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(close=group['close'], window=20, window_dev=2)
        group['bb_upper'] = bb.bollinger_hband()
        group['bb_lower'] = bb.bollinger_lband()
        group['bb_middle'] = bb.bollinger_mavg()
        # Round
        cols_to_round = ['short_ma', 'long_ma', 'rsi', 'macd', 'macd_signal', 'bb_upper', 'bb_lower', 'bb_middle']
        group[cols_to_round] = group[cols_to_round].round(4)
        return group

    # Apply per ticker
    df = df.groupby('ticker', group_keys=False).apply(compute_group_indicators, include_groups=True)
    df = df.dropna(subset=['short_ma', 'long_ma'])  # Drop rows with insufficient data
    return df

# --- Strategy Config Loader ---
def load_strategy_config(json_path: str):
    config = json.load(open(json_path))
    # Extract fields from config
    name = config['strategy_name']
    tickers = config['tickers']
    short_window = config['parameters']['short_window']
    long_window = config['parameters']['long_window']
    start_date = datetime.strptime(config['parameters']['start_date'], "%Y-%m-%d")
    end_date = datetime.strptime(config['parameters']['end_date'], "%Y-%m-%d")
    buy_condition = config['logic']['buy_condition']
    sell_condition = config['logic']['sell_condition']
    capital = config.get('capital', 100000)
    rebalance = config.get('rebalance', 'daily')
    sizing_method = config['position_sizing'].get('method', 'equal_weight')
    stop_loss = config['risk_management'].get('stop_loss_pct', 0.05)
    take_profit = config['risk_management'].get('take_profit_pct', 0.15)

    return {
        "name": name,
        "tickers": tickers,
        "params": {
            "short_window": short_window,
            "long_window": long_window,
            "start_date": start_date,
            "end_date": end_date
        },
        "logic": {
            "buy": buy_condition,
            "sell": sell_condition
        },
        "capital": capital,
        "rebalance": rebalance,
        "sizing": sizing_method,
        "risk": {
            "stop_loss": stop_loss,
            "take_profit": take_profit
        }
    }

# --- Credentials Loader ---
def get_credentials():
    return json.load(open('credentials.json'))['api_key']

# --- Polygon Data Fetcher ---
def get_polygon_data(config):
    client = RESTClient(api_key=get_credentials())
    tickers = config['tickers']
    df_aggs = pd.DataFrame()
    for ticker in tickers:
        aggs = []
        for a in client.list_aggs(ticker=ticker, multiplier=15, timespan="minute",
                                 from_=config['params']['start_date'], to=config['params']['end_date'], limit=50000):
            aggs.append(a)
            _aggs = pd.DataFrame(aggs)
            _aggs['ticker'] = ticker
        df_aggs = pd.concat([df_aggs, _aggs])
    df_aggs['timestamp'] = df_aggs['timestamp'].apply(lambda x: datetime.fromtimestamp(x/1000))
    df_aggs.sort_index(inplace=True)
    return df_aggs

# --- Signal Evaluation ---
def evaluate_signals(df, logic):
    def compute_signals(group):
        group = group.copy()
        group['buy'] = pd.eval(logic['buy'], local_dict=group, engine='python')
        group['sell'] = pd.eval(logic['sell'], local_dict=group, engine='python')
        group['signal'] = 0
        group.loc[group['buy'], 'signal'] = 1
        group.loc[group['sell'], 'signal'] = -1
        return group

    df = df.groupby('ticker', group_keys=False).apply(compute_signals, include_groups=True)
    return df

# --- Main Script ---
if __name__ == '__main__':
    config = load_strategy_config('strategies\strategyexample.json')
    df = compute_indicators(get_polygon_data(config), config)
    df_wIndicators = evaluate_signals(df, config['logic']).reset_index(drop=True)
    sim = simulate_trades_with_risk(df_wIndicators, config['capital'], config)
    sim.to_csv('backtesting_results.csv', index=False)
    generate_pdf_report(sim, config)
