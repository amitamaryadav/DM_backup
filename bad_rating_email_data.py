import pandas as pd
import sys
import pdb
import numpy as np


def f(df):
    df['booking_count'] = np.arange(len(df)) + 1
    return df 



def main():
    filename = sys.argv[1]
    columns_to_use = ['Booking ID','Phone','Email','City','Customer name','requested_date','Discount amount','Locality','Amount','DM credits used','Status','Feedback','Type','Bad rating reason']
    df = pd.read_csv(filename, usecols = columns_to_use)
    df['requested_date'] = pd.to_datetime(df['requested_date'])
    df['booking_month'] = df['requested_date'].apply(lambda x: x.strftime('%Y-%m'))
    df['Discount amount'].fillna(value = 0,inplace = True)
    df['AMP'] = df['Amount'] - df['Discount amount'] -[x if x>0 else 0 for x in df['DM credits used']]

    df = df[(df['Status'].isin(['closed','service_complete'])) & (df['requested_date'] > '1-april-2016') & (df['Feedback'].isin([1,2,3])) & (df['Bad rating reason'].str.contains('requested'))] 

    
    df.sort_values(['Phone','requested_date'], inplace = True)
    df = df.groupby('Phone').apply(f)
    
    df[['Email','requested_date','Customer name','Type','Booking ID','Feedback','City','Locality','booking_count','Bad rating reason']].to_csv('logistics.csv', index = False)
    


if __name__=='__main__':
    main()
