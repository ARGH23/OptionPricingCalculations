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
    

    #doing this now for convenience and safety
    x_points = []
    y_points = []

    for maturity_len, ticker in tickers[country].items():
        y = safe_last_yield(ticker)
        if y is not None:
            x_points.append(maturity_len)
            y_points.append(y)

    # If nothing worked, fallback
    if not x_points:
        return get_risk_free_rate("US", maturity)

    mini = x_points[0]
    maxi = x_points[-1]


    #defined rate
    if maturity in x_points:
        return y_points[x_points.index(maturity)]


    #least square solution
    elif maturity < mini or len(x_points) == 1:
        x = np.array(x_points)
        y = np.array(y_points)

        gradient = np.cov(x, y, bias=True)[0, 1] / np.var(x)
        intercept = y.mean() - gradient * x.mean()

        return gradient * maturity + intercept


    #linear interpolation case 1
    elif maturity > maxi:
        x1, x2 = x_points[-2], x_points[-1]
        y1, y2 = y_points[-2], y_points[-1]

        gradient = (y2 - y1) / (x2 - x1)
        intercept = y1 - gradient * x1

        return gradient * maturity + intercept


    #linear interpolation case 2
    else:
        for i in range(len(x_points) - 1):
            if x_points[i] < maturity < x_points[i + 1]:
                x1, x2 = x_points[i], x_points[i + 1]
                y1, y2 = y_points[i], y_points[i + 1]

                gradient = (y2 - y1) / (x2 - x1)
                intercept = y1 - gradient * x1

                return gradient * maturity + intercept







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
