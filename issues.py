import sys
import ipdb
import matplotlib.pyplot as plt
import os
import pandas as pd
import seaborn as sns


def FRT(df):
    #df1 = all issues created within start_date & end_date by customers and are logistics issues with ownership during close with either with bangalore,mumbai,CC
    df['First response time (minutes)'] = pd.to_numeric(df['First response time (minutes)'], errors = 'coerce')
    df['Time of creation'] = pd.to_datetime(df['Time of creation'], errors = 'coerce', dayfirst = True)
    df = df[(df['Time of creation'] >= w1_start) & (df['Time of creation'] <= w2_end+pd.Timedelta('1 day'))]
    df['week'] = ['W1' if (x>=w1_start) & (x<=w1_end+pd.Timedelta('1 day')) else  'W2' for x in df['Time of creation']]
    df['adjusted_time_of_creation'] = [(x + pd.Timedelta('1 day')).strftime('%d-%m-%y') + ' ' + '8:00:00' if (x.hour >= 22) else x for x in df['Time of creation']]
    df['adjusted_time_of_creation'] = [x.strftime('%d-%m-%y') + ' ' + '8:00:00' if (x.hour <= 7) else x for x in df['Time of creation']]
    df['adjusted_time_of_creation'] = pd.to_datetime(df['adjusted_time_of_creation'], errors = 'coerce')
    df['FRT_time'] = df['Time of creation'] + pd.to_timedelta(df['First response time (minutes)'], unit = 'm')
    df['First response time (minutes)'] = (df['FRT_time'] - df['adjusted_time_of_creation']).fillna(0)
    df['First response time (minutes)'] = [x.seconds/60.0 for x in df['First response time (minutes)']]
    df1 = df[(df['FreshDesk/Internal'].notnull()) & (df['L2 subtype'].isin(['pickup','delivery'])) & (df['Ownership during close with'].isin(['mumbai','CC']))]

    grouped = df1.groupby(['Ownership during close with','L2 subtype','week'])
    total = df1.groupby('week')['Booking id'].count()
    sns.set(rc = {'figure.figsize': (22,12)})
    frt = df1.boxplot(column = 'First response time (minutes)', by = ['Ownership during close with','L2 subtype','week'], whis = [10,75], showfliers = False)
    frt.set(xticklabels = ["%s\n$n$=%d,$p$=%2.1f,$\mu$=%2.1f,\n$90Percentile$=%2.1f"%(k, len(v), 100*len(v)/float(total['W1']) if k[0] == 'W1' else 100*len(v)/float(total['W2']), v['First response time (minutes)'].mean(), v['First response time (minutes)'].quantile(.9)) for k,v in grouped])
    frt.set(title = '')
    plt.ylabel('First Response Time (in minutes)', fontsize = 24)
    plt.xlabel('Team-L2_subtype-Week', fontsize = 24)
    plt.suptitle('Distribution of FRT of Toolbox ISSUES (only Logisitcs)', fontsize = 28)
    frt.text(.2,.9,'W1 ='+w1_start.strftime('%d%b%y')+'-'+w1_end.strftime('%d%b%y')+', W2 ='+w2_start.strftime('%d%b%y')+'-'+w2_end.strftime('%d%b%y'),transform = frt.transAxes, ha='center',va='center',fontsize = 18)
    frt.tick_params(axis = 'x', labelsize = 14)
    plt.tight_layout()
    plt.savefig(os.path.join(desktop,'logitics_FRT_distribution.png'))

    return


def resolution_time(df):
    df = df[~df['L2 subtype'].isin(['Duplicate Booking','Feedback','Refund'])]
    df['L2 subtype'] = df['L2 subtype'].str.lower()
    df['Closed at'] = pd.to_datetime(df['Closed at'], dayfirst = True)
    df2 = df[(df['Closed at'] >= w1_start) & (df['Closed at'] <= w2_end) & (df['Active'] == False)]
    df2['week'] = ['W1' if (x>=w1_start) & (x<=w1_end) else 'W2' for x in df2['Closed at']]
    df2['Time taken to close(hours)'] = pd.to_numeric(df['Time taken to close(hours)'], errors = 'coerce')
    df2['L2 subtype'].replace({'Clothes Lost/Exchanged':'Lost/Ex'}, inplace = True)

    rt = df2.boxplot(column = 'Time taken to close(hours)', by = ['L2 subtype','week'], whis = [10,75], showfliers = False)
    grouped = df2.groupby(['L2 subtype','week'])
    total = df2.groupby('week')['Booking id'].count()
    rt.set(xticklabels = ["%s\n$n$=%d,$p$=%2.1f,$\mu$=%2.1f\n$90Percentile$=%2.1f"%(k, len(v), 100*len(v)/float(total['W1']) if k[0] == 'W1' else 100*len(v)/float(total['W2']), v['Time taken to close(hours)'].mean(), v['Time taken to close(hours)'].quantile(.9)) for k,v in grouped])
    rt.set(title = '')
    plt.xlabel('week-L2 subtypes',fontsize = 24)
    plt.ylabel('resolution times(in hours)', fontsize = 24)
    plt.suptitle('Distribution of Resolution Times of Toolbox ISSUES', fontsize = 28)
    rt.text(.2,.9,'W1 ='+w1_start.strftime('%d%b%y')+'-'+w1_end.strftime('%d%b%y')+', W2 ='+w2_start.strftime('%d%b%y')+'-'+w2_end.strftime('%d%b%y'),transform = rt.transAxes, ha='center',va='center',fontsize = 18)
    rt.tick_params(axis = 'x', labelsize = 10)
    plt.tight_layout()
    plt.savefig(os.path.join(desktop,'Resolution_times_distribution_by_L2Subtypes.png'))

    return

def logistics_l3(df):
    df['Closed at'] = pd.to_datetime(df['Closed at'], dayfirst = True)
    df = df[(df['Closed at'] >= w1_start) & (df['Closed at'] <= w2_end) & (df['Active'] == False)]
    df['week'] = ['W1' if (x>=w1_start) & (x<=w1_end) else 'W2' for x in df['Closed at']]
    pickup = df[df['L2 subtype'] == 'pickup']
    pickup = 100*pickup.groupby(['week','L3 subtype'])['ID'].count().divide(pickup.groupby('week')['ID'].count(), axis = 0)
    sns.set(rc = {'figure.figsize': (22,13)})
    pickup_L3 = pickup.unstack(level = 0).plot.bar()
    pickup_L3.tick_params(axis = 'x', labelsize = 18)
    pickup_L3.set(xlabel = 'L3_subtypes_pickup_issues', ylabel = '% of all Pickup Issues')
    plt.suptitle('Pickup Issues-L3 reason analysis', fontsize = 28)
    pickup_L3.text(.2,.9,'W1 ='+w1_start.strftime('%d%b%y')+'-'+w1_end.strftime('%d%b%y')+', W2 ='+w2_start.strftime('%d%b%y')+'-'+w2_end.strftime('%d%b%y'),transform = pickup_L3.transAxes, ha='center',va='center',fontsize = 18)
    plt.tight_layout()
    plt.savefig(os.path.join(desktop,'pickup_issues_L3_subtypes.png'))

    delivery = df[df['L2 subtype'] == 'delivery']
    delivery = 100*delivery.groupby(['week','L3 subtype'])['ID'].count().divide(delivery.groupby('week')['ID'].count(), axis = 0)
    sns.set(rc = {'figure.figsize': (25,13)})
    delivery_L3 = delivery.unstack(level = 0).plot.bar()
    delivery_L3.tick_params(axis = 'x', labelsize = 18)
    delivery_L3.set(xlabel = 'L3_subtypes_delivery_issues', ylabel = '% of all Pickup Issues')
    plt.suptitle('Delivery Issues-L3 reason analysis', fontsize = 28)
    delivery_L3.text(.2,.9,'W1 ='+w1_start.strftime('%d%b%y')+'-'+w1_end.strftime('%d%b%y')+', W2 ='+w2_start.strftime('%d%b%y')+'-'+w2_end.strftime('%d%b%y'),transform = delivery_L3.transAxes, ha='center',va='center',fontsize = 18)
    plt.tight_layout()
    plt.savefig(os.path.join(desktop,'delivery_issues_L3_subtypes.png'))


    return

def quality_l3(df):
    df['Closed at'] = pd.to_datetime(df['Closed at'], dayfirst = True)
    df = df[(df['Closed at'] >= w1_start) & (df['Closed at'] <= w2_end) & (df['Active'] == False)]
    df['week'] = ['W1' if (x>=w1_start) & (x<=w1_end) else 'W2' for x in df['Closed at']]
    quality = df[df['L2 subtype'] == 'Quality']
    quality = 100*quality.groupby(['week','L3 subtype'])['ID'].count().divide(quality.groupby('week')['ID'].count(), axis = 0)
    sns.set(rc = {'figure.figsize': (25,13)})
    quality_L3 = quality.unstack(level = 0).plot.bar()
    quality_L3.tick_params(axis = 'x', labelsize = 14)
    plt.xlabel('L3_subtypes_quality_issues', fontsize = 18)
    plt.ylabel('% of all Quality Issues', fontsize = 18)
    plt.suptitle('Quality Issues-L3 reason analysis', fontsize = 28)
    quality_L3.text(.2,.9,'W1 ='+w1_start.strftime('%d%b%y')+'-'+w1_end.strftime('%d%b%y')+', W2 ='+w2_start.strftime('%d%b%y')+'-'+w2_end.strftime('%d%b%y'),transform = quality_L3.transAxes, ha='center',va='center',fontsize = 18)
    plt.tight_layout()
    plt.savefig(os.path.join(desktop,'Quality_issues_L3_subtypes.png'))

    return



w1_start = pd.to_datetime('9-jul-2016')
w1_end = pd.to_datetime('15-jul-2016')
w2_start = pd.to_datetime('16-jul-2016')
w2_end = pd.to_datetime('22-jul-2016')
desktop = 'c:/users/amit/desktop'


def main():
    filename = sys.argv[1]
    df = pd.read_csv(filename)
    df['Ownership during close with'].replace({'Mumbai Delivery ( After RFD )':'mumbai', 'Mumbai Logistics (pickup)':'mumbai', 'Bangalore logistics (pickup)':'bangalore','Bangalore Delivery ( After RFD )': 'bangalore', 'CC_customers':'CC'}, inplace = True)
    df['L2 subtype'].replace({'Clothes Lost/Exchanged':'lost/ex'}, inplace = True)

    FRT(df[df['City'] == 'Mumbai'])
    resolution_time(df[df['City'] == 'Mumbai'])
    logistics_l3(df[df['City'] == 'Mumbai'])
    quality_l3(df[df['City'] == 'Mumbai'])

if __name__=='__main__':
    main()
