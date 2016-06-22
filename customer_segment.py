import pandas as pd
import sys
import pdb


phone_r = []
phone_p = []



def f1(df):
    threshold = .1
    #pdb.set_trace()
    gmv_p = 0
    gmv_r = 0
    dry = 0
    prime = 0
    for row in df.itertuples():
        phone = row[3]
        if row[4] == 'Laundry':
            gmv_p = gmv_p + row[8]
            if 'Dry' in row[5]:
                dry = dry + 1
            elif 'Dry' not in row[5]:
                prime = prime + 1
        else: 
            gmv_r = gmv_r + row[8]
    
    if gmv_r + gmv_p > 0:
        if gmv_r/float(gmv_r+gmv_p) > threshold:
            if gmv_p/float(gmv_r+gmv_p) > threshold:
                df['customer_segment'] = 'working_professional'
            else:
                df['customer_segment'] = 'students'
                phone_r.append(phone)
        else: 
            df['customer_segment'] = 'families'
            phone_p.append(phone)
    else: df['customer_segment'] = 'GMV == 0'

    if df.iloc[0,8] == 'families': 
        if (dry > 0) & (prime > 0):
            df['premium_sub-cat'] = 'both prime & dry'
        elif (dry >0) & (prime == 0):
            df['premium_sub-cat'] = 'only dry'
        elif (dry == 0) & (prime > 0):
            df['premium_sub-cat'] = 'only prime'
        else: df['premium_sub-cat'] = 'none'


    return df




def main():
    filename = sys.argv[1]
    columns_to_use = ['Phone','requested_date','Status','City','Category','Amount','Type','Email','Customer name']
    df = pd.read_csv(filename, usecols = columns_to_use)
    df['requested_date'] = pd.to_datetime(df['requested_date'])
    df['booking_month'] = df['requested_date'].apply(lambda x: x.strftime('%Y-%m'))

    df = df[(df['Status'].isin(['closed','service_complete'])) & (df['requested_date'] > '1-feb-2016')]

    df['customer_segment'] = ''
    df['premium_sub-cat'] = ''
    df = df.groupby('Phone').apply(f1)

    dfm1 = df.copy(deep = True)
    dfm2 = df.copy(deep = True)
    dfm1 = dfm1[dfm1['Phone'].isin(phone_p)]
    dfm2 = dfm2[dfm2['Phone'].isin(phone_r)]
    grouped1 = dfm1.groupby('Phone').agg({'Email':'first','Customer name':'first','customer_segment':'first','premium_sub-cat':'first','Amount':'sum'})
    grouped2 = dfm2.groupby('Phone').agg({'Email':'first','Customer name':'first','customer_segment':'first','premium_sub-cat':'first','Amount':'sum'})

    grouped1.to_csv('premium.csv')
    grouped2.to_csv('regular.csv')




if __name__=='__main__':
    main()
