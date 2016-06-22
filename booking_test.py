import pandas as pd
import sys
import pdb


def main():
    filename = sys.argv[1]
    columns_to_use = ['Phone','Email','Customer name','requested_date','Discount amount','Amount','DM credits used','Status']
    df = pd.read_csv(filename, usecols = columns_to_use)
    df['requested_date'] = pd.to_datetime(df['requested_date'])
    df['booking_month'] = df['requested_date'].apply(lambda x: x.strftime('%Y-%m'))
    df['Discount amount'].fillna(value = 0,inplace = True)
    df['AMP'] = df['Amount'] - df['Discount amount'] -[x if x>0 else 0 for x in df['DM credits used']]

    df = df[df['Status'].isin(['closed','service_complete'])]

    df.set_index('Phone', inplace = True)
    df['successful_bookings'] = df.groupby(level = 0)['requested_date'].count()
    df.reset_index(inplace = True)



if __name__=='__main__':
    main()
