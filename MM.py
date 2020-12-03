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

        # trader inventory
        self.inventory = 0
        self.MIN_INVENTORY = 0
        self.MAX_INVENTORY = 3

        # Exponential Moving Average
        self.eqlbm = None
        self.nLastTrades = 5
        self.ema_param = 2 / float(self.nLastTrades + 1)

        # Linear Regression Long Term Trend
        self.ltt = LR_LTT()
    
    def generate_order(self, time, countdown, lob):
        # choose order type based on LTT
        quoteprice = self.get_quoteprice(time, lob, self.job)
        if (quoteprice == None): return

        quoteprice = int(round(quoteprice))
        quantity = 1 # hard coded as this version of BSE does not support order quantites
        new_order = BSE.Order(self.tid, self.job, quoteprice, quantity, time, lob['QID'])
        
        return new_order

    def get_quoteprice(self, time, lob, otype):
        if (self.ltt.history_length < self.nLastTrades): # check if ema has built up enough history
            print("funky price sent")
            if (otype == 'Bid'): # CHANGE to best possible price
                quoteprice = 69
            elif (otype == 'Ask'):
                quoteprice = 69
            else: 
                print("wrong otype:", otype)
                exit(1)

        else:
            # returns None if regression is not fitted
            quoteprice = float(self.ltt.predict_price(time))
        return quoteprice

    # called by the market session
    def getorder(self, time, countdown, lob):

        # decide the job type for the order and update regression
        self.job = self.ltt.decide_job(time, self.eqlbm)

        # check there is sufficient inventory
        if (self.job == 'Ask'):
            if (self.inventory <= self.MIN_INVENTORY):
                self.job = None
                # print("insufficent inventory")
                return None
        elif (self.job == 'Bid'):
            if (self.inventory > self.MAX_INVENTORY):
                self.job = None
                print("inventory capped")
                return None  

        # print("ZIPMM about to generate order")
        customer_order = self.generate_order(time, countdown, lob) # generate an order using ltt as a limit price
        if customer_order == None:
            return None
        # add to orders
        self.orders = [customer_order]
        # print("customer order:", self.orders[0])

        lob_order = super().getorder(time, countdown, lob) # refine the order with ZIP (makes more passive?)
        # print("lob order:", lob_order)
        return lob_order

    def update_eq(self, price):
        # Updates the equilibrium price estimate using EMA
        if self.eqlbm == None: self.eqlbm = price
        else: self.eqlbm = self.ema_param * price + (1 - self.ema_param) * self.eqlbm

    def respond(self, time, lob, trade, verbose):
        if (trade != None):
            self.update_eq(trade["price"]) # update EMA
            self.ltt.append_data(time, trade["price"])# update LTT

        # ZIP black box         
        super().respond(time, lob, trade, verbose)

    def bookkeep(self, trade, order, verbose, time):

        outstr = ""
        for order in self.orders:
            outstr = outstr + str(order)
            
        self.blotter.append(trade) # add trade record to trader's blotter
        # NB What follows is **LAZY** -- it assumes all orders are quantity=1
        transactionprice = trade['price']
        
        bidTrans = True #did I buy? (for output logging only)
        self.active = False # no current orders on the exchange

        if(len(self.orders) != 1):
            print("orders:", self.orders)

        if self.orders[0].otype == 'Bid':
            # Bid order succeeded, remember the price and adjust the balance 
            self.inventory += 1
            self.balance -= transactionprice
            self.last_purchase_price = transactionprice
        elif self.orders[0].otype == 'Ask':
            bidTrans = False # we made a sale (for output logging only) # Sold! put the money in the bank
            self.inventory -= 1
            self.balance += transactionprice
            self.last_purchase_price = 0
        else:
            sys.exit('FATAL: ZIPMM doesn\'t know .otype %s\n' %
                    self.orders[0].otype)

        self.n_trades += 1

        verbose = True # We will log to output

        if verbose: # The following is for logging output to terminal 
            if bidTrans: # We bought some shares
                outcome = "Bght"
            else:        # We sold some shares
                outcome = "Sold"
                
            net_worth = self.balance + self.last_purchase_price 
            print('Type=%s; %s, %s=%d; Qty=%d; Balance=%d, NetWorth=%d' %
                (self.ttype, outstr, outcome, transactionprice, 1, self.balance, net_worth)) 
        
        self.del_order(order) # delete the order


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
            print('Type=%s; %s, %s=%d; Qty=%d; Balance=%d, NetWorth=%d' %
                (self.ttype, outstr, outcome, transactionprice, owned, self.balance, net_worth)) 
        
        self.del_order(order) # delete the order

class LR_LTT(): # Linear Regression - Long Term Trend
    """ Analyses the market to choose trader job. """
    
    def __init__(self):
        self.transaction_times = []
        self.transaction_prices = []
        self.history_length = 0
        self.regression = linear_model.LinearRegression()
        self.r_fitted = False
        self.needs_update = False

    def fit_regression(self):
        # if there is insufficient data to regress => self.r_fitted = False
        if (self.transaction_prices == [] or self.transaction_times == []): return
        self.regression.fit(self.transaction_times, self.transaction_prices)
        self.r_fitted = True
        self.needs_update = False
        # print("New coefficient: %.1f" % self.regression.coef_)
        # print("New intercept: %.1f" % self.regression.intercept_)

    def append_data(self, time, price):
        self.transaction_times.append([time])
        self.transaction_prices.append(price)
        self.needs_update = True
        self.history_length += 1

    def predict_price(self, time):
        self.fit_regression()
        if (self.r_fitted == False): return None
        return self.regression.predict([[time]])

    def decide_job(self, time, market_price_equilibrium):
        self.fit_regression()
        if (self.r_fitted == False or
                market_price_equilibrium > self.regression.predict([[time]])): return "Ask"
        else: return "Bid"
        