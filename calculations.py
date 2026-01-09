import numpy as np
import yfinance as yf
from scipy.stats import norm
from datetime import datetime

def black_scholes(option_type, sigma, K, S, T, r):
    """
    Black-Scholes option pricing model
    """
    d1 = (np.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "call":
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    return price


# For safety
def safe_last_yield(ticker):
    hist = yf.Ticker(ticker).history(period="1mo")
    if hist.empty or "Close" not in hist:
        return None
    return hist["Close"].iloc[-1] / 100


def get_risk_free_rate(country="US", maturity=3):
    print(country)
    tickers = {
        "US": {3: "^IRX", 60: "^FVX", 120: "^TNX"},
        "DE": {120: "^DE10Y"},
        "UK": {120: "^GB10Y"},
        "JP": {12: "^JP1Y", 24: "^JP2Y", 120: "^JP10Y"},
        "CA": {120: "^CA10Y"},
        "AU": {3: "^AU3M", 120: "^AU10Y"},
        "CH": {12: "^CH1Y", 120: "^CH10Y"}
    }

    country_map = {
        "United States": "US",
        "Germany": "DE",
        "United Kingdom": "UK",
        "Japan": "JP",
        "Canada": "CA",
        "Australia": "AU",
        "Switzerland": "CH"
    }

    if country not in tickers:
        if country in country_map:
            country = country_map[country]
        else:
            country = "US"
    
    print(country)
    
    all_lens = []
    for i in tickers[country]:
        all_lens.append(i)
    all_lens = sorted(all_lens)
    mini = all_lens[0]
    maxi = all_lens[-1]

    if (maturity in tickers[country]):
        ticker = tickers[country][maturity]
        data = yf.Ticker(ticker).history()
        return data["Close"].iloc[-1] / 100
    
    elif maturity < mini or len(all_lens) == 1:
        total_points = 0
        xsum = 0
        ysum = 0
        xysum = 0
        x2sum = 0

        for i in tickers[country]:
            xp = i
            ticker = tickers[country][i]
            yp = (yf.Ticker(ticker).history())["Close"].iloc[-1] / 100

            total_points += 1
            xsum += xp
            ysum += yp
            xysum += xp*yp
            x2sum += xp**2
        
        gradient = (total_points * xysum - xsum * ysum)/(total_points * x2sum - (xsum)**2)
        b = (ysum - gradient*xsum)/total_points
        return gradient*maturity + b

    elif maturity > maxi:
        d1x = all_lens[-2]
        ticker = tickers[country][d1x]
        d1y = (yf.Ticker(ticker).history())["Close"].iloc[-1] / 100

        d2x = all_lens[-1]
        ticker = tickers[country][d2x]
        d2y = (yf.Ticker(ticker).history())["Close"].iloc[-1] / 100

        gradient = (d2y - d1y)/(d2x - d1x)
        b = d1y - gradient*d1x
        return gradient * maturity + b

    else:
        small_term = 0
        big_term = 1

        while (maturity > all_lens[big_term]):
            small_term += 1
            big_term += 1
        
        d1x = all_lens[small_term]
        ticker = tickers[country][d1x]
        d1y = (yf.Ticker(ticker).history())["Close"].iloc[-1] / 100

        d2x = all_lens[big_term]
        ticker = tickers[country][d2x]
        d2y = (yf.Ticker(ticker).history())["Close"].iloc[-1] / 100

        gradient = (d2y - d1y)/(d2x - d1x)
        b = d1y - gradient*d1x
        return gradient * maturity + b







def price_option(stock_name, option_type, K, T_months):
    # Risk-free rate (3-month T-bill)
    info = yf.Ticker(stock_name).info
    if "country" in info and info["country"]:
        r = get_risk_free_rate(info["country"],T_months)
    else:
        r = get_risk_free_rate("US",T_months)

    # Stock price history
    prices = yf.Ticker(stock_name).history(start=datetime(2019, 1, 1))["Close"]
    returns = np.log(prices / prices.shift())
    sigma = returns.std() * np.sqrt(252)

    S = prices.iloc[-1]
    T = T_months / 12

    option_price = black_scholes(option_type, sigma, K, S, T, r)

    return {
        "stock": stock_name,
        "current_price": round(S, 2),
        "strike_price": K,
        "time_months": T_months,
        "risk_free_rate": round(r * 100, 2),
        "option_price": round(option_price, 2),
        "type": option_type.capitalize()
    }
