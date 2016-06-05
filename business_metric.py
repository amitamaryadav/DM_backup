import sys
import os
import pandas as pd
import numpy as np

'''http://www.gregreda.com/2015/08/23/cohort-analysis-with-python/
followed the above article for cohort analysis.

This is required once a month by core team
'''

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




def new_repeat_booking(df):
    first_booking_index = df['requested_date'].idxmin()
    df.ix[first_booking_index, 'new/repeat'] = 'first_booking'
    return df
    

def new_repeat(filename):
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
    df = df.groupby('Phone').apply(new_repeat_booking)

    #getting virtual money depending on new/repeat groups
    grouped = df.groupby(['new/repeat','month'])
    virtual_money = grouped.agg({'Booking ID':'count','virtual money':'sum'})
    revenue = grouped.agg({'Amount':'count','Amount':'sum'})

    output_file = os.path.join(os.path.dirname(filename),'output\[new_repeat].xlsx')

    writer = pd.ExcelWriter(output_file)
    virtual_money.to_excel(writer, sheet_name = 'virtual_money')
    revenue.to_excel(writer, sheet_name = 'revenue')
    
    writer.save()





def cohort_to_excel(df_list,writer,sheetname):
    row_number = 0
    for df in df_list:
        df.to_excel(writer, startrow = row_number, sheet_name = sheetname)
        row_number = row_number + len(df.index) + 6
    
    return

def cohorts_cal(df,writer,cohort_type):
    #actual cohort calculation - abs and percentage
    cohorts = df.groupby(['cohort_month','booking_month']).agg({\
                                    'Phone':pd.Series.nunique,\
                                    'Booking ID': 'count',\
                                    'Amount': 'sum'})

    cohorts.rename(columns = {'Phone':'Total Users','Booking ID':'Total Bookings','Amount':'Total Revenue'}, inplace = True)
    
    user_abs = cohorts['Total Users'].unstack(level = 1)
    user_percentage = user_abs.divide(cohorts['Total Users'].groupby(level = 0).first(), axis = 0)

    booking_abs = cohorts['Total Bookings'].unstack(level = 1)
    booking_percentage = booking_abs.divide(cohorts['Total Bookings'].groupby(level = 0).first(), axis = 0)
    

    revenue_abs = cohorts['Total Revenue'].unstack(level = 1)
    revenue_percentage = revenue_abs.divide(cohorts['Total Revenue'].groupby(level = 0).first(), axis = 0)

    cohort_abs = [user_abs, booking_abs, revenue_abs]
    cohort_percentage = [user_percentage, booking_percentage, revenue_percentage]
    cohort_to_excel(cohort_abs, writer, cohort_type+'_abs')
    cohort_to_excel(cohort_percentage, writer, cohort_type+'_%')

    return 


def cohorts(filename):
    columns_to_use = ['Booking ID','Phone','Status','requested_date','DM credits used','Amount','Discount amount','Feedback','Rating']
    df = pd.read_csv(filename, usecols = columns_to_use, low_memory = False) 
    df = df[df['Status'].isin(['closed','service_complete','in_service'])]
    df['requested_date'] = pd.to_datetime(df['requested_date'])
    df['booking_month'] = df['requested_date'].apply(lambda x: x.strftime('%Y-%m'))
    
    df['Discount amount'].fillna(value = 0, inplace = True)
    df['Actual Amount Paid'] = df['Amount'] - df['Discount amount'] - [x if x>0 else 0 for x in df['DM credits used']]

    df = df[df['booking_month'] <> '2016-06']

    df.set_index('Phone',inplace = True)
    grouped = df.groupby(level = 0)
    df['cohort_month'] = grouped['requested_date'].min().apply(lambda x: x.strftime('%Y-%m'))
    df['successful_bookings'] = grouped['requested_date'].count()
    df['avg_feedback'] = grouped['Feedback'].mean()
    df.reset_index(inplace = True)

    df_wo_garbage = df[~((df['successful_bookings'] == 1) & (df['Actual Amount Paid'] == 0))]
    df_ge2_bookings = df[df['successful_bookings'] > 1]
    df_feedback_ge3 = df[df['avg_feedback'] >= 3]
    df_good_profile = df[df['Rating'] > 3]


    output_file = os.path.join(os.path.dirname(filename),'output\[cohorts].xlsx')
    writer = pd.ExcelWriter(output_file)
    cohorts_cal(df,writer,'Overall')
    cohorts_cal(df_wo_garbage,writer,'wo_garbage')
    cohorts_cal(df_ge2_bookings,writer,'atleast_2_bookings')
    cohorts_cal(df_feedback_ge3,writer,'avg_feedback>=3')
    cohorts_cal(df_good_profile,writer,'profile=4,5')

    writer.save()


def main():
	option = sys.argv[1]
        filename = sys.argv[2]

        if option == '--NPS':
            nps(filename)

        elif option == '--new_repeat':
            new_repeat(filename)

        elif option == '--cohorts':
            cohorts(filename)

        else: 
            print 'invalid option \n'
            print 'usage : python filename.py {--NPS | --cohorts | --new_repeat} booking_data.csv'


if __name__ == '__main__':
    main()
