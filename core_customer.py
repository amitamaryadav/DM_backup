import pandas as pd
import sys
import pdb
import numpy as np
import os



def core(df):
    #pdb.set_trace()

    if df['only_DC'].notnull().all():
        if ((df['frequency'].mean() < 60) & (df['successful_bookings'].mean() > 1)).all():
            df['core customer'] = 1
        else: df['core customer'] = 0
    else:
        if ((df['frequency'].mean() < 20) & (df['successful_bookings'].mean() > 1)).all():
            df['core_customer'] = 1
        else: df['core_customer'] = 0
    #df['booking_count'] = np.arange(len(df)) + 1
    return df

def f(df, date, booking_month):
    #adding frequency and successful bookings
    #pdb.set_trace()
    df = df[df['requested_date'] < date]
    df.set_index('Phone', inplace = True)
    df['daysOnSystem'] = df.groupby(level = 0)['requested_date'].apply(lambda x: pd.to_datetime(date)-x.min()).astype('timedelta64[D]')
    df['frequency'] = df['daysOnSystem'].divide(df['successful_bookings'], axis = 0)
    df.reset_index(inplace = True)
    

    df.set_index('Booking ID', inplace = True) 
    df = df.groupby('Phone').apply(core)
    df.reset_index(inplace = True)

    core_users = df.loc[(df['booking_month'] == booking_month) & (df['core_customer'] == 1), 'Phone'].nunique()
    total_users = df.loc[(df['booking_month'] == booking_month), 'Phone'].nunique()

    core_gmv = df.loc[(df['booking_month'] == booking_month) & (df['core_customer'] == 1), 'total_revenue'].sum()
    total_gmv = df.loc[(df['booking_month'] == booking_month), 'total_revenue'].sum()
    return (total_users, core_users/float(total_users),total_gmv,core_gmv/float(total_gmv))



def main():
    print 'frequency < 20 days, successful_bookings >=2'
    filename = sys.argv[1]
    columns_to_use = ['Booking ID','Phone','Email','Customer name','requested_date','Discount amount','Amount','DM credits used','Status','acquisition_source','successful_bookings','booking_month','Category','Taxes','only_DC','customer_segment']
    df = pd.read_csv(filename, usecols = columns_to_use)

    df['requested_date'] = pd.to_datetime(df['requested_date'])
    df['Discount amount'].fillna(value = 0,inplace = True)
    df['Taxes'].fillna(value = 0,inplace = True)
    df['total_revenue'] = df['Amount']+df['Taxes']
    df['AMP'] = df['total_revenue'] - df['Discount amount'] -[x if x>0 else 0 for x in df['DM credits used']]

    #df = df[~((df['successful_bookings'] == 1))]
    df = df[df['Status'].isin(['closed','service_complete'])]

    l = []
    date_list = ['1-feb-2016','1-March-2016','1-april-2016','1-may-2016','1-jun-2016']
    booking_month = ['2016-05','2016-04','2016-03','2016-02','2016-01']
    for date in date_list:
        #pdb.set_trace()
        month = booking_month.pop()
        l.append(f(df,date, month))

    print l


    #output_file = 'output\core_may.csv'
    #grouped = df.groupby(['booking_month','core_customer']).agg({'Phone':pd.Series.nunique,'Amount':'sum','AMP':'sum','total_revenue':'sum','Booking ID':'count'})
    #grouped.to_csv(os.path.join(os.path.dirname(filename),output_file))



if __name__=='__main__':
    main()
