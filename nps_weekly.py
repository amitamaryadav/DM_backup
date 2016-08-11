import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import ipdb

'''http://www.gregreda.com/2015/08/23/cohort-analysis-with-python/
followed the above article for cohort analysis.

This is required once a month by core team

Input required - a file with all successful bookings with additional columns like new_repeat, cohort_group already present
Output - excel file containg the NPS, cohorts, new_repeat behaviour
'''
w1_start = pd.to_datetime('4-june-2016')
w1_end = pd.to_datetime('10-jun-2016')
w2_start = pd.to_datetime('11-jun-2016')
w2_end = pd.to_datetime('17-jun-2016')
w3_start = pd.to_datetime('18-jun-2016')
w3_end = pd.to_datetime('24-jun-2016')
w4_start = pd.to_datetime('26-jun-2016')
w4_end = pd.to_datetime('1-jul-2016')
w5_start = pd.to_datetime('2-jul-2016')
w5_end = pd.to_datetime('8-jul-2016')
w6_start = pd.to_datetime('9-jul-2016')
w6_end = pd.to_datetime('15-jul-2016')
w7_start = pd.to_datetime('16-jul-2016')
w7_end = pd.to_datetime('22-jul-2016')
w8_start = pd.to_datetime('23-jul-2016')
w8_end = pd.to_datetime('29-jul-2016')

desktop = 'C:/users/amit/desktop'


def week(df, col):
    if (df[col] >=w1_start) & (df[col] <= w1_end):
        df['week'] = 'W1'
    elif (df[col]>=w2_start) & (df[col] <= w2_end):
        df['week'] = 'W2'
    elif (df[col] >=w3_start) & (df[col] <= w3_end):
        df['week'] = 'W3'
    elif (df[col] >=w4_start) & (df[col] <= w4_end):
        df['week'] = 'W4'
    elif (df[col]>=w5_start) & (df[col] <= w5_end):
        df['week'] = 'W5'
    elif (df[col] >=w6_start) & (df[col] <= w6_end):
        df['week'] = 'W6'
    elif (df[col] >=w7_start) & (df[col] <= w7_end):
        df['week'] = 'W7'
    else: df['week'] = 'W8'

    return df


def nps(filename):
    df = pd.read_csv(filename)
    #extracting only closed and service complete bookings
    #df = df[df['Status'].isin(['service_complete','closed'])]

    #calculating nps and writing it to file
    nps = df.groupby(['week'])['nps'].agg(['size','count','mean'])
    nps.rename(index = str, columns = {'size':'Total Bookings','count':'Total Bookings with Feedback','mean':'NPS'})
    nps_city = df.groupby(['booking_month','City'])['nps'].agg(['size','count','mean'])
    nps_city.rename(index = str, columns = {'size':'Total Bookings','count':'Total Bookings with Feedback','mean':'NPS'})

    output_file = os.path.join(os.path.dirname(filename),'output\[nps].xlsx')
    writer = pd.ExcelWriter(output_file)
    nps.to_excel(writer, sheet_name = 'nps')
    nps_city.to_excel(writer, sheet_name = 'nps_city')
    
    #analyzing bad rating reason
    #total feedback to calculate percentage feedbacks in the bad feedback rating
    total_feedbacks = df.groupby('week')['nps'].count()
    #http://stackoverflow.com/questions/17116814/pandas-how-do-i-split-text-in-a-column-into-multiple-rows - used this answer to do the following analysis
    df = df[df['Bad rating reason'].notnull()]
    s = df['Bad rating reason'].str.split(',').apply(pd.Series, 1).stack()
    s.index = s.index.droplevel(-1)
    s.name = 'Bad rating reason'
    del df['Bad rating reason']
    df = df.join(s)

    bad_rating_reason = df.groupby(['week','Bad rating reason','Feedback'])['Booking ID'].count()
    bad_rating_reason.to_csv('tmp.csv')
    #bad_rating_reason = bad_rating_reason.div(total_feedbacks, level = 0)
    #bad_rating_reason.to_frame().to_excel(writer, sheet_name = 'bad_rating_analysis')
    #writer.save()

    return



def main():
    filename = sys.argv[1]
    columns_to_use = ['Booking ID','City','requested_date','nps','Bad rating reason','booking_month']
    df = pd.read_csv(filename, usecols = columns_to_use, skiprows = range(1,50000))

    #converting 'requested_date to datetime column
    df['requested_date'] = pd.to_datetime(df['requested_date'])
    df = df[(df['requested_date'] >= w1_start) & (df['requested_date'] <=w8_end) & (df['City'] == 'Mumbai')]
    df = df.apply(week, args=('requested_date',), axis = 1)


    sns.set(rc = {'figure.figsize': (20,10)})
    #nps = df.groupby('week').agg({'nps':{'count','mean'}})
    nps = df.groupby('week')
    nps_number = df.groupby(['week','nps'])['Booking ID'].count().divide(df.groupby('week')['nps'].count()).unstack(level = 1)
    nps_number['NPS'] = nps_number[1.0] - nps_number[-1.0]
    #nps.rename('NPS', inplace = True)
    nps_plot = nps_number.plot(color = ['r','b','g','k'])
    nps_plot.set(xticklabels = ["%s\n$Requested$=%d\n$Feedbacks$=%d\n$P$=%2.1f"%(k,v['Booking ID'].count(),v['nps'].count(),100*v['nps'].count()/float(v['Booking ID'].count())) for k,v in nps])
    plt.legend(('Feedback = 1,2','Feedback = 3','Feedback = 4,5','NPS'), fontsize = 18, loc = 'best')
    plt.ylabel('% of All Feedbacks', fontsize = 18)
    plt.xlabel('Week', fontsize = 18)
    plt.title('NPS_Analysis', fontsize = 28)
    plt.suptitle('')

    nps_plot.text(.05,.85,'W1 ='+w1_start.strftime('%d%b%y')+'-'+w1_end.strftime('%d%b%y')+', W2 ='+w2_start.strftime('%d%b%y')+'-'+w2_end.strftime('%d%b%y'),transform = nps_plot.transAxes, ha='left',va='center',fontsize = 18)
    nps_plot.text(.05,.8,'W3 ='+w3_start.strftime('%d%b%y')+'-'+w3_end.strftime('%d%b%y')+', W4 ='+w4_start.strftime('%d%b%y')+'-'+w4_end.strftime('%d%b%y'),transform = nps_plot.transAxes, ha='left',va='center',fontsize = 18)
    nps_plot.text(.05,.75,'W5 ='+w5_start.strftime('%d%b%y')+'-'+w5_end.strftime('%d%b%y')+', W6 ='+w6_start.strftime('%d%b%y')+'-'+w6_end.strftime('%d%b%y'),transform = nps_plot.transAxes, ha='left',va='center',fontsize = 18)
    nps_plot.text(.05,.7,'W7 ='+w7_start.strftime('%d%b%y')+'-'+w7_end.strftime('%d%b%y')+', W8 ='+w8_start.strftime('%d%b%y')+'-'+w8_end.strftime('%d%b%y'),transform = nps_plot.transAxes, ha='left',va='center',fontsize = 18)
    nps_plot.tick_params(axis = 'y', labelsize = 18)
    nps_plot.tick_params(axis = 'x', labelsize = 18)
    plt.tight_layout()
    #nps_plot.text(.5,.9,nps, transform = nps_plot.transAxes, ha = 'center', va = 'center')
    #plt.show()
    plt.savefig(os.path.join(desktop,'NPS_numbers.png'))

    df1 = df.copy(deep = True)
    df = df[df['Bad rating reason'].notnull()]
    s = df['Bad rating reason'].str.split(',').apply(pd.Series, 1).stack()
    s.index = s.index.droplevel(-1)
    s.name = 'Bad rating reason'
    del df['Bad rating reason']
    df = df.join(s)

    #merging Pickup/Delivery into Logistics and Iron/Packagin into Quality
    #df['Bad rating reason'] = df['Bad rating reason'].replace({'delivery_not_done_in_requested_time':'logistics_pain','pick_up_not_done_in_requested_time':'logistics_pain','unsatisfactory_quality_iron_packaging':'quality_pain','unsatisfactory_quality_wash_dry_clean':'quality_pain'})
    df['nps_split'] = ['-ve' if x == -1 else '+ve' for x in df['nps']]

    sns.set(rc = {'figure.figsize': (20,10)})
    bad_rating_reason = df[df['Bad rating reason'].isin(['unsatisfactory_customer_support_on_call_email','overall_service_took_more_time_than_promised'])].groupby(['nps_split','week','Bad rating reason'])['Booking ID'].count().divide(df1.groupby('week')['Booking ID'].count()*.01).unstack(level = 1)
    fig = plt.figure()
    feedback_reason = bad_rating_reason.plot.bar()
    #feedback_reason.set_xticklabels(["%s\n$Requested$=%d\n$reasons$=%d\n$P$=%2.1f"%(k,v['Booking ID'].size,v['Booking ID'].count(),100*v['Booking ID'].count()/float(v['Booking ID'].count())) for k,v in reason], rotation = 0)
    for p in feedback_reason.patches:
        feedback_reason.annotate(str(round(p.get_height(),1)), (p.get_x() * 1.01, p.get_height() * 1.01))
    plt.legend(fontsize = 18, loc = 'upper left')
    plt.ylabel('% of Requested Bookings', fontsize = 18)
    plt.xlabel('Week', fontsize = 18)
    plt.title('NPS_Reasons_Analysis_CC+TAT', fontsize = 28)
    plt.suptitle('')

    feedback_reason.tick_params(axis = 'y', labelsize = 18)
    feedback_reason.tick_params(axis = 'x', labelsize = 18)
    plt.tight_layout()
    feedback_reason.text(.7,.95,'+ve = Feedback=3,4,5; -ve = Feedback=1,2', transform = feedback_reason.transAxes, va = 'center', ha = 'left', fontsize = 18, color = 'r')
    feedback_reason.text(.7,.9,'W1 ='+w1_start.strftime('%d%b%y')+'-'+w1_end.strftime('%d%b%y')+', W2 ='+w2_start.strftime('%d%b%y')+'-'+w2_end.strftime('%d%b%y'),transform = feedback_reason.transAxes, ha='left',va='center',fontsize = 18)
    feedback_reason.text(.7,.85,'W3 ='+w3_start.strftime('%d%b%y')+'-'+w3_end.strftime('%d%b%y')+', W4 ='+w4_start.strftime('%d%b%y')+'-'+w4_end.strftime('%d%b%y'),transform = feedback_reason.transAxes, ha='left',va='center',fontsize = 18)
    feedback_reason.text(.7,.8,'W5 ='+w5_start.strftime('%d%b%y')+'-'+w5_end.strftime('%d%b%y')+', W6 ='+w6_start.strftime('%d%b%y')+'-'+w6_end.strftime('%d%b%y'),transform = feedback_reason.transAxes, ha='left',va='center',fontsize = 18)
    feedback_reason.text(.7,.75,'W7 ='+w7_start.strftime('%d%b%y')+'-'+w7_end.strftime('%d%b%y')+', W8 ='+w8_start.strftime('%d%b%y')+'-'+w8_end.strftime('%d%b%y'),transform = feedback_reason.transAxes, ha='left',va='center',fontsize = 18)
    #plt.show()
    plt.savefig(os.path.join(desktop,'NPS_reasons_CC+TAT.png'))


    #reason = df.groupby(['week','nps_split'])
    sns.set(rc = {'figure.figsize': (20,10)})
    bad_rating_reason = df[df['Bad rating reason'].isin(['unsatisfactory_quality_iron_packaging','unsatisfactory_quality_wash_dry_clean'])].groupby(['nps_split','week','Bad rating reason'])['Booking ID'].count().divide(df1.groupby('week')['Booking ID'].count()*.01).unstack(level = 2)
    fig = plt.figure()
    feedback_reason = bad_rating_reason.plot.bar()
    #feedback_reason.set_xticklabels(["%s\n$Requested$=%d\n$reasons$=%d\n$P$=%2.1f"%(k,v['Booking ID'].size,v['Booking ID'].count(),100*v['Booking ID'].count()/float(v['Booking ID'].count())) for k,v in reason], rotation = 0)
    for p in feedback_reason.patches:
        feedback_reason.annotate(str(round(p.get_height(),1)), (p.get_x() * 1.01, p.get_height() * 1.01))
    plt.legend(fontsize = 18, loc = 'upper left')
    plt.ylabel('% of Requested Bookings', fontsize = 18)
    plt.xlabel('Week', fontsize = 18)
    plt.title('NPS_Reasons_Analysis_Quality', fontsize = 28)
    plt.suptitle('')

    feedback_reason.tick_params(axis = 'y', labelsize = 18)
    feedback_reason.tick_params(axis = 'x', labelsize = 18)
    plt.tight_layout()
    feedback_reason.text(.7,.95,'+ve = Feedback=3,4,5; -ve = Feedback=1,2', transform = feedback_reason.transAxes, va = 'center', ha = 'left', fontsize = 18, color = 'r')
    feedback_reason.text(.7,.9,'W1 ='+w1_start.strftime('%d%b%y')+'-'+w1_end.strftime('%d%b%y')+', W2 ='+w2_start.strftime('%d%b%y')+'-'+w2_end.strftime('%d%b%y'),transform = feedback_reason.transAxes, ha='left',va='center',fontsize = 18)
    feedback_reason.text(.7,.85,'W3 ='+w3_start.strftime('%d%b%y')+'-'+w3_end.strftime('%d%b%y')+', W4 ='+w4_start.strftime('%d%b%y')+'-'+w4_end.strftime('%d%b%y'),transform = feedback_reason.transAxes, ha='left',va='center',fontsize = 18)
    feedback_reason.text(.7,.8,'W5 ='+w5_start.strftime('%d%b%y')+'-'+w5_end.strftime('%d%b%y')+', W6 ='+w6_start.strftime('%d%b%y')+'-'+w6_end.strftime('%d%b%y'),transform = feedback_reason.transAxes, ha='left',va='center',fontsize = 18)
    feedback_reason.text(.7,.75,'W7 ='+w7_start.strftime('%d%b%y')+'-'+w7_end.strftime('%d%b%y')+', W8 ='+w8_start.strftime('%d%b%y')+'-'+w8_end.strftime('%d%b%y'),transform = feedback_reason.transAxes, ha='left',va='center',fontsize = 18)
    #plt.show()
    plt.savefig(os.path.join(desktop,'NPS_reasons_Quality.png'))



    sns.set(rc = {'figure.figsize': (20,10)})
    bad_rating_reason = df[df['Bad rating reason'].isin(['delivery_not_done_in_requested_time','pick_up_not_done_in_requested_time'])].groupby(['nps_split','week','Bad rating reason'])['Booking ID'].count().divide(df1.groupby('week')['Booking ID'].count()*.01).unstack(level = 1)
    fig = plt.figure()
    feedback_reason = bad_rating_reason.plot.bar()
    #feedback_reason.set_xticklabels(["%s\n$Requested$=%d\n$reasons$=%d\n$P$=%2.1f"%(k,v['Booking ID'].size,v['Booking ID'].count(),100*v['Booking ID'].count()/float(v['Booking ID'].count())) for k,v in reason], rotation = 0)
    for p in feedback_reason.patches:
        feedback_reason.annotate(str(round(p.get_height(),1)), (p.get_x() * 1.01, p.get_height() * 1.01))
    plt.legend(fontsize = 18, loc = 'upper left')
    plt.ylabel('% of Requested Bookings', fontsize = 18)
    plt.xlabel('Week', fontsize = 18)
    plt.title('NPS_Reasons_Analysis_Logistics', fontsize = 28)
    plt.suptitle('')

    feedback_reason.tick_params(axis = 'y', labelsize = 18)
    feedback_reason.tick_params(axis = 'x', labelsize = 18)
    plt.tight_layout()
    feedback_reason.text(.7,.95,'+ve = Feedback=3,4,5; -ve = Feedback=1,2', transform = feedback_reason.transAxes, va = 'center', ha = 'left', fontsize = 18, color = 'r')
    feedback_reason.text(.7,.9,'W1 ='+w1_start.strftime('%d%b%y')+'-'+w1_end.strftime('%d%b%y')+', W2 ='+w2_start.strftime('%d%b%y')+'-'+w2_end.strftime('%d%b%y'),transform = feedback_reason.transAxes, ha='left',va='center',fontsize = 18)
    feedback_reason.text(.7,.85,'W3 ='+w3_start.strftime('%d%b%y')+'-'+w3_end.strftime('%d%b%y')+', W4 ='+w4_start.strftime('%d%b%y')+'-'+w4_end.strftime('%d%b%y'),transform = feedback_reason.transAxes, ha='left',va='center',fontsize = 18)
    feedback_reason.text(.7,.8,'W5 ='+w5_start.strftime('%d%b%y')+'-'+w5_end.strftime('%d%b%y')+', W6 ='+w6_start.strftime('%d%b%y')+'-'+w6_end.strftime('%d%b%y'),transform = feedback_reason.transAxes, ha='left',va='center',fontsize = 18)
    feedback_reason.text(.7,.75,'W7 ='+w7_start.strftime('%d%b%y')+'-'+w7_end.strftime('%d%b%y')+', W8 ='+w8_start.strftime('%d%b%y')+'-'+w8_end.strftime('%d%b%y'),transform = feedback_reason.transAxes, ha='left',va='center',fontsize = 18)
    #plt.show()
    plt.savefig(os.path.join(desktop,'NPS_reasons_Logistics.png'))
    '''
    sns.set(rc = {'figure.figsize': (20,10)})
    bad_rating_reason = df[df['nps'] <> -1].groupby(['week','Bad rating reason'])['Booking ID'].count().divide(df.groupby('week')['Booking ID'].count()).unstack(level = 1)
    fig = plt.figure()
    feedback_reason = bad_rating_reason.plot.bar(stacked=True)
    plt.legend(('Logistics_pain','TAT Breach','Quality','CC'), fontsize = 18, loc = 'best')
    plt.ylabel('% of Requested Bookings', fontsize = 18)
    plt.xlabel('Week', fontsize = 18)
    plt.title('NPS_Reasons_Analysis_Feedback=3,4,5', fontsize = 28)
    plt.suptitle('')

    feedback_reason.tick_params(axis = 'y', labelsize = 18)
    feedback_reason.tick_params(axis = 'x', labelsize = 18)
    plt.tight_layout()
    #plt.show()
    plt.savefig(os.path.join(desktop,'NPS_reasons_3,4,5_Feedback.png'))
    '''


if __name__ == '__main__':
    main()
