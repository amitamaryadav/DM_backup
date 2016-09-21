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


def marketing_master_booking_data(filename):
    column_to_use = ['total_revenue','Customer name','Email','Phone','Locality','City','Feedback','requested_date','Customer DMC','rating']
    df = pd.read_csv(filename)
    #getting set of non_cancelled bookings
    df = df[(df['City'] == 'Mumbai')]
    df['requested_date'] = pd.to_datetime(df['requested_date'], errors = 'coerce')

    #http://stackoverflow.com/questions/13703720/converting-between-datetime-timestamp-and-datetime64 - understanding difference between datetimes of python and pandas
    grouped = df.groupby('Phone')
    today = pd.to_datetime('today')
    agg_f = {'Customer name':{'Customer_Name':'first'},\
                'Email':{'Customer_Email_ID':'first'},\
                'Locality':{'Customer_Locality':'first'},\
                'City':{'Customer_City':'first'},\
                'Feedback':{'Customer_Feedback':'mean'},\
                'rating':{'DoorMint_rating':'first'},\
                'requested_date':{'Total_Bookings':'count',\
                                'Last_Booking_Date':'max',\
                                'No Booking in last 30 days':lambda x: (today - x.max()).days > 30,\
                                'No Booking in last 45 days':lambda x: (today - x.max()).days > 45,\
                                'No Booking in last 75 days':lambda x: (today - x.max()).days > 75,\
                                'No Booking in last 60 days':lambda x: (today - x.max()).days > 60,\
                                'No Booking in last 90 days':lambda x: (today - x.max()).days > 90},\
                'Customer DMC':{'Balance_DMC':'first'},\
                'customer_segment':{'customer_segment':'first'}}
    
    final_df = grouped.agg(agg_f)
    #final_df.columns = final_df.columns.droplevel()
    final_df.to_csv(os.path.join(os.path.dirname(filename),'output\marketing_master_booking_data123.csv'))

    return 


def main():
    if len(sys.argv) < 3:
        print 'invalid option \n'
        print 'usage: python filename.py {--verify_nobooking_data | --marketing_master_booking_data } files'
        print 'the files should be in chronological order with the most recent file first'
        sys.exit(1)

    option = sys.argv[1]
    filename = sys.argv[2:]

    if option == '--verify_nobooking_data':
        nobookings_data = pd.read_csv(filename[0])
        bookings_data = pd.read_csv(filename[1]) 
        column_list = nobookings_data.columns
        verified_nobookings_data = verify_nobooking_data(nobookings_data,bookings_data)
        verified_nobookings_data = verified_nobookings_data[column_list]
        verified_nobookings_data.to_csv(os.path.join(os.path.dirname(filename[0]), 'output\[verified_data_dump].csv'), index = False)

    elif option == '--marketing_master_booking_data':
        marketing_master_booking_data(filename[0])

    else:
        print 'invalid option \n'
        print 'usage: python filename.py {--verify_nobooking_data | --marketing_master_booking_data } files'
        print 'the files should be in chronological order with the most recent file first'
        sys.exit(1)


if __name__ == '__main__':
    main()
