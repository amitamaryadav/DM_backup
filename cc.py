import pandas as pd
import sys
import ipdb
import os
import matplotlib.pyplot as plt
import seaborn as sns


def missed_analysis(df):
    flag = 0
    df = df[['phone','Direction','Status','StartTime','BillableDuration']]

    for row in df.itertuples():
        if (row[3] =='missed-call') & (flag == 0):
            t1 = row[4]
            flag = 1
        elif (row[2] == 'inbound') & (row[3] == 'completed') & (flag == 1):
            flag = 0
            df.loc[row[0],'callback_status'] = 'inb'
            t2 = (row[4] - t1).seconds/60.0
            df.loc[row[0],'callback_time(min)'] = t2
        elif (row[2] == 'outbound') & (flag == 1):
            flag = 0
            if row[3] == 'completed':
                df.loc[row[0],'callback_status'] = 'out_success'
            else:
                df.loc[row[0],'callback_status'] = 'out_fail'
            t2 = (row[4] - t1).seconds/60.0
            df.loc[row[0],'callback_time(min)'] = t2

    if flag == 1:
        df.loc[df.loc[df['Status'] == 'missed-call', 'StartTime'].idxmax(), 'callback_status'] = 'no_callback'
    return df



def customer_phone(df):
    if df['Direction'] == 'inbound':
        df['phone'] = df['From']
    else: df['phone'] = df['To']

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
    df['Ownership during close with'].replace({'CC_customers':'CC'}, inplace = True)

    df['First response time (minutes)'] = pd.to_numeric(df['First response time (minutes)'], errors = 'coerce')
    df['Time of creation'] = pd.to_datetime(df['Time of creation'], errors = 'coerce', dayfirst = True)
    #selecting last 4 weeks
    df = df[(df['Time of creation'] >= w1_start) & (df['Time of creation'] <= w4_end + pd.Timedelta('1 day'))]
    #apply week numbers
    df = df.apply(week, args = ('Time of creation',), axis = 1)
    #modifying FRT for issues created in non_business hours
    df = df.apply(modify_FRT, axis = 1)
    #modifying FRT for issues created in Business hours - 8AM to 10PM 
    tmp = df['Time of creation'] + pd.to_timedelta(df['First response time (minutes)'], unit = 'm')
    df['First response time (minutes)'] = df['First response time (minutes)'] - (600*((tmp.dt.date-df['Time of creation'].dt.date)).dt.days) 

    #filtering only customer issues handled by CC
    df1 = df[(df['FreshDesk/Internal'].notnull()) & ((df['Ownership during close with'].isin(['CC'])) | (df['Closed by'].isin(['barnana.goswami@doormint.in', 'joel.creado@doormint.in', 'khalid.kadri@doormint.in','krunaljoshib@gmail.com','monalisheth92@gmail.com', 'ompathak28@gmail.com', 'richiakre@gmail.com', 'rizwan.shaikh@doormint.in', 'sachin.yadav@doormint.in','madhushree.ramani@doormint.in'])))]

    grouped = df1.groupby(['week'])
    total_issues = grouped['First response time (minutes)'].count()
    kpi = pd.Series('', index = ['KPI'])
    issues_20 = df1[df1['First response time (minutes)'] <= 20].groupby('week')['First response time (minutes)'].count()/total_issues
    kpi['% issues replied within 20 min'] = ''
    kpi = kpi.append((100*issues_20).round(1))
    kpi['% issues replied within 60 min'] = ''
    issues_60 = df1[df1['First response time (minutes)'] <= 60].groupby('week')['First response time (minutes)'].count()/total_issues
    kpi = kpi.append((100*issues_60).round(1))
    sns.set(rc = {'figure.figsize': (22,12)})
    frt = df1.boxplot(column = 'First response time (minutes)', by = 'week', whis = [10,75], showfliers = False)
    frt.set(xticklabels = ["%s\n$N$=%d,\n$\mu$=%2.1f,\n$80P$=%2.1f\n$90P$=%2.1f"%(k, len(v), v['First response time (minutes)'].mean(), v['First response time (minutes)'].quantile(.8), v['First response time (minutes)'].quantile(.9)) for k,v in grouped])
    frt.set(title = '')
    plt.ylabel('First Response Time (in minutes)', fontsize = 24)
    plt.xlabel('Week', fontsize = 24)
    plt.suptitle('Distribution of Response Time of Toolbox ISSUES', fontsize = 28)
    frt.text(.9,.98,'W1 ='+w1_start.strftime('%d%b%y')+'-'+w1_end.strftime('%d%b%y')+', W2 ='+w2_start.strftime('%d%b%y')+'-'+w2_end.strftime('%d%b%y'), transform = frt.transAxes, ha='center', va='center', fontsize = 16, color = 'red')
    frt.text(.9,.95,'W3 ='+w3_start.strftime('%d%b%y')+'-'+w3_end.strftime('%d%b%y')+', W4 ='+w4_start.strftime('%d%b%y')+'-'+w4_end.strftime('%d%b%y'), transform = frt.transAxes, ha='center', va='center', fontsize = 16, color = 'red')
    frt.text(.01,1.0, kpi, transform = frt.transAxes, ha='left', va='top', fontsize = 16, color = 'black')
    frt.tick_params(axis = 'x', labelsize = 18)
    plt.tight_layout()
    plt.savefig(os.path.join(desktop,'CC_FRT_distribution.png'))

    return



w1_start = pd.to_datetime('9-jul-2016')
w1_end = pd.to_datetime('15-jul-2016')
w2_start = pd.to_datetime('16-jul-2016')
w2_end = pd.to_datetime('22-jul-2016')
w3_start = pd.to_datetime('23-jul-2016')
w3_end = pd.to_datetime('29-jul-2016')
w4_start = pd.to_datetime('30-jul-2016')
w4_end = pd.to_datetime('5-Aug-2016')

desktop = 'c:/users/amit/desktop'



def week(df, col):
    if (df[col] >=w1_start) & (df[col] <= w1_end + pd.Timedelta('1 day')):
        df['week'] = 'W1'
    elif (df[col]>=w2_start) & (df[col] <= w2_end + pd.Timedelta('1 day')):
        df['week'] = 'W2'
    elif (df[col] >=w3_start) & (df[col] <= w3_end + pd.Timedelta('1 day')):
        df['week'] = 'W3'
    else: df['week'] = 'W4'

    return df



def main():

    #reading specific columns from the call report from exotel
    filename = sys.argv[1]
    filename2 = sys.argv[2]
    issues = pd.read_csv(filename2) 
    frt = FRT(issues)
    columns_to_use = ['Direction','From','Status','StartTime','To','BillableDuration']
    df = pd.read_csv(filename, usecols = columns_to_use)
    df['Direction'].replace({'outbound-api':'outbound','outbound-dial':'outbound'}, inplace = True)
    df['Status'].replace({'failed':'unsuccessful','no-answer':'unsuccessful','busy':'unsuccessful'}, inplace = True)

    #identifying calls where CC was involved and selecting 4 week period
    cc_agent = [2230721203, 2230721204, 2230721205, 2230721207, 2230721211, 2230721212, 2230721217, 2230721219, 2230721221, 2230721224, 2230721228, 2230721226, 2230721220, 2230721232]
    df = df[(df['Direction'] == 'inbound') | (df['From'].isin(cc_agent))]
    df['StartTime'] = pd.to_datetime(df['StartTime'])
    df = df[(df['StartTime'] >= w1_start) & (df['StartTime'] <= w4_end + pd.Timedelta('1 day'))]

    #introducing a new column 'Phone' which has customers phone number irrespective of inb or outbound calls
    df = df.apply(customer_phone, axis = 1)
    df.drop(['To','From'],axis = 1,inplace = True)
    df['phone'] = pd.to_numeric(df['phone'])

    #applying new columns for whether missed call was called back and callback_time
    df.sort_values(['phone','StartTime'], ascending = [True,True], inplace = True)
    df = df.groupby('phone').apply(missed_analysis)
    #applying week number
    df = df.apply(week, args = ('StartTime',), axis = 1)

    #plotting distribution of callback times for missed calls
    #finding key parameters which need to be written on the main graph
    total_missed = df.groupby(['callback_status','week'])['Direction'].count()
    no_callback = total_missed['no_callback']/total_missed.groupby(level = 1).sum()
    callback_20 = df[df['callback_time(min)'] <= 20].groupby('week')['Direction'].count()/total_missed.groupby(level = 1).sum()
    callback_60 = df[df['callback_time(min)'] <= 60].groupby('week')['Direction'].count()/total_missed.groupby(level = 1).sum()
    kpi = pd.Series('',index = ['KPI'])
    kpi['Callback within 20 min'] = ''
    kpi = kpi.append((100*callback_20).round(1))
    kpi['Callback with 60 min'] = ''
    kpi = kpi.append((100*callback_60).round(1))
    kpi['not_calledback'] = ''
    kpi = kpi.append((100*no_callback).round(1))

    df_with_callback = df[(df['callback_status'] <> 'no_callback') & (df['callback_status'].notnull())]
    df_with_callback.replace({'inb':'A','out_fail':'B','out_success':'C'}, inplace = True)
    fig = plt.figure()
    sns.set(rc = {'figure.figsize': (22,12)})
    grouped = df_with_callback.groupby(['callback_status','week'])
    #total = df.groupby('week')['callback_status'].count()
    cb_time = df_with_callback.boxplot(column = 'callback_time(min)', by = ['callback_status','week'], whis = [10,75], showfliers = False)
    #http://stackoverflow.com/questions/29286217/is-there-a-good-way-to-display-sample-size-on-grouped-boxplots-using-python-matp?rq=1
    cb_time.set_xticklabels(["%s\n$N$=%d\n$\mu$=%6.2f\n$80P$=%2.1f\n$90P$=%2.1f"%(k, len(v), v['callback_time(min)'].mean(), v['callback_time(min)'].quantile(.8), v['callback_time(min)'].quantile(.9)) for k,v  in grouped])
    cb_time.set(title = '')
    plt.suptitle('Distribution of callback times for missed calls', fontsize = 28)
    plt.xlabel('Callback_Status', fontsize = 24)
    plt.ylabel('Callback-Time(in min)', fontsize = 24)
    cb_time.text(.03,.98,'W1 ='+w1_start.strftime('%d%b%y')+'-'+w1_end.strftime('%d%b%y')+', W2 ='+w2_start.strftime('%d%b%y')+'-'+w2_end.strftime('%d%b%y'), transform = cb_time.transAxes, ha='left', va='center', fontsize = 16, color = 'red')
    cb_time.text(.03,.95,'W3 ='+w3_start.strftime('%d%b%y')+'-'+w3_end.strftime('%d%b%y')+', W4 ='+w4_start.strftime('%d%b%y')+'-'+w4_end.strftime('%d%b%y'), transform = cb_time.transAxes, ha='left', va='center', fontsize = 16, color = 'red')
    cb_time.text(.03,.92, kpi, transform = cb_time.transAxes, ha='left', va='top', fontsize = 16, color = 'black')
    cb_time.legend(('A=Customer_called','B=Out_Fail','C=Out_Success'), loc = 'best', fontsize = 18)
    cb_time.tick_params(axis = 'x', labelsize = 18)
    plt.tight_layout()
    plt.savefig(os.path.join(desktop,'MissedCall-callbackTime'))

    #plotting AHT
    df = df[(df['Status'].isin(['unsuccessful','completed']))]
    df['Status'].replace({'completed':'X','unsuccessful':'Y'}, inplace = True)
    df['Direction'].replace({'inbound':'A','outbound':'B'}, inplace = True)
    df['BillableDuration'] = df['BillableDuration'].div(60)

    grouped = df.groupby(['Direction','Status','week'])
    #total = df.groupby('week')['Status'].count()
    handling_time = df.boxplot(column = 'BillableDuration', by = ['Direction','Status','week'], whis = [10,75], showfliers = False)
    handling_time.set_xticklabels(["%s\n$N$=%d\n$\mu$=%2.1f,\n$80P$=%2.1f\n$90P$=%2.1f"%(k, len(v), v['BillableDuration'].mean(), v['BillableDuration'].quantile(.8), v['BillableDuration'].quantile(.9)) for k,v  in grouped])
    handling_time.set(title = '')
    plt.suptitle('Distribution of Handling times of calls handled by CC', fontsize = 28)
    plt.xlabel('Call_Status', fontsize = 24)
    plt.ylabel('Handling Time (in min)', fontsize = 24)
    handling_time.tick_params(axis = 'x', labelsize = 18)
    handling_time.text(.03,.98,'W1 ='+w1_start.strftime('%d%b%y')+'-'+w1_end.strftime('%d%b%y')+', W2 ='+w2_start.strftime('%d%b%y')+'-'+w2_end.strftime('%d%b%y'), transform = handling_time.transAxes, ha='left', va='center', fontsize = 16, color = 'red')
    handling_time.text(.03,.95,'W3 ='+w3_start.strftime('%d%b%y')+'-'+w3_end.strftime('%d%b%y')+', W4 ='+w4_start.strftime('%d%b%y')+'-'+w4_end.strftime('%d%b%y'), transform = handling_time.transAxes, ha='left', va='center', fontsize = 16, color = 'red')
    handling_time.legend(('A=Inbound','B=Outbound','X=Completed_calls','Y=Unsuccessful_calls'), loc = 'best', fontsize = 18)
    plt.tight_layout()
    plt.savefig(os.path.join(desktop,'HandlingTime'))


if __name__=='__main__':
    main()
