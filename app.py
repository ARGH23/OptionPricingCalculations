from flask import Flask, render_template, request
from calculations import price_option

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None

    if request.method == "POST":
        stock = request.form["stock"]
        option_type = request.form["option_type"]
        strike = float(request.form["strike"])
        maturity = int(request.form["maturity"])

        result = price_option(stock, option_type, strike, maturity)

    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
