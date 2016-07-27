import sys
import os
import pandas as pd
import pdb
import numpy as np


def merge_df(df1,df2):
    return df1.combine_first(df2)


def acquisition_s(df):
    #pdb.set_trace()
    index = df['requested_date'].idxmin()
    if df.loc[index,'Whether referred'] == 1:
        if df[df.index == index]['Coupon'].notnull().all():
            df['acquisition_source'] = 'Both Marketing & Referral'
        else: df['acquisition_source'] = 'Only Referral'
    else:
        if df[df.index == index]['Coupon'].notnull().all():
            df['acquisition_source'] = 'Only Marketing'
        else: df['acquisition_source'] = 'Organically'

    return df


def customer_segment(df):
    threshold = .1
    #pdb.set_trace()

    if (df['Category'] == 'Laundry').all():
        df['customer_segment'] = 'only premium'
        if (df['Type'].str.contains('Dry')).all():
            df['only_DC'] = 1
    elif (df['Category'] == 'Regular Laundry').all():
        df['customer_segment'] = 'only regular'
    else: 
        category_gmv = df.groupby('Category')['Amount'].sum()
        if category_gmv['Laundry']/float(category_gmv.sum()) < threshold:
            df['customer_segment'] = 'only regular'
        elif category_gmv['Regular Laundry']/float(category_gmv.sum()) < threshold:
            df['customer_segment'] = 'only premium'
        else: df['customer_segment'] = 'both premium & regular'

    return df

def booking_count(df):
    df.sort_values('requested_date', ascending = True)
    df['booking_count'] = np.arange(len(df)) + 1
    return df

def rating(df):
    successful_bookings = df['successful_bookings'].mean()
    revenue = df['AMP'].sum()/float(successful_bookings)
    if revenue <= 2:
        p1 = 1
    elif revenue <= 54:
        p1 = 2
    elif revenue <= 149:
        p1 = 3
    elif revenue <= 249:
        p1 = 4
    else:
        p1 = 5

    if successful_bookings == 1:
        p2 = 1
    elif successful_bookings == 2:
        p2 = 2
    elif successful_bookings == 3:
        p2 = 3
    elif successful_bookings == 4:
        p2 = 4
    else :
        p2 = 5 

    df['rating'] = .5*(p1+p2)
    return df

def customer_DMC(df):
    df['Customer DMC'] = df.loc[df['requested_date'].idxmax(), 'Customer DMC']
    return df

def duplicate_booking(df):
    index = list(df[df['Parent ID'].notnull()].index)

    for booking in index:
        if (df.loc[booking, 'Parent ID'] in df.index.tolist()) & pd.Series(df.loc[booking, 'Rescheduled/Redo']).isnull().all():
            df.loc[booking,'duplicate_booking'] = 1

    return df


def new_repeat(df):
    df.loc[df['requested_date'].idxmin(), 'new_repeat'] = 'first_booking'
    return df


def new_columns(df):
    df['successful_bookings'] = df['requested_date'].count()
    df['cohort_group'] = df.loc[df['requested_date'].idxmin(),'booking_month']
    df = acquisition_s(df)
    df = customer_segment(df)
    df = booking_count(df)
    df = rating(df)
    df = customer_DMC(df)
    df = duplicate_booking(df)
    df = new_repeat(df)
    return df

def nps(s):
    if s < 3: return -1
    elif s == 3: return 0
    elif s > 3: return 1
    else: return np.nan


def main():
    filename1 = sys.argv[1]
    filename2 = sys.argv[2]
    df1 = pd.read_csv(filename1, index_col = 'Booking ID', low_memory = False)
    df2 = pd.read_csv(filename2, index_col = 'Booking ID', low_memory = False)
    #getting column_list of original df to retain the column order 
    column_list = df1.columns.tolist()
    merged_data_dump = merge_df(df1,df2)
    merged_data_dump = merged_data_dump[column_list]
    merged_data_dump['requested_date'] = pd.to_datetime(merged_data_dump['requested_date'])
    merged_data_dump['booking_month'] = merged_data_dump['requested_date'].apply(lambda x: x.strftime('%Y-%m'))
    merged_data_dump[['Discount amount','Taxes']] = merged_data_dump[['Discount amount','Taxes']].fillna(value = {'Discount amount':0, 'Taxes':0})
    merged_data_dump['DM credits used'] = [x if x>=0 else 0 for x in merged_data_dump['DM credits used']]
    merged_data_dump['total_revenue'] = merged_data_dump['Amount']+merged_data_dump['Taxes']
    merged_data_dump['AMP'] = merged_data_dump['total_revenue'] - merged_data_dump['Discount amount'] - [x if x>= 0 else 0 for x in merged_data_dump['DM credits used']]
    merged_data_dump.to_csv(os.path.join(os.path.dirname(filename1),'output\merged_data_dump.csv'), index = True)


    success = merged_data_dump[merged_data_dump['Status'].isin(['closed','service_complete','in_service'])]
    #arbitraly adding a column with 'repeat_booking' string...would modify this to include new_booking tag
    success['new_repeat'] = 'repeat_booking'

    success = success.groupby('Phone').apply(new_columns)
    success['nps'] = success['Feedback'].map(nps)
    additions = ['total_revenue','AMP','booking_month','successful_bookings','cohort_group','acquisition_source','customer_segment','only_DC','booking_count','rating','duplicate_booking','new_repeat','nps']
    column_list.extend(additions)
    success = success[column_list]

    columns_to_use = ['Phone','Customer name','Email','Locality','City','Category','Type','requested_date','requested_time','Status','RFD time','Paid online','Paid cash','Invoice date','Tags','Hub','Facility','booking_month','Lead channel','total_revenue','Taxes','AMP','Coupon','Discount amount','DM credits used','Feedback','nps','Bad rating reason','TAT','Facility','Customer DMC','successful_bookings','cohort_group','acquisition_source','customer_segment','only_DC','rating','booking_count','duplicate_booking','new_repeat']
    success = success[columns_to_use]

    output = 'output\success.csv'
    success.to_csv(os.path.join(os.path.dirname(filename1), output), index = True)


if __name__ == '__main__':
    main()
