import pandas as pd
import sys
import pdb
import numpy as np


def cancellation_slot(df):
    if df['Cancellation time'] - df['requested_time'] < pd.Timedelta('-1 hours'):
        df['cancel_slot'] = '<t-1hours'
    elif df['Cancellation time'] - df['requested_time'] < pd.Timedelta('-30 minutes'):
        df['cancel_slot'] = '<t-1 to t-.5 hour'
    elif df['Cancellation time'] - df['requested_time'] < pd.Timedelta('0 hours'):
        df['cancel_slot'] = '<t-.5 to t hour'
    elif df['Cancellation time'] - df['requested_time'] <= pd.Timedelta('1 hours'):
        df['cancel_slot'] = '<t-t+1hour'
    elif df['Cancellation time'] - df['requested_time'] <= pd.Timedelta('2 hours'):
        df['cancel_slot'] = 't+1-t+2hour'
    else:
        df['cancel_slot'] = '>t+2 hours'


    return df



def main():
    filename = sys.argv[1]
    #columns_to_use = ['Type','Phone','Email','Customer name','requested_date','Discount amount','Amount','DM credits used','Status','successful_bookings','total_revenue']
    df = pd.read_csv(filename, skiprows = np.arange(1,110000))
    pdb.set_trace()
    df['requested_time'] = df['requested_time'].astype(int).astype(str) + ':00:00'
    df['requested_time'] = pd.to_datetime(df['requested_date'] + ' ' + df['requested_time'])
    df['Cancellation time'] = pd.to_datetime(df['Cancellation time'])
    df['requested_date'] = pd.to_datetime(df['requested_date'])

    df = df.apply(cancellation_slot, axis = 1)

    df[df['Status'] == 'cancelled'].groupby(['City','Booking cancel reason','cancel_slot'])['Booking ID'].count().to_csv('tmp.csv')





if __name__=='__main__':
    main()
