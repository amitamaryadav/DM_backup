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
    columns_to_use = ['Booking ID','Status','requested_date','City','Feedback','Bad rating reason','Locality']
    df = pd.read_csv(filename, usecols = columns_to_use)
    #extracting only closed and service complete bookings
    df = df[df['Status'].isin(['service_complete','closed'])]
    #converting 'requested_date to datetime column
    df['requested_date'] = pd.to_datetime(df['requested_date'])
    df['month'] = df['requested_date'].apply(lambda x: x.strftime('%Y-%m'))
    #maping Feedbacks to corresponding nps score
    df['nps'] = df['Feedback'].map(calculate_nps)

    #calculating nps and writing it to file
    nps = df.groupby('Locality')['nps'].agg(['size','count','mean'])
    nps.rename(index = str, columns = {'size':'Total Bookings','count':'Total Bookings with Feedback','mean':'NPS'})
    min_size =5 
    min_nps = .10
    nps = nps[(nps['size'] > min_size) & (nps['mean'] > min_nps)]
    #nps_city = df.groupby(['month','City'])['nps'].agg(['size','count','mean'])
    #nps_city.rename(index = str, columns = {'size':'Total Bookings','count':'Total Bookings with Feedback','mean':'NPS'})

    output_file = os.path.join(os.path.dirname(filename),'output\[nps].xlsx')
    writer = pd.ExcelWriter(output_file)
    nps.to_excel(writer, sheet_name = 'nps')
    #nps_city.to_excel(writer, sheet_name = 'nps_city')

    writer.save()
    
    return list(nps.index)





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


def cohorts(filename, locality):
    columns_to_use = ['Booking ID','Phone','Status','requested_date','DM credits used','Amount','Discount amount','Feedback','Rating','Locality']
    df = pd.read_csv(filename, usecols = columns_to_use, low_memory = False) 
    df = df[df['Locality'].isin(locality)]
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
    #df_feedback_ge3 = df[df['avg_feedback'] >= 3]
    df_good_profile = df[df['Rating'] > 3]


    output_file = os.path.join(os.path.dirname(filename),'output\[cohorts].xlsx')
    writer = pd.ExcelWriter(output_file)
    cohorts_cal(df,writer,'Overall')
    cohorts_cal(df_wo_garbage,writer,'wo_garbage')
    cohorts_cal(df_ge2_bookings,writer,'atleast_2_bookings')
    #cohorts_cal(df_feedback_ge3,writer,'avg_feedback>=3')
    cohorts_cal(df_good_profile,writer,'profile=4,5')

    writer.save()


def main():
        filename = sys.argv[1]

        locality = nps(filename)
        cohorts(filename, locality)



if __name__ == '__main__':
    main()
