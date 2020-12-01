import BSE

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
