import sys
import ipdb
import matplotlib.pyplot as plt
import os
import pandas as pd
import seaborn as sns



def week(df, col):
    if (df[col] >=w5_start) & (df[col] <= w5_end + pd.Timedelta('1 day')):
        df['week'] = 'W5'
    elif (df[col]>=w6_start) & (df[col] <= w6_end + pd.Timedelta('1 day')):
        df['week'] = 'W6'
    elif (df[col] >=w7_start) & (df[col] <= w7_end + pd.Timedelta('1 day')):
        df['week'] = 'W7'
    else: df['week'] = 'W8'

    return df



def modify_FRT(df):
    #modifying FRT of issues created in non_business hours (issues received between 12 midnight to 8AM)
    if df['Time of creation'].hour >= 22:
        tmp = pd.to_datetime((df['Time of creation'] + pd.Timedelta('1 day')).strftime('%d-%m-%Y') + ' ' + '8:00:00')
        df['First response time (minutes)'] = df['First response time (minutes)'] - (tmp - df['Time of creation']).seconds/60.0
        df['Time of creation'] = tmp 
    elif df['Time of creation'].hour <= 7:
        tmp = pd.to_datetime(df['Time of creation'].strftime('%d-%m-%Y') + ' ' + '8:00:00')
        df['First response time (minutes)'] = df['First response time (minutes)'] - (tmp - df['Time of creation']).seconds/60.0
        df['Time of creation'] = tmp 


    return df



def FRT(df):
    df['First response time (minutes)'] = pd.to_numeric(df['First response time (minutes)'], errors = 'coerce')
    df['Time of creation'] = pd.to_datetime(df['Time of creation'], errors = 'coerce', dayfirst = True)
    #selecting last 4 weeks
    df = df[(df['Time of creation'] >= w5_start) & (df['Time of creation'] <= w8_end + pd.Timedelta('1 day'))]
    #apply week numbers
    df = df.apply(week, args = ('Time of creation',), axis = 1)
    #modifying FRT for issues created in non_business hours
    df = df.apply(modify_FRT, axis = 1)
    #modifying FRT for issues created in Business hours - 8AM to 10PM 
    tmp = df['Time of creation'] + pd.to_timedelta(df['First response time (minutes)'], unit = 'm')
    df['First response time (minutes)'] = df['First response time (minutes)'] - (600*((tmp.dt.date-df['Time of creation'].dt.date)).dt.days) 

    df1 = df[(df['First response time (minutes)'].notnull()) & (df['L2 subtype'].isin(['pickup','delivery'])) & ((df['Ownership during close with'].isin(['mumbai'])) | (df['Closed by'].isin(['rishabh@doormint.in','kunal@doormint.in','keithbuthello12@gmail.com','rehman@doormint.in','bhushandhende4@gmail.com'])))]

    grouped = df1.groupby(['L2 subtype','week'])
    total = df1.groupby('week')['Booking id'].count()
    #calculating KPIs
    total_issues = df1.groupby('week')['First response time (minutes)'].count()
    kpi = pd.Series('', index = ['KPI'])
    issues_20 = df1[df1['First response time (minutes)'] <= 20].groupby('week')['First response time (minutes)'].count()/total_issues
    kpi['% issues replied within 20 min'] = ''
    kpi = kpi.append((100*issues_20).round(1))
    kpi['% issues replied within 60 min'] = ''
    issues_60 = df1[df1['First response time (minutes)'] <= 60].groupby('week')['First response time (minutes)'].count()/total_issues
    kpi = kpi.append((100*issues_60).round(1))

    sns.set(rc = {'figure.figsize': (25,12)})
    frt = df1.boxplot(column = 'First response time (minutes)', by = ['L2 subtype','week'], whis = [10,75], showfliers = False)
    #frt.set(xticklabels = ["%s\n$N$=%d,\n$P$=%2.1f,\n$\mu$=%2.1f,\n$90P$=%2.1f"%(k, len(v), 100*len(v)/float(total['W5']) if k[1] == 'W5' else (100*len(v)/float(total['W6']) if k[1] == 'W6' else (100*len(v)/float(total['W7']) if k[1] == 'W7' else 'W8')), v['First response time (minutes)'].mean(), v['First response time (minutes)'].quantile(.9)) for k,v in grouped])
    frt.set(xticklabels = ["%s\n$N$=%d\n$\mu$=%2.1f,\n$90P$=%2.1f"%(k, len(v), v['First response time (minutes)'].mean(), v['First response time (minutes)'].quantile(.9)) for k,v in grouped])
    frt.set(title = '')
    plt.ylabel('First Response Time (in minutes)', fontsize = 24)
    plt.xlabel('Team-L2_subtype-Week', fontsize = 24)
    plt.suptitle('Distribution of FRT of Toolbox ISSUES (only Logisitcs)', fontsize = 28)
    frt.text(.9,.98,'W5 ='+w5_start.strftime('%d%b%y')+'-'+w5_end.strftime('%d%b%y')+', W6 ='+w6_start.strftime('%d%b%y')+'-'+w6_end.strftime('%d%b%y'), transform = frt.transAxes, ha='center', va='center', fontsize = 16, color = 'red')
    frt.text(.9,.95,'W7 ='+w7_start.strftime('%d%b%y')+'-'+w7_end.strftime('%d%b%y')+', W8 ='+w8_start.strftime('%d%b%y')+'-'+w8_end.strftime('%d%b%y'), transform = frt.transAxes, ha='center', va='center', fontsize = 16, color = 'red')
    frt.text(.01,1.0, kpi, transform = frt.transAxes, ha='left', va='top', fontsize = 16, color = 'black')
    frt.tick_params(axis = 'x', labelsize = 18)
    frt.tick_params(axis = 'y', labelsize = 18)
    plt.tight_layout()
    plt.savefig(os.path.join(desktop,'logitics_FRT_distribution.png'))

    return


def resolution_time(df):
    df = df[~df['L2 subtype'].isin(['Duplicate Booking','Feedback','Refund'])]
    df['L2 subtype'] = df['L2 subtype'].str.lower()
    df['Closed at'] = pd.to_datetime(df['Closed at'], dayfirst = True)
    df2 = df[(df['Closed at'] >= w7_start) & (df['Closed at'] <= w8_end + pd.Timedelta('1 day')) & (df['Active'] == False)]
    #apply week numbers
    df2 = df2.apply(week, args = ('Closed at',), axis = 1)
    df2['Time taken to close(hours)'] = pd.to_numeric(df['Time taken to close(hours)'], errors = 'coerce')
    df2['L2 subtype'].replace({'Clothes Lost/Exchanged':'Lost/Ex'}, inplace = True)

    sns.set(rc = {'figure.figsize': (25,12)})
    rt = df2.boxplot(column = 'Time taken to close(hours)', by = ['L2 subtype','week'], whis = [10,75], showfliers = False)
    grouped = df2.groupby(['L2 subtype','week'])
    total = df2.groupby('week')['Booking id'].count()
    rt.set(xticklabels = ["%s\n$n$=%d,$\mu$=%2.1f\n$80P$=%2.1f\n$90P$=%2.1f"%(k, len(v), v['Time taken to close(hours)'].mean(), v['Time taken to close(hours)'].quantile(.8), v['Time taken to close(hours)'].quantile(.9)) for k,v in grouped])
    rt.set(title = '')
    plt.xlabel('week-L2 subtypes',fontsize = 24)
    plt.ylabel('resolution times(in hours)', fontsize = 24)
    plt.suptitle('Distribution of Resolution Times of Toolbox ISSUES', fontsize = 28)
    rt.text(.9,.98,'W5 ='+w5_start.strftime('%d%b%y')+'-'+w5_end.strftime('%d%b%y')+', W6 ='+w6_start.strftime('%d%b%y')+'-'+w6_end.strftime('%d%b%y'),transform = rt.transAxes, ha='center',va='center',fontsize = 16, color = 'red')
    rt.text(.9,.95,'W7 ='+w7_start.strftime('%d%b%y')+'-'+w7_end.strftime('%d%b%y')+', W8 ='+w8_start.strftime('%d%b%y')+'-'+w8_end.strftime('%d%b%y'), transform = rt.transAxes, ha='center', va='center', fontsize = 16, color = 'red')
    rt.tick_params(axis = 'x', labelsize = 12)
    rt.tick_params(axis = 'y', labelsize = 12)
    plt.tight_layout()
    #plt.savefig(os.path.join(desktop,'Resolution_times_distribution_by_L2Subtypes.png'))
    plt.show()

    return

def logistics_l3(df):
    df['requested_date'] = pd.to_datetime(df['requested_date'], dayfirst = True)
    df = df[(df['requested_date'] >= w7_start) & (df['requested_date'] <= w8_end + pd.Timedelta('1 day')) & (df['Active'] == False)]
    #apply week numbers
    df = df.apply(week, args = ('requested_date',), axis = 1)
    #df['L3 subtype'].replace({'Request for change in pick up time slot : early, late, reschedule':'change_time_slot','Pick up pending and was not done in the requested time slot':'pickup_not_in_requested_slot','Customer not available in the requested time slot':'cust._not_available'}, inplace = True)
    #taking only customer pickup issues
    pickup = df[(df['L1 subtype'] == 'Pickup') & (df['FreshDesk/Internal'].notnull())]
    #tmp code
    #pickup.replace({'change_time_slot':'A','pickup_not_in_requested_slot':'B','cust._not_available':'C','cancel booking':'D','Reschedule the pickup':'E','Priority pickup':'F','Pickup stock out':'G','Pickup request at different address':'H','Pickup boy number request':'I','Pickup boy complaints':'J','Out of geography':'K','Others':'L'}, inplace = True)
    #label = pd.Series(['','','','','','','','','','','',''], index = ['A=change_time_slot','B=pickup_not_in_requested_slot','C=cust._not_available','D=cancel booking','E=Reschedule the pickup','F=Priority Pickup','G=Pickup stock out', 'H=Pickup request at different address', 'I=Pickup boy number request', 'J=Pickup boy complaints', 'K=Out of geography', 'L=Others'])
    total = pd.Series([''], index = ['Total Pickup Issues'])
    total = total.append(pickup.groupby('week')['ID'].count())
    pickup = 100*pickup.groupby(['week','L3 subtype'])['ID'].count().divide(pickup.groupby('week')['ID'].count(), axis = 0)
    sns.set(rc = {'figure.figsize': (25,13)})
    pickup_L3 = pickup.unstack(level = 0).plot.barh(legend = True)
    #feedback_reason.set_xticklabels(["%s\n$Requested$=%d\n$reasons$=%d\n$P$=%2.1f"%(k,v['Booking ID'].size,v['Booking ID'].count(),100*v['Booking ID'].count()/float(v['Booking ID'].count())) for k,v in reason], rotation = 0)
    pickup_L3.tick_params(axis = 'x', labelsize = 18)
    pickup_L3.tick_params(axis = 'y', labelsize = 18)
    plt.ylabel('L3_subtypes_pickup_issues', fontsize = 20)
    plt.xlabel('% of Pickup Issues', fontsize = 20)
    plt.title('Pickup Issues-L3 reason analysis', fontsize = 28)
    plt.suptitle('')
    plt.legend(fontsize = 18)
    pickup_L3.text(.65,.25,'W5 ='+w5_start.strftime('%d%b%y')+'-'+w5_end.strftime('%d%b%y')+', W6 ='+w6_start.strftime('%d%b%y')+'-'+w6_end.strftime('%d%b%y'),transform = pickup_L3.transAxes, ha='left',va='center',fontsize = 19)
    pickup_L3.text(.65,.22,'W7 ='+w7_start.strftime('%d%b%y')+'-'+w7_end.strftime('%d%b%y')+', W8 ='+w8_start.strftime('%d%b%y')+'-'+w8_end.strftime('%d%b%y'),transform = pickup_L3.transAxes, ha='left',va='center',fontsize = 19)
    pickup_L3.text(.65,.19,total, transform = pickup_L3.transAxes, ha='left',va='top',fontsize = 19)
    #pickup_L3.text(.75,.4, label, transform = pickup_L3.transAxes, ha = 'left', va='top', fontsize = 19)
    plt.tight_layout()
    plt.savefig(os.path.join(desktop,'pickup_issues_L3_subtypes.png'))

    delivery = df[(df['L1 subtype'] == 'Delivery') & (df['FreshDesk/Internal'].notnull())]
    #delivery['L3 subtype'].replace({'Request for change in delivery time slot : early, late, reschedule':'change_time_slot'}, inplace = True)
    total = pd.Series([''], index = ['Total Delivery Issues'])
    total = total.append(delivery.groupby('week')['ID'].count())
    delivery = 100*delivery.groupby(['week','L3 subtype'])['ID'].count().divide(delivery.groupby('week')['ID'].count(), axis = 0)
    sns.set(rc = {'figure.figsize': (25,13)})
    delivery_L3 = delivery.unstack(level = 0).plot.barh(legend = True)
    delivery_L3.tick_params(axis = 'x', labelsize = 18)
    delivery_L3.tick_params(axis = 'y', labelsize = 18)
    plt.ylabel('L3_subtypes_delivery_issues', fontsize = 18)
    plt.xlabel('% of Delivery Issues', fontsize = 18)
    plt.title('Delivery Issues-L3 reason analysis', fontsize = 28)
    plt.legend(fontsize = 18)
    plt.suptitle('')
    delivery_L3.text(.65,.8,'W5 ='+w5_start.strftime('%d%b%y')+'-'+w5_end.strftime('%d%b%y')+', W6 ='+w6_start.strftime('%d%b%y')+'-'+w6_end.strftime('%d%b%y'),transform = delivery_L3.transAxes, ha='left',va='center',fontsize = 19)
    delivery_L3.text(.65,.75,'W7 ='+w7_start.strftime('%d%b%y')+'-'+w7_end.strftime('%d%b%y')+', W8 ='+w8_start.strftime('%d%b%y')+'-'+w8_end.strftime('%d%b%y'),transform = delivery_L3.transAxes, ha='left',va='center',fontsize = 19)
    delivery_L3.text(.65,.7,total, transform = delivery_L3.transAxes, ha='left',va='top',fontsize = 19)
    plt.tight_layout()
    plt.savefig(os.path.join(desktop,'delivery_issues_L3_subtypes.png'))


    return

def quality_l3(df):
    df['requested_date'] = pd.to_datetime(df['requested_date'], dayfirst = True)
    #change this next week
    df = df[df['requested_date'] >= pd.Timestamp('22-aug-2016')]
    df = df[(df['requested_date'] >= w5_start) & (df['requested_date'] <= w8_end + pd.Timedelta('1 day'))]
    #apply week numbers
    df = df.apply(week, args = ('requested_date',), axis = 1)
    #df['L3 subtype'].replace({'Bad packaging':'A','Color Fade/color change':'B','Linen/embroidery damage':'C','Post-Process Stains':'D','Shrinkage':'E','Wet clothes/Bad smell':'F','ironing_issue':'G','others':'H','stains_not_removed':'I'},inplace = True)
    quality_dry_cleaning = df[(df['L1 subtype'] == 'Wash quality') & (df['L2 subtype'] == 'Dry cleaning')]
    #quality = 100*quality.groupby(['week','L3 subtype'])['ID'].count().divide(quality.groupby('week')['ID'].count(), axis = 0)
    quality_dry_cleaning = quality_dry_cleaning.groupby(['L3 subtype','week'])['ID'].count()
    sns.set(rc = {'figure.figsize': (25,13)})
    quality_L3 = quality_dry_cleaning.unstack(level = 1).plot.barh(stacked=False, legend = True)
    plt.legend(fontsize = 18)
    #plt.legend(('Dry Cleaning','Wash and Iron Prime','Wash and Iron by weight'), fontsize = 18, loc = 'best')
    #label = pd.Series(['','','','','','','','',''], index = ['A = Bad Packaging','B = Color Fade/color change','C = Linen/Embroidery damage','D = Post-process Stains','E = Shrinkage','F = Wet Clothes/Bad Smell','G = Ironing Issues','H = Others', 'I = Stains_not_removed'])
    plt.ylabel('L3_subtypes_quality_issues', fontsize = 18)
    plt.xlabel('Number of Quality Issues', fontsize = 18)
    plt.title('Quality Issues-L3 reason analysis--Dry Cleaning', fontsize = 28)
    plt.suptitle('')
    quality_L3.text(.7,.45,'W5 ='+w5_start.strftime('%d%b%y')+'-'+w5_end.strftime('%d%b%y')+', W6 ='+w6_start.strftime('%d%b%y')+'-'+w6_end.strftime('%d%b%y'),transform = quality_L3.transAxes, ha='left',va='center',fontsize = 19)
    quality_L3.text(.7,.42,'W7 ='+w7_start.strftime('%d%b%y')+'-'+w7_end.strftime('%d%b%y')+', W8 ='+w8_start.strftime('%d%b%y')+'-'+w8_end.strftime('%d%b%y'),transform = quality_L3.transAxes, ha='left',va='center',fontsize = 19)
    #quality_L3.text(.8,.35, label, transform = quality_L3.transAxes, ha = 'left', va='top', fontsize = 19)
    quality_L3.tick_params(axis = 'y', labelsize = 18)
    quality_L3.tick_params(axis = 'x', labelsize = 18)
    plt.tight_layout()
    plt.savefig(os.path.join(desktop,'Quality_issues_Dry_Cleaning.png'))

    quality_dry_cleaning = df[(df['L1 subtype'] == 'Wash quality') & (df['L2 subtype'] == 'Wash and iron prime')]
    #quality = 100*quality.groupby(['week','L3 subtype'])['ID'].count().divide(quality.groupby('week')['ID'].count(), axis = 0)
    quality_dry_cleaning = quality_dry_cleaning.groupby(['L3 subtype','week'])['ID'].count()
    sns.set(rc = {'figure.figsize': (25,13)})
    quality_L3 = quality_dry_cleaning.unstack(level = 1).plot.barh(stacked=False, legend = True)
    plt.legend(fontsize = 18)
    #plt.legend(('Dry Cleaning','Wash and Iron Prime','Wash and Iron by weight'), fontsize = 18, loc = 'best')
    #label = pd.Series(['','','','','','','','',''], index = ['A = Bad Packaging','B = Color Fade/color change','C = Linen/Embroidery damage','D = Post-process Stains','E = Shrinkage','F = Wet Clothes/Bad Smell','G = Ironing Issues','H = Others', 'I = Stains_not_removed'])
    plt.ylabel('L3_subtypes_quality_issues', fontsize = 18)
    plt.xlabel('Number of Quality Issues', fontsize = 18)
    plt.title('Quality Issues-L3 reason analysis--Wash and Iron Prime', fontsize = 28)
    plt.suptitle('')
    quality_L3.text(.7,.45,'W5 ='+w5_start.strftime('%d%b%y')+'-'+w5_end.strftime('%d%b%y')+', W6 ='+w6_start.strftime('%d%b%y')+'-'+w6_end.strftime('%d%b%y'),transform = quality_L3.transAxes, ha='left',va='center',fontsize = 19)
    quality_L3.text(.7,.42,'W7 ='+w7_start.strftime('%d%b%y')+'-'+w7_end.strftime('%d%b%y')+', W8 ='+w8_start.strftime('%d%b%y')+'-'+w8_end.strftime('%d%b%y'),transform = quality_L3.transAxes, ha='left',va='center',fontsize = 19)
    #quality_L3.text(.8,.35, label, transform = quality_L3.transAxes, ha = 'left', va='top', fontsize = 19)
    quality_L3.tick_params(axis = 'y', labelsize = 18)
    quality_L3.tick_params(axis = 'x', labelsize = 18)
    plt.tight_layout()
    plt.savefig(os.path.join(desktop,'Quality_issues_L3_subtypes_Wash and Iron Prime.png'))

    
    quality_dry_cleaning = df[(df['L1 subtype'] == 'Wash quality') & (df['L2 subtype'] == 'Wash and iron by weight')]
    #quality = 100*quality.groupby(['week','L3 subtype'])['ID'].count().divide(quality.groupby('week')['ID'].count(), axis = 0)
    quality_dry_cleaning = quality_dry_cleaning.groupby(['L3 subtype','week'])['ID'].count()
    sns.set(rc = {'figure.figsize': (25,13)})
    quality_L3 = quality_dry_cleaning.unstack(level = 1).plot.barh(stacked=False, legend = True)
    plt.legend(fontsize = 18)
    #plt.legend(('Dry Cleaning','Wash and Iron Prime','Wash and Iron by weight'), fontsize = 18, loc = 'best')
    #label = pd.Series(['','','','','','','','',''], index = ['A = Bad Packaging','B = Color Fade/color change','C = Linen/Embroidery damage','D = Post-process Stains','E = Shrinkage','F = Wet Clothes/Bad Smell','G = Ironing Issues','H = Others', 'I = Stains_not_removed'])
    plt.ylabel('L3_subtypes_quality_issues', fontsize = 18)
    plt.xlabel('Number of Quality Issues', fontsize = 18)
    plt.title('Quality Issues-L3 reason analysis--Wash and Iron by weight', fontsize = 28)
    plt.suptitle('')
    quality_L3.text(.7,.45,'W5 ='+w5_start.strftime('%d%b%y')+'-'+w5_end.strftime('%d%b%y')+', W6 ='+w6_start.strftime('%d%b%y')+'-'+w6_end.strftime('%d%b%y'),transform = quality_L3.transAxes, ha='left',va='center',fontsize = 19)
    quality_L3.text(.7,.42,'W7 ='+w7_start.strftime('%d%b%y')+'-'+w7_end.strftime('%d%b%y')+', W8 ='+w8_start.strftime('%d%b%y')+'-'+w8_end.strftime('%d%b%y'),transform = quality_L3.transAxes, ha='left',va='center',fontsize = 19)
    #quality_L3.text(.8,.35, label, transform = quality_L3.transAxes, ha = 'left', va='top', fontsize = 19)
    quality_L3.tick_params(axis = 'y', labelsize = 18)
    quality_L3.tick_params(axis = 'x', labelsize = 18)
    plt.tight_layout()
    plt.savefig(os.path.join(desktop,'Quality_issues_L3_subtypes_Wash and Iron by weight.png'))

    return

w5_start = pd.to_datetime('8-Aug-2016')
w5_end = pd.to_datetime('14-Aug-2016')
w6_start = pd.to_datetime('15-Aug-2016')
w6_end = pd.to_datetime('21-Aug-2016')
w7_start = pd.to_datetime('22-Aug-2016')
w7_end = pd.to_datetime('28-Aug-2016')
w8_start = pd.to_datetime('29-Aug-2016')
w8_end = pd.to_datetime('04-Sep-2016')

desktop = 'c:/users/amit/desktop'


def main():
    filename = sys.argv[1]
    bookings_file = sys.argv[2]
    df = pd.read_csv(filename)
    bookings = pd.read_csv(bookings_file)
    df = pd.merge(df,bookings[['Booking ID','requested_date']], left_on = 'Booking id', right_on = 'Booking ID', how = 'inner')
    df['Ownership during close with'].replace({'Mumbai Delivery ( After RFD )':'mumbai', 'Mumbai Logistics (pickup)':'mumbai', 'Bangalore logistics (pickup)':'bangalore','Bangalore Delivery ( After RFD )': 'bangalore', 'CC_customers':'CC'}, inplace = True)
    df['L2 subtype'].replace({'Clothes Lost/Exchanged':'lost/ex'}, inplace = True)
    df['L3 subtype'].replace({'Clothes not cleaned properly/Stain not removed':'stains_not_removed','Ironing issue-Poor finishing/iron marks/Lint':'ironing_issue'},inplace = True)
    df['Category'].replace({'Wash and Fold by weight':'Wash and Iron by weight'}, inplace = True)

    #FRT(df[df['City'] == 'Mumbai'])
    #resolution_time(df[df['City'] == 'Mumbai'])
    logistics_l3(df[df['City'] == 'Mumbai'])
    quality_l3(df[df['City'] == 'Mumbai'])

if __name__=='__main__':
    main()
