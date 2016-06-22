import sys
import os
import pandas as pd
import pdb


def merge_df(df1,df2):
    return df1.combine_first(df2)



def verify_nobooking_data(nobookings, bookings):
    #drop duplicates if any
    nobookings.drop_duplicates(inplace = True)
    #series isin series does not take the index into account...it just searches for the values
    return nobookings[~(nobookings['Number'].isin(bookings.loc[bookings['Status'] <> 'cancelled', 'Phone']))]



def customer_segment(df):
    threshold = .1
    #pdb.set_trace()
    gmv_p = 0
    gmv_r = 0
    for row in df.itertuples():
        if row[6] == 'Laundry':
            gmv_p = gmv_p + row[9]
        else: 
            gmv_r = gmv_r + row[9]
    
    if gmv_r + gmv_p > 0:
        if gmv_r/float(gmv_r+gmv_p) > threshold:
            if gmv_p/float(gmv_r+gmv_p) > threshold:
                df['customer_segment'] = 'both regular and prime'
            else:
                df['customer_segment'] = 'only regular'
        else: 
            df['customer_segment'] = 'only premium'
    else: df['customer_segment'] = 'GMV == 0'

    return df


def marketing_master_booking_data(filename):
    #i only read the file and not the dataframe because pandas thinks that i am working on a copy here and raises warning...so just to be on safe side, i read the data inside the function
    #pdb.set_trace()
    column_to_use = ['Category','Amount','Customer name','Email','Phone','Locality','Status','City','Feedback','requested_date','Customer DMC','Rating']
    df = pd.read_csv(filename, usecols = column_to_use)
    #getting set of non_cancelled bookings
    df = df[df['Status'].isin(['closed','service_complete'])]
    #converting the requested_date to datetime format...even the function in comments works great
    #df.loc[:,'requested_date'] = df.loc[:,'requested_date'].apply(lambda x: pd.to_datetime(x))
    df['requested_date'] = pd.to_datetime(df['requested_date'], errors = 'coerce')
    #getting customer segment
    df['customer_segment'] = 'nothing'
    df = df.groupby('Phone').apply(customer_segment)
    #need to sort so that the latest booking with latest customer DMC comes to the top of the group and i apply 'first' to extract it
    df.sort_values(by='requested_date',ascending = False, inplace = True)
     
    #Method 1 :- The reason for the need to put set_index is because grouped = df.groupby('Phone') puts the index as Phone. Since the original df does not have Phone number index, so the assignment throws an error....so this is needed. 
    #http://www.shanelynn.ie/summarising-aggregation-and-grouping-data-in-python-pandas/ - good article about groupby basics
    '''
    df.set_index('Phone', inplace = True)
    grouped = df.groupby(level = 0)
    df['no booking for 45 days'] =  (pd.to_datetime('today').date() - grouped['requested_date'].max()).dt.days > 45
    df['no booking for 30 days'] =  (pd.to_datetime('today').date() - grouped['requested_date'].max()).dt.days > 30 
    df['no booking for 60 days'] =  (pd.to_datetime('today').date() - grouped['requested_date'].max()).dt.days > 60 
    df['last booking date'] = grouped['requested_date'].max()
    df['successful bookings'] = grouped['requested_date'].count()
    agg_f = ({\
            'Customer name':'first',\
            'Email':'first',\
            'Locality':'first',\
            'City':'first',\
            'Feedback':'mean',\
            'Rating':'first',\
            'successful bookings':'first',\
            'last booking date':'first',\
            'no booking for 30 days':'first',\
            'no booking for 45 days':'first',\
            'no booking for 60 days':'first',\
            'Customer DMC':'first'})
    '''
    #Method 2 :- trying an alternate method
    #http://stackoverflow.com/questions/13703720/converting-between-datetime-timestamp-and-datetime64 - understanding difference between datetimes of python and pandas
    grouped = df.groupby('Phone')
    today = pd.to_datetime('today')
    agg_f = {'Customer name':{'Customer_Name':'first'},\
                'Email':{'Customer_Email_ID':'first'},\
                'Locality':{'Customer_Locality':'first'},\
                'City':{'Customer_City':'first'},\
                'Feedback':{'Customer_Feedback':'mean'},\
                'Rating':{'DoorMint_rating':'first'},\
                'requested_date':{'Total_Bookings':'count',\
                                'Last_Booking_Date':'max',\
                                'No Booking in last 30 days':lambda x: (today - x.max()).days > 30,\
                                'No Booking in last 45 days':lambda x: (today - x.max()).days > 45,\
                                'No Booking in last 60 days':lambda x: (today - x.max()).days > 60},\
                'Customer DMC':{'Balance_DMC':'first'},\
                'customer_segment':{'customer_segment':'first'}}
    
    final_df = grouped.agg(agg_f)
    final_df.columns = final_df.columns.droplevel()
    final_df.to_csv(os.path.join(os.path.dirname(filename),'output\marketing_master_booking_data123.csv'))

    return 





def main():
    if len(sys.argv) < 3:
        print 'invalid option \n'
        print 'usage: python filename.py {--merge_datadumps | --verify_nobooking_data | --marketing_master_booking_data } files'
        print 'the files should be in chronological order with the most recent file first'
        sys.exit(1)
    
    option = sys.argv[1]
    filename = sys.argv[2:]
    if option == '--merge_datadumps':
        df1 = pd.read_csv(filename[0], index_col = 'Booking ID', low_memory = False)
        df2 = pd.read_csv(filename[1], index_col = 'Booking ID', low_memory = False)
        #getting column_list of original df to retain the column order 
        column_list = df1.columns
        merged_data_dump = merge_df(df1,df2)
        merged_data_dump = merged_data_dump[column_list]
        merged_data_dump.to_csv(os.path.join(os.path.dirname(filename[0]),'output\merged_data_dump.csv'), index = True)

    elif option == '--verify_nobooking_data':
        nobookings_data = pd.read_csv(filename[0])
        bookings_data = pd.read_csv(filename[1]) 
        column_list = nobookings_data.columns
        verified_nobookings_data = verify_nobooking_data(nobookings_data,bookings_data)
        verified_nobookings_data = verified_nobookings_data[column_list]
        verified_nobookings_data.to_csv(os.path.join(os.path.dirname(filename[0]), 'output\wverified_data_dump.csv'), index = False)

    elif option == '--marketing_master_booking_data':
        marketing_master_booking_data(filename[0])

    else:
        print 'invalid option \n'
        print 'usage: python filename.py {--merge_datadumps | --verify_nobooking_data | --marketing_master_booking_data } files'
        print 'the files should be in chronological order with the most recent file first'
        sys.exit(1)
    

if __name__ == '__main__':
    main()
