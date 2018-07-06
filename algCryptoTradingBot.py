import time
import datetime
import ccxt


# FUNCTIONS

def get_bid_ask_spread(xchange, symbol):
    # Returns the tuple (highest bid, lowest ask, spread between them)
    time.sleep(1)
    orderbook = xchange.fetch_order_book(symbol)
    time.sleep(1)
    bid = orderbook['bids'][0][0] if len(orderbook['bids']) > 0 else None
    ask = orderbook['asks'][0][0] if len(orderbook['asks']) > 0 else None
    spread = (ask - bid) if (bid and ask) else None
    return bid, ask, spread


def get_optimized_bid_ask_spread(xchange, symbol, amount):
    # returns the bid ask spread but without the orders below the amount to prevent manipulation
    time.sleep(1)
    orderbook = xchange.fetch_order_book(symbol)
    time.sleep(1)
    bids = [x for x in orderbook['bids'] if x[1] >= amount]
    asks = [x for x in orderbook['asks'] if x[1] >= amount]
    #print(bids)
    #print(asks)
    bid = orderbook['bids'][0][0] if len(bids) == 0 else bids[0][0]
    ask = orderbook['asks'][0][0] if len(asks) == 0 else asks[0][0]
    spread = (ask - bid) if (bid and ask) else None
    return bid, ask, spread


def get_faked_bid_ask_spread(xchange, symbol, amount):
    # returns the bid ask spread but without the orders below the amount to prevent manipulation
    time.sleep(1)
    orderbook = xchange.fetch_order_book(symbol)
    time.sleep(1)
    bids = [x for x in orderbook['bids'] if x[1] >= amount]
    asks = [x for x in orderbook['asks'] if x[1] >= amount]
    #print(bids)
    #print(asks)
    bid = orderbook['bids'][0][0] if len(bids) == 0 else bids[0][0]
    ask = orderbook['asks'][0][0] if len(asks) == 0 else asks[0][0]
    mid = (bid + ask) / 2.0
    percentage = 0.02
    bid = (1.0 - percentage) * mid
    ask = (1.0 + percentage) * mid
    spread = (ask - bid) if (bid and ask) else None
    return bid, ask, spread


def get_balances_base_target(xchange, symX, symY):
    # From the xchange and both currencies symX and symY,
    # this function fetches the balance of both
    time.sleep(1)
    balance = xchange.fetch_balance({'recvWindow': 10000000})
    time.sleep(1)
    # print(balance)
    bal_base = balance[symX]['free'] if symX in balance else 0.0
    bal_target = balance[symY]['free'] if symY in balance else 0.0
    return bal_base, bal_target


def get_fee(xchange, amount, price):
    # only for southxchange currently
    return amount * price * 0.001


def sell_point_heuristic(xchange, amount, price, fee, balanceTarget):
    if amount <= 0:
        return False
    if fee > amount * price * 0.1:
        # Fee is larger than 10%, do not trade
        return False
    if amount * price < 0.002:
        return False
    return True


def buy_point_heuristic(xchange, amount, price, fee, balanceBase):
    if amount <= 0:
        return False
    if fee > amount * price * 0.1:
        # Fee is larger than 10%, do not trade
        return False
    if amount * price < 0.002:
        return False
    return True

# VARIABLES

symbol_base = "BTC"
symbol_target = "ADA"
symbol = symbol_target + "/" + symbol_base

xchange = ccxt.binance({
    'apiKey': 'YOUR API KEY HERE',
    'secret': 'YOUR SECRET HERE',
})
time.sleep(1)
markets = xchange.load_markets()
time.sleep(1)
print(markets.keys())
print(xchange.id)
print(markets[symbol])

lastBuyPrice = 0

# CODE

# start with selling and then play ping pong
sell_time = False
minimal_target_coins = 0.0 # the last amount of target coins to keep (e.g. GRT)
minimal_base_coins = 0.0 # the last amount of base coins to keep (e.g. BTC)

# the fraction of coins from balance that can be maximally spent:
alpha = 0

while True:
    try:
        print("sleep...")
        time.sleep(10)
        print("... let's make some coins.")
        print(datetime.datetime.now())

        # current balances --> strong monotonic increase
        balanceBase, balanceTarget = get_balances_base_target(xchange, symbol_base, symbol_target)
        minimal_target_coins = max(minimal_target_coins, alpha * balanceTarget)
        minimal_base_coins = max(minimal_base_coins, alpha * balanceBase)
        print(symbol_base + ": " + str(balanceBase) + "; keep minimal: " + str(minimal_base_coins))
        print(symbol_target + ": " + str(balanceTarget) + "; keep minimal: " + str(minimal_target_coins))

        # The percentage in [0,1] we improve the currently best ask/bid
        # arbitrageReduction = 0.01
        if sell_time:
            # do selling target coin (e.g. GRT)
            # amount = min(balanceTarget - minimal_target_coins, 0.3 * balanceTarget)
            amount = min(balanceTarget - minimal_target_coins, balanceTarget)
            amount = max(0, amount)

            # current spread
            bid, ask, spread = get_faked_bid_ask_spread(xchange, symbol, amount)
            print("Bid" + str(bid))
            print("Ask" + str(ask))
            print("Spread" + str(spread))
            mid = (bid + ask) / 2.0

            # price = (1.0 - arbitrageReduction) * ask
            price = (mid + ask) / 2.0
            price = max(mid, price)

            # sell for at least last buy price
            price = max(lastBuyPrice, price)

            fee = get_fee(xchange, amount, price)
            print("Fee: " + str(fee))
            if sell_point_heuristic(xchange, amount, price, fee, balanceTarget):
                print("Sell " + str(amount) + " " + symbol_target + " for " + str(price))
                xchange.create_limit_sell_order(symbol, amount, price)
            else:
                print("Skip selling " + str(amount) + " " + symbol_target + " for " + str(price))
            sell_time = False
        else:
            # do buying target coin (e.g. GRT)
            # amountBaseCoins = min(balanceBase - minimal_base_coins, 0.3 * balanceBase)
            amountBaseCoins = min(balanceBase - minimal_base_coins, balanceBase)
            amountBaseCoins = max(amountBaseCoins, 0) # e.g. BTC
            # estimate amount using bid price
            amount = amountBaseCoins / get_bid_ask_spread(xchange, symbol)[0]

            # current spread
            bid, ask, spread = get_faked_bid_ask_spread(xchange, symbol, amount)
            print("Bid" + str(bid))
            print("Ask" + str(ask))
            print("Spread" + str(spread))
            mid = (bid + ask) / 2.0

            #price = (1.0 + arbitrageReduction) * bid
            price = (bid + mid) / 2.0
            price = min(mid, price)

            # update amount using real price
            amount = amountBaseCoins / price

            fee = get_fee(xchange, amount, price)
            if buy_point_heuristic(xchange, amount, price, fee, balanceBase):
                print("Buy" + str(amount) + " " + symbol_target + " for " + str(price))
                lastBuyPrice = price
                xchange.create_limit_buy_order(symbol, amount, price)
            else:
                print("Skip buying" + str(amount) + " " + symbol_target + " for " + str(price))
            sell_time = True
    except (ccxt.errors.RequestTimeout, ccxt.errors.NetworkError, ccxt.errors.InvalidOrder):
        print("There was an error with network or timeout -- skipped this execution!")
        time.sleep(100)
    except (ccxt.errors.InvalidOrder):
        print("Invalid Order: " + str(amount) + " coins for " + str(price))
        time.sleep(100)
    except (ccxt.errors.ExchangeError):
        print("There was an exchange error!")
        time.sleep(100)
