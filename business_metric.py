import sys
import os
import pandas as pd
import numpy as np

'''http://www.gregreda.com/2015/08/23/cohort-analysis-with-python/
followed the above article for cohort analysis.

This is required once a month by core team

Input required - a file with all successful bookings with additional columns like new_repeat, cohort_group already present
Output - excel file containg the NPS, cohorts, new_repeat behaviour
'''

def nps(filename):
    df = pd.read_csv(filename)
    #extracting only closed and service complete bookings
    df = df[df['Status'].isin(['service_complete','closed'])]
    #converting 'requested_date to datetime column
    df['requested_date'] = pd.to_datetime(df['requested_date'])

    #calculating nps and writing it to file
    nps = df.groupby(['booking_month'])['nps'].agg(['size','count','mean'])
    nps.rename(index = str, columns = {'size':'Total Bookings','count':'Total Bookings with Feedback','mean':'NPS'})
    nps_city = df.groupby(['booking_month','City'])['nps'].agg(['size','count','mean'])
    nps_city.rename(index = str, columns = {'size':'Total Bookings','count':'Total Bookings with Feedback','mean':'NPS'})

    output_file = os.path.join(os.path.dirname(filename),'output\[nps].xlsx')
    writer = pd.ExcelWriter(output_file)
    nps.to_excel(writer, sheet_name = 'nps')
    nps_city.to_excel(writer, sheet_name = 'nps_city')

    #analyzing bad rating reason
    #total feedback to calculate percentage feedbacks in the bad feedback rating
    total_feedbacks = df.groupby('booking_month')['nps'].count()
    #http://stackoverflow.com/questions/17116814/pandas-how-do-i-split-text-in-a-column-into-multiple-rows - used this answer to do the following analysis
    df = df[df['Bad rating reason'].notnull()]
    s = df['Bad rating reason'].str.split(',').apply(pd.Series, 1).stack()
    s.index = s.index.droplevel(-1)
    s.name = 'Bad rating reason'
    del df['Bad rating reason']
    df = df.join(s)

    bad_rating_reason = df.groupby(['booking_month','Bad rating reason'])['Booking ID'].count()  
    bad_rating_reason = bad_rating_reason.div(total_feedbacks, level = 0)
    bad_rating_reason.to_frame().to_excel(writer, sheet_name = 'bad_rating_analysis')
    writer.save()

    return



def cohort_to_excel(df_list,writer,sheetname):
    row_number = 0
    for df in df_list:
        df.to_excel(writer, startrow = row_number, sheet_name = sheetname)
        row_number = row_number + len(df.index) + 6
    return

def cohorts_cal(df,writer,cohort_type):
    #actual cohort calculation - abs and percentage
    cohorts = df.groupby(['cohort_group','booking_month']).agg({\
                                    'Phone':pd.Series.nunique,\
                                    'Booking ID': 'count',\
                                    'total_revenue': 'sum'})

    cohorts.rename(columns = {'Phone':'Total Users','Booking ID':'Total Bookings','total_revenue':'Total Revenue'}, inplace = True)

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
    df = pd.read_csv(filename, low_memory = False)
    #calculating only Mumbai cohorts
    df = df[df['City'] == 'Gurgaon']
    df['requested_date'] = pd.to_datetime(df['requested_date'])

    #df = df[df['booking_month'] <> '2016-09']
    df = df[~df['cohort_group'].isin(['2016-09','2015-04','2015-05','2015-06','2015-07','2015-08'])]

    df.set_index('Phone',inplace = True)
    df['avg_feedback'] = df.groupby(level = 0)['Feedback'].mean()
    df.reset_index(inplace = True)

    df_wo_garbage = df[~((df['successful_bookings'] == 1) & (df['AMP'] == 0))]
    df_ge2_bookings = df[df['successful_bookings'] > 1]
    df_feedback_ge3 = df[df['avg_feedback'] >= 3]
    df_good_profile = df[df['rating'] > 3]


    output_file = os.path.join(os.path.dirname(filename),'output\[cohorts].xlsx')
    writer = pd.ExcelWriter(output_file)
    cohorts_cal(df,writer,'Overall')
    cohorts_cal(df_wo_garbage,writer,'wo_garbage')
    cohorts_cal(df_ge2_bookings,writer,'atleast_2_bookings')
    cohorts_cal(df_feedback_ge3,writer,'avg_feedback>=3')
    cohorts_cal(df_good_profile,writer,'profile=4,5')

    writer.save()

    return


def main():
    option = sys.argv[1]
    filename = sys.argv[2]
    if option == '--NPS':
        nps(filename)

    elif option == '--cohorts':
        cohorts(filename)

    else:
        print 'invalid option \n'
        print 'usage : python filename.py {--NPS | --cohorts | --new_repeat} booking_data.csv'



if __name__ == '__main__':
    main()
