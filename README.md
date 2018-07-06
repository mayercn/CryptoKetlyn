# CryptoKetlyn
This is a simple Python cryptocurrency trading bot that tries to exploit arbitrage opportunities between two crpytocurrencies.

1) Install the Python package [ccxt](https://github.com/ccxt/ccxt). This should be as simple as typing the following command into your console:
  
```
pip install ccxt
```
  
2) Create an account at a supported exchange as listed [here](https://github.com/ccxt/ccxt). This bot uses a binance account. You have to create an API key as well. Find a guide how to do this for binance [here](https://support.binance.com/hc/en-us/articles/360002502072-How-to-create-API). Then insert the created API key and the secret into the script. Search for the following code snippet:

```
xchange = ccxt.binance({
    'apiKey': 'YOUR API KEY HERE',
    'secret': 'YOUR SECRET HERE',
})
```

3) Adapt the trading algorithm of the bot to your needs (e.g. parameters, cryptocurrencies, etc.). The given implementation is only an example algorithm. Of course, we do not guarantee any performance of this bot. USE THE BOT AT YOUR OWN RISK and start with a small amount in your account for testing. 

4) Only then, run the script.


Hope you have fun!
