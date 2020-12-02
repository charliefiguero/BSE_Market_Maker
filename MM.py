import numpy as np
from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score

import BSE

# self.ttype = ttype  # what type / strategy this trader is
# self.tid = tid  # trader unique ID code
# self.balance = balance  # money in the bank
# self.blotter = []  # record of trades executed
# self.orders = []  # customer orders currently being worked (fixed at 1)
# self.n_quotes = 0  # number of quotes live on LOB
# self.birthtime = time  # used when calculating age of a trader/strategy
# self.profitpertime = 0  # profit per unit time
# self.n_trades = 0  # how many trades has this trader done?
# self.lastquote = None  # record of what its last quote was

class Trader_ZIPMM(BSE.Trader_ZIP):

    def __init__(self, ttype, tid, balance, time):
        super().__init__(ttype, tid, balance, time)
        self.eqlbm = None
        self.ltt = LTT()
    
    def generate_order(self):
        new_order = BSE.Order(self.tid, "Buy", 100, 1, self.birthtime, 69696969)
        print()
        print("Generated order: %s" %new_order)

    def getorder(self, time, countdown, lob):
        # generate_order()
        super().getorder(time, countdown, lob)

    def update_eq(self, price):
        # Updates the equilibrium price estimate using EMA
        if self.eqlbm == None: self.eqlbm = price
        else: self.eqlbm = self.ema_param * price + (1 - self.ema_param) * self.eqlbm

    def respond(self, time, lob, trade, verbose):
        super().respond(time, lob, trade, verbose)
        
        # if transaction:
            # # update LTT
            # update_eq(trade.price) # update EMA
            

class Trader_DIMM01(BSE.Trader):

    def __init__(self, ttype, tid, balance, time):

        super().__init__(ttype, tid, balance, time) # initialise Trader superclass

        # below are new variables for the DIMM only (they are not in the superclass) 
        self.job = 'Buy' # flag switches between 'Buy' & 'Sell' to show what DIMM does next 
        self.last_purchase_price = None # we haven't traded yet so set null
        self.bid_delta = 1 # how much (absolute value) to improve on best ask when buying 
        self.ask_delta = 5 # how much (absolute value) to improve on purchase price

    # the following is just a copy of GVWY's getorder method
    def getorder(self, time, countdown, lob):
        if len(self.orders) < 1:
            order = None
        else:
            quoteprice = self.orders[0].price
            self.lastquote = quoteprice
            order=BSE.Order(self.tid,
                        self.orders[0].otype,
                        quoteprice,
                        self.orders[0].qty,
                        time,lob['QID'])
        return order

    def respond(self, time, lob, trade, verbose):
        # DIMM buys and holds, sells as soon as it can make a "decent" profit 
        if self.job == 'Buy':
            # see what's on the LOB
            if lob['asks']['n'] > 0:
                # there is at least one ask on the LOB
                bestask = lob['asks']['best']
                # try to buy a single unit at price of bestask+biddelta 
                bidprice = bestask + self.bid_delta
                if bidprice < self.balance :
                    # can afford it!
                    # do this by issuing order to self, processed in getorder() 
                    order=BSE.Order(self.tid, 'Bid', bidprice, 1, time, lob['QID']) 
                    self.orders=[order]
                    if verbose : print('DIMM01 Buy order=%s ' % ( order))
        
        elif self.job == 'Sell':
            # is there at least one counterparty on the LOB? 
            if lob['bids']['n'] > 0:
                # there is at least one bid on the LOB
                bestbid = lob['bids']['best']
                # sell single unit at price of purchaseprice+askdelta 
                askprice = self.last_purchase_price + self.ask_delta 
                if askprice < bestbid :
                    # seems we have a buyer
                    # do this by issuing order to self, processed in getorder() 
                    order=BSE.Order(self.tid, 'Ask', askprice, 1, time, lob['QID']) 
                    self.orders=[order]
                    if verbose : print('DIMM01 Sell order=%s ' % ( order))
        else :
            sys.exit('FATAL: DIMM01 doesn\'t know self.job type %s\n' % self.job)

    def bookkeep(self, trade, order, verbose, time):

        outstr = ""
        for order in self.orders:
            outstr = outstr + str(order)
            
        self.blotter.append(trade) # add trade record to trader's blotter
        # NB What follows is **LAZY** -- it assumes all orders are quantity=1
        transactionprice = trade['price']
        
        bidTrans = True #did I buy? (for output logging only) 
        if self.orders[0].otype == 'Bid':
            # Bid order succeeded, remember the price and adjust the balance 
            self.balance -= transactionprice
            self.last_purchase_price = transactionprice
            self.job = 'Sell' # now try to sell it for a profit
        elif self.orders[0].otype == 'Ask':
            bidTrans = False # we made a sale (for output logging only) # Sold! put the money in the bank
            self.balance += transactionprice
            self.last_purchase_price = 0
            self.job = 'Buy' # now go back and buy another one
        else:
            sys.exit('FATAL: DIMM01 doesn\'t know .otype %s\n' %
                    self.orders[0].otype)

        self.n_trades += 1

        verbose = True # We will log to output

        if verbose: # The following is for logging output to terminal 
            if bidTrans: # We bought some shares
                outcome = "Bght"
                owned = 1
            else:        # We sold some shares
                outcome = "Sold"
                owned = 0
                
            net_worth = self.balance + self.last_purchase_price 
            print('%s, %s=%d; Qty=%d; Balance=%d, NetWorth=%d' %
                (outstr, outcome, transactionprice, owned, self.balance, net_worth)) 
        
        self.del_order(order) # delete the order

class LTT():
    """ Analyses the market to send out buy or sell orders. """
    
    def __init__(self):
        transaction_times = np.reshape(np.arange(5), (-1,1))
        transaction_prices = np.arange(5) * 2
        regression = linear_model.LinearRegression()
        regression.fit(transaction_times, transaction_prices)
    
    def fit_regression(self):
        regression.fit(transaction_times, transaction_prices)
        print("Coefficients: %.1f" % regression.coef_)
        print("Intercept: %.1f" % regression.intercept_)

    def decide_order_type(self, time, market_price_equilibrium):
        if (market_price_equilibrium > regression.predict[[time]]):
            return "Sell"
        else: return "Buy"
        