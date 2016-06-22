import pandas as pd
import sys



def main():
    filename = sys.argv[1]
    df = pd.read_csv(filename)
    df['requested_date'] = pd.to_datetime(df['requested_date'], format = '%Y-%m-%d')
    df['booking_month'] = df['requested_date'].apply(lambda x: x.strftime('%Y-%m'))
    df = df[df['Status'].isin(['closed','service_complete'])]

    df.set_index('Phone',inplace = True)
    df['successful_bookings'] = df.groupby(level = 0)['requested_date'].count()
    df['frequency'] = df.groupby(level = 0)['requested_date'].apply(lambda x: (pd.to_datetime('today')-x.min()))
    df['frequency'] =  df['frequency'].astype('timedelta64[D]')
    df['frequency'] = df['frequency'].divide(df['successful_bookings'], axis = 0)
    df.reset_index(inplace = True)

    df['Discount amount'].fillna(value = 0, inplace = True)
    df['actual amount paid'] = df['Amount'] - df['Discount amount'] - [x if x>0 else 0 for x in df['DM credits used']]

    grouped = df.groupby('Phone').agg({'successful_bookings':'first','frequency':'first'})
    #grouped['avg actual amount paid'] = grouped['actual amount paid'].divide(grouped.successful_bookings, axis = 0)
    #grouped['avg AMP range'] = pd.qcut(grouped['avg actual amount paid'], 5)
    grouped['avg_buckets'] = pd.qcut(grouped['frequency'], 5)

    #grouped.to_csv('profiling.csv')

    dfm.set_index('Phone', inplace = True)
    dfm['successful_bookings'] = dfm.groupby(level = 0)['requested_date'].count()
    dfm['frequency'] = dfm.groupby(level = 0)['requested_date'].apply(lambda x: (pd.to_datetime('today')-x.min()))
    dfm['frequency'] =  dfm['frequency'].astype('timedelta64[D]')
    dfm['frequency'] = dfm['frequency'].divide(dfm['successful_bookings'], axis = 0)
    dfm.reset_index(inplace = True)
    grouped = dfm.groupby('Phone').agg({'successful_bookings':'first','frequency':'first','actual amount paid':'sum'})
    grouped['avg actual amount paid'] = grouped['actual amount paid'].divide(grouped.successful_bookings, axis = 0)
    grouped['avg revenue'] = grouped['Amount'].divide(grouped.successful_bookings, axis = 0)
    grouped['avg revenue buckets'] = pd.qcut(grouped['avg revenue'],5)
    grouped['avg AMP range'] = pd.qcut(grouped['avg actual amount paid'], 5)
    grouped['freq bucket'] = pd.qcut(grouped['frequency'], 5)
    grouped.to_csv('profiling1.csv')
    





if __name__=='__main__':
    main()
