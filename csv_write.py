    
def zip_transactions(sess_id, traders):
    # ZIP TRANSACTIONS (buy sell)
    bdump = open('transactions/'+sess_id+'_ZIPMM_transactions.csv', 'w')
    # headers
    bdump.write('%s,%s,%s,%s\n'% ('tid','transaction_type','time','price'))
    for t in traders:
        if traders[t].ttype == 'ZIPMM':
            for transaction in traders[t].transactions:
                # each transaction
                bdump.write('%s,%s,%f,%f\n'% (traders[t].tid, 
                                                    transaction[0], # type
                                                    transaction[1], # time
                                                    transaction[2])) # price
    bdump.close()

def zip_networth(sess_id, traders):
    # ZIP NETWORTH
    bdump = open('networths/'+sess_id+'_ZIPMM_networth.csv', 'w')
    for t in traders:
        if traders[t].ttype == 'ZIPMM':
            # write header file
            bdump.write('%s,%s,%s\n' % ('TID', 'Time', 'Networth'))
            for step in traders[t].networth:
                bdump.write('%s,%f,%f\n' % 
                    (traders[t].tid, step[0], step[1]))
    bdump.close()

def zip_ema(sess_id, traders):
    # ZIP EMA values
    bdump = open('ema/'+sess_id+'_ZIPMM_ema.csv', 'w')
    # headers
    bdump.write('%s,%s,%s\n'% ('tid','time','price'))
    for t in traders:
        if traders[t].ttype == 'ZIPMM':
            for data in traders[t].ema_history:
                # each transaction
                bdump.write('%s,%f,%f\n'% (traders[t].tid, 
                                                data[0], # time
                                                data[1])) # price
    bdump.close()

def zip_job(sess_id, traders):
    # ZIP job history
    bdump = open('job_history/'+sess_id+'_ZIPMM_job_history.csv', 'w')
    # headers
    bdump.write('%s,%s,%s\n'% ('tid','time','new_job'))
    for t in traders:
        if traders[t].ttype == 'ZIPMM':
            for data in traders[t].job_history:
                # each transaction
                bdump.write('%s,%f,%s\n'% (traders[t].tid, 
                                                data[0], # time
                                                data[1])) # job
    bdump.close()

def zip_inventory(sess_id, traders):
    # ZIP inventory history
    bdump = open('inventory_history/'+sess_id+'_ZIPMM_inventory_history.csv', 'w')
    # headers
    bdump.write('%s,%s,%s\n'% ('tid','time','inventory'))
    for t in traders:
        if traders[t].ttype == 'ZIPMM':
            for step in traders[t].inventory_history:
                # each transaction
                bdump.write('%s,%f,%f\n'% (traders[t].tid, 
                                            step[0], # time
                                            step[1])) # inventory
    bdump.close()

def zip_ltt(sess_id, traders):
    # ZIP ltt history
    bdump = open('ltt_history/'+sess_id+'_ZIPMM_ltt_history.csv', 'w')
    # headers
    bdump.write('%s,%s,%s\n'% ('tid','time','predicted_price'))
    for t in traders:
        if traders[t].ttype == 'ZIPMM':
            for step in traders[t].inventory_history:
                # each transaction
                bdump.write('%s,%f,%f\n'% (traders[t].tid, 
                                            step[0], # time
                                            step[1])) # predicted price
    bdump.close()