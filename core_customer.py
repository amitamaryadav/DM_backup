import pandas as pd
import sys
import pdb
import numpy as np


def core(df):
    #pdb.set_trace()
    if ((df['frequency'].mean() < 30) & (df['successful_bookings'].mean() > 1)).all():
            df['core_customer'] = 1
    else: df['core_customer'] = 0
    df['booking_count'] = np.arange(len(df)) + 1
    return df
            


def main():
    filename = sys.argv[1]
    columns_to_use = ['Booking ID','Phone','Email','Customer name','requested_date','Discount amount','Amount','DM credits used','Status']
    df = pd.read_csv(filename, usecols = columns_to_use)
    df['requested_date'] = pd.to_datetime(df['requested_date'])
    df['booking_month'] = df['requested_date'].apply(lambda x: x.strftime('%Y-%m'))
    df['Discount amount'].fillna(value = 0,inplace = True)
    df['AMP'] = df['Amount'] - df['Discount amount'] -[x if x>0 else 0 for x in df['DM credits used']]

    df = df[df['Status'].isin(['closed','service_complete'])]
    df.sort_values(['Phone','requested_date'], inplace = True)

    #adding frequency and successful bookings
    df.set_index('Phone', inplace = True)
    df['successful_bookings'] = df.groupby(level = 0)['requested_date'].count()
    #pdb.set_trace()
    df['daysOnSystem'] = df.groupby(level = 0)['requested_date'].apply(lambda x: pd.to_datetime('today')-x.min()).astype('timedelta64[D]')
    df['frequency'] = df['daysOnSystem'].divide(df['successful_bookings'], axis = 0)

    df = df.groupby(level = 0).apply(core)

    output = 'c:/users/amit/documents/data_dump/output.core_customer.csv'




if __name__=='__main__':
    main()
