import sys
import os
import pandas as pd
import numpy as np


def calculate_nps(s):
    if s<3: return -1
    elif s==3 : return 0
    elif s>3 : return 1
    else: return np.nan
    


def nps(filename):
    #reading selected columns from the file
    columns_to_use = ['Booking ID','Status','Feedback','Bad rating reason','City','requested_date']
    df = pd.read_csv(filename, usecols = columns_to_use)
    #extracting only closed and service complete bookings
    df = df[df['Status'].isin(['service_complete','closed'])]
    #converting 'requested_date to datetime column
    df['requested_date'] = pd.to_datetime(df['requested_date'])
    df['month'] = df['requested_date'].apply(lambda x: x.strftime('%Y-%m'))
    #maping Feedbacks to corresponding nps score
    df['nps'] = df['Feedback'].map(calculate_nps)

    #calculating nps and writing it to file
    nps = df.groupby(['month','City'])['nps'].agg(['size','count','mean'])
    output_file = os.path.join(os.path.dirname(filename),'output\[nps].xlsx')
    writer = pd.ExcelWriter(output_file)
    nps.to_excel(writer, sheet_name = 'nps')
    #total feedback to calculate percentage feedbacks in the bad feedback rating
    total_feedbacks = df.groupby('month')['nps'].count()
    
    #analyzing bad rating reason
    #http://stackoverflow.com/questions/17116814/pandas-how-do-i-split-text-in-a-column-into-multiple-rows - used this answer to do the following analysis
    df = df[df['Bad rating reason'].notnull()]
    s = df['Bad rating reason'].str.split(',').apply(pd.Series, 1).stack()
    s.index = s.index.droplevel(-1)
    s.name = 'Bad rating reason'
    del df['Bad rating reason']
    df = df.join(s)
    bad_rating_reason = df.groupby(['month','Bad rating reason'])['Booking ID'].count()  
    bad_rating_reason = bad_rating_reason.div(total_feedbacks, level = 0)
    bad_rating_reason.to_frame().to_excel(writer, sheet_name = 'bad_rating_analysis')
    writer.save()

    return


def new_repeat(df):
    first_booking_index = df['requested_date'].idxmin()
    df.ix[first_booking_index, 'new/repeat'] = 'first_booking'
    return df
    

def new_repeat_virtual(filename):
    columns_to_use = ['Booking ID','Phone','Status','requested_date','DM credits used','Amount','Discount amount']
    df = pd.read_csv(filename, usecols = columns_to_use) 
    df['requested_date'] = pd.to_datetime(df['requested_date'])
    df = df[df['Status'].isin(['closed','service_complete'])]
    df['Discount amount'].fillna(value = 0, inplace = True)
    #cashbacks are not included here...as they will be applied in future
    df['actual_amt_paid'] = df['Amount'] - df['Discount amount'] - [x if x>=0 else 0 for x in df['DM credits used']]
    df['virtual money'] = df['Discount amount'] + df['DM credits used']
    df['month'] = df['requested_date'].apply(lambda x: x.strftime('%Y-%m'))

    
    #new/repeat_booking label introduced
    df['new/repeat'] = 'repeat_booking'
    df = df.groupby('Phone').apply(new_repeat)

    #getting virtual money depending on new/repeat groups
    grouped = df.groupby(['new/repeat','month']).agg({'Booking ID':'count','virtual money':'sum'})
    grouped.to_csv(os.path.join(os.path.dirname(filename),'output\[new_repeat_virtual.csv'))


def main():
	option = sys.argv[1]
        filename = sys.argv[2]

        if option == '--NPS':
            nps(filename)

        elif option == '--new_repeat_virtual':
            new_repeat_virtual(filename)

if __name__ == '__main__':
    main()
