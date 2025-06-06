# Trade Strategy Testing

This project provides a framework for developing, testing, and analyzing trading strategies. It is designed to help traders and developers evaluate the performance of various strategies using historical market data.
It currently allows for MACD, RSI, Bollinger Bands and Moving average testing, being flexible enough to allow for different buy and sell strategies.

## Example Results

[Results CSV](https://github.com/aeneteoenedot/trade-strategy-testing/blob/ed7d0bc22439721900073a7e655dcfb61dfadf18/backtesting_results.csv)

[Results PDF](https://github.com/aeneteoenedot/trade-strategy-testing/blob/ed7d0bc22439721900073a7e655dcfb61dfadf18/backtesting_results.pdf)

## Features

- Backtesting of trading strategies with customizable parameters
- Performance metrics and analytics
- Support for multiple data sources and formats
- Modular design for easy strategy integration

## Limitations

- Does not support real-time trading or live data feeds
- Backtest results depend on the quality and completeness of historical data
- Limited support for advanced order types and broker integrations
- No built-in risk management or portfolio optimization features
- Requires Python knowledge to develop and integrate custom strategies

## Getting Started

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/trade-strategy-testing.git
    ```
2. Install dependencies:
    ```bash
    cd trade-strategy-testing
    # Install required packages (update as needed)
    pip install -r requirements.txt
    ```
3. Run a sample backtest:
    ```bash
    python main.py --strategy example_strategy --data data/sample.csv
    ```

## Usage

- Add your custom strategies in the `strategies/` directory.
- Configure backtest parameters in the configuration file or via command-line arguments.
- View results and analytics in the `results/` directory.

## Contributing

Contributions are welcome! Please open issues or submit pull requests for improvements.

## License

This project is licensed under the MIT License.
