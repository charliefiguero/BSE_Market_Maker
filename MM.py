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

        # staleness checks
        self.order_age = 0
        self.MAX_ORDER_AGE = 100

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

        self.job = 'Bid'

        # logging data
        self.times = []
        self.networth = []
    
    def get_quoteprice(self, time, otype): # none
        if self.ltt.history_length < self.nLastTrades or self.eqlbm == None: # check if ema has built up enough history
            return self.get_stub_price(otype)
        else:
            if self.eqlbm == None:
                print("Error: quoteprice == None")
                exit(1)
            return float(self.eqlbm) # returns current market average - to be improved by ZIP

    def get_stub_price(self, otype): 
        """ Used to set price that will never be fulfilled. """
        if otype == 'Bid': return BSE.bse_sys_minprice
        elif otype == 'Ask': return BSE.bse_sys_maxprice
        else: 
            print('Error in order type')
            exit(1)

    def generate_order(self, time, lob, otype):
        """ Only called after a respond call. This is important as 
            self.eqlbm must != None """

        # find a baseline quoteprice - currently based on ema
        quoteprice = self.get_quoteprice(time, self.job)

        # balance check - can get stuck trying to buy with no money due to job set in bookkeep
        if self.job == 'Bid':
            if self.balance < quoteprice:
                quoteprice = self.balance

        # create new order
        quoteprice = int(round(quoteprice)) # trader.orders[0] must be better price than market sessions getorder result
        quantity = 1 # hard coded as this version of BSE does not support order quantites
        new_order = BSE.Order(self.tid, self.job, quoteprice, quantity, time, lob['QID'])
        
        # add order to orders
        self.add_order(new_order, verbose=False)

    def update_eq(self, price):
        # Updates the equilibrium price estimate using EMA
        if self.eqlbm == None: self.eqlbm = price
        else: self.eqlbm = self.ema_param * price + (1 - self.ema_param) * self.eqlbm

    def calculate_networth(self):
        if (self.inventory <= 0): return self.balance
        return self.balance + (self.inventory * self.eqlbm)

    def decide_by_inventory(self):
        # decide job by inventory constraints
        if self.inventory == self.MAX_INVENTORY:
            return 'Ask'
        elif self.inventory == self.MIN_INVENTORY:
            return 'Bid'
        else:
            return 'None'

    def decide_by_ltt(self, time, market_price_equilibrium):
        # decide by LTT
        self.ltt.fit_regression()
        if (self.ltt.r_fitted == False or
                market_price_equilibrium < self.ltt.predict_price(time)): return "Bid"
        else: return "Ask"

    # can only be called in bookkeep
    def decide_job(self, time, market_price_equilibrium):
        """ Changes the order type of the MM trader. """

        # force job if constrained by inventory
        inventory_choice = self.decide_by_inventory()
        if inventory_choice != 'None': return inventory_choice

        # decide by LTT
        return self.decide_by_ltt(time, market_price_equilibrium)

    # called by the market session
    def getorder(self, time, countdown, lob):
        
        # check that the market conditions still match job.
        # if job was force set by inventory, this will stop unfavourable trades going through
        if self.decide_by_ltt(time, self.eqlbm) != self.job:
            # send stub order if you don't want to trade
            quantity = 1
            return BSE.Order(self.tid, self.job, self.get_stub_price(self.job), 
                                quantity, time, lob['QID'])

        # refine order with ZIP
        lob_order = super().getorder(time, countdown, lob)

        # if (len(self.orders) == 1): 
        #     print("equilibrium:",self.eqlbm,"; order:",self.orders[0],"; lob order:", lob_order)
        return lob_order # can change price on BSE but not otype

    # called by the market session
    def respond(self, time, lob, trade, verbose):
        self.order_age += 1
        
        if (trade != None):
            self.update_eq(trade["price"]) # update EMA
            self.ltt.append_data(time, trade["price"])# update LTT
 
        # if no orders, generate one
        if len(self.orders) < 1:
            self.generate_order(time, lob, self.job)
            # if len(self.orders) == 1:
            #     print("generated new order (previously empty):", self.orders[0])
            self.order_age = 0

        # order staleness check
        if (self.order_age > self.MAX_ORDER_AGE):
            self.generate_order(time, lob, self.job)
            # if len(self.orders) == 1:
            #     print("generated new order (stale):", self.orders[0])
            self.order_age = 0

        # ZIP black box.
        if (self.price != None):
            super().respond(time, lob, trade, verbose)

        # save networth for logging
        self.times.append(time)
        self.networth.append(self.calculate_networth())

    # called by the market session
    def bookkeep(self, trade, order, verbose, time):
        outstr = ""
        for order in self.orders:
            outstr = outstr + str(order)
            
        self.blotter.append(trade) # add trade record to trader's blotter
        # NB What follows is **LAZY** -- it assumes all orders are quantity=1
        transactionprice = trade['price']
        
        bidTrans = True #did I buy? (for output logging only)
        self.active = False # no current orders on the exchange

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

        verbose = True
        if verbose: # The following is for logging output to terminal 
            if bidTrans: outcome = "Bght"    # we bought some shares
            else:        outcome = "Sold"    # We sold some shares
                
            net_worth = self.balance + self.last_purchase_price 
            print('Type=%s; Order=%s; %s=%d; Inventory=%d; Balance=%d, NetWorth=%d' %
                (self.ttype, outstr, outcome, transactionprice, self.inventory, self.balance, self.calculate_networth())) 
        
        # delete the order
        self.del_order(order) 

        # Decides job of next order. Must be done here because of structure of BSE
        self.job = self.decide_job(time, self.eqlbm)

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
        self.r_fitted = False # has the model ever been fitted
        self.needs_update = False # is the model out of date

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

        