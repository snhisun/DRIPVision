# app.py
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    tickers = request.form.getlist('ticker[]')
    weights = request.form.getlist('weight[]')
    index_symbol = request.form['index']
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    # Convert weights to floats and check if they sum to 100%
    try:
        weights = [float(w) for w in weights]
    except ValueError:
        return "Error: Please enter valid weights."

    if sum(weights) != 100:
        return "Error: Weights must sum to 100%."

    # Prepare data
    try:
        portfolio_df = get_portfolio_data(tickers, weights, start_date, end_date)
    except Exception as e:
        return f"Error: {str(e)}"

    # Calculate portfolio value over time
    initial_investment = 10000
    portfolio_df['Total Portfolio Value'] = portfolio_df.sum(axis=1)

    portfolio_return = ((portfolio_df['Total Portfolio Value'].iloc[-1] - initial_investment) / initial_investment) * 100

    # Prepare graph data
    data = [go.Scatter(x=portfolio_df.index, y=portfolio_df['Total Portfolio Value'], name='Your Portfolio')]

    index_return = None
    index_name = None

    if index_symbol != 'None':
        index_df = get_index_data(index_symbol, start_date, end_date)
        index_df['Index Value'] = index_df['Adj Close'] / index_df['Adj Close'].iloc[0] * initial_investment
        index_return = ((index_df['Index Value'].iloc[-1] - initial_investment) / initial_investment) * 100
        index_name = get_index_name(index_symbol)
        data.append(go.Scatter(x=index_df.index, y=index_df['Index Value'], name=index_name))

    graphJSON = json.dumps({'data': data, 'layout': {'title': 'Portfolio vs Index'}}, default=str)

    return render_template('result.html', graphJSON=graphJSON, portfolio_return=round(portfolio_return, 2),
                           index_return=round(index_return, 2) if index_return else None, index_name=index_name)

def get_portfolio_data(tickers, weights, start_date, end_date):
    initial_investment = 10000
    investment_amounts = [initial_investment * (weight / 100) for weight in weights]

    # Create a date range for the entire period
    date_range = pd.date_range(start=start_date, end=end_date)

    portfolio_values = pd.DataFrame(index=date_range)

    for ticker, weight, investment in zip(tickers, weights, investment_amounts):
        stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False, actions=True)
        if stock_data.empty:
            raise Exception(f"Ticker {ticker} has no data for the given period.")

        # Get price and dividend data
        price_data = stock_data['Adj Close']
        dividend_data = stock_data[stock_data['Dividends'] > 0]['Dividends']

        # Simulate dividend reinvestment
        shares = investment / price_data.iloc[0]
        total_shares = shares.copy()

        for date in price_data.index[1:]:
            if date in dividend_data.index:
                # Reinvest dividends
                dividend = dividend_data.loc[date]
                dividend_amount = total_shares.loc[date - pd.Timedelta(days=1)] * dividend
                additional_shares = dividend_amount / price_data.loc[date]
                total_shares.loc[date] = total_shares.loc[date - pd.Timedelta(days=1)] + additional_shares
            else:
                total_shares.loc[date] = total_shares.loc[date - pd.Timedelta(days=1)]

        # Calculate investment value over time
        investment_values = total_shares * price_data
        investment_values = investment_values.reindex(date_range).fillna(method='ffill')
        portfolio_values[ticker] = investment_values

    return portfolio_values

def get_index_data(symbol, start_date, end_date):
    df = yf.download(symbol, start=start_date, end=end_date, progress=False)
    if df.empty:
        raise Exception(f"Index {symbol} has no data for the given period.")
    return df

def get_index_name(symbol):
    index_names = {
        '^GSPC': 'S&P 500',
        '^NDX': 'Nasdaq 100',
        '^DJI': 'Dow Jones Industrial Average',
        '^RUT': 'Russell 2000'
    }
    return index_names.get(symbol, 'Index')

if __name__ == '__main__':
    app.run(debug=True)
