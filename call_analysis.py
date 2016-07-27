import pandas as pd
import sys
import ipdb
import os
import matplotlib.pyplot as plt
import seaborn as sns


def missed_analysis(df):
    flag = 0
    df = df[['phone','Direction','Status','StartTime','BillableDuration','cc_involved']]

    for row in df.itertuples():
        if (row[3] =='missed-call') & (flag == 0):
            t1 = row[4]
            flag = 1
        elif (row[2] == 'inbound') & (row[3] == 'completed') & (flag == 1):
            flag = 0
            df.loc[row[0],'callback_status'] = 'inbound completed'
            t2 = (row[4] - t1).seconds/60.0
            df.loc[row[0],'callback_time(min)'] = t2
        elif (row[2] == 'outbound') & (flag == 1):
            flag = 0
            if row[3] == 'completed':
                df.loc[row[0],'callback_status'] = 'outbound-success'
            else:
                df.loc[row[0],'callback_status'] = 'outbound-failed'
            t2 = (row[4] - t1).seconds/60.0
            df.loc[row[0],'callback_time(min)'] = t2

    if flag == 1:
        df.loc[df.loc[df['Status'] == 'missed-call', 'StartTime'].idxmax(), 'callback_status'] = 'not_called_back'
    return df


def customer_phone(df):
    if df['Direction'] == 'inbound':
        df['phone'] = df['From']
    else: df['phone'] = df['To']

    return df

w1_start = pd.to_datetime('9-jul-2016')
w1_end = pd.to_datetime('15-jul-2016')
w2_start = pd.to_datetime('16-jul-2016')
w2_end = pd.to_datetime('22-jul-2016')
desktop = 'c:/users/amit/desktop'

def main():


    filename = sys.argv[1]
    columns_to_use = ['Direction','From','Status','StartTime','To','BillableDuration']
    df = pd.read_csv(filename, usecols = columns_to_use)
    df['Direction'].replace({'outbound-api':'outbound','outbound-dial':'outbound'}, inplace = True)
    df['Status'].replace({'failed':'unsuccessful','no-answer':'unsuccessful','busy':'unsuccessful'}, inplace = True)
    df['StartTime'] = pd.to_datetime(df['StartTime'])

    cc_agent = [2230721203, 2230721204, 2230721205, 2230721211, 2230721212, 2230721217, 2230721219, 2230721221, 2230721224, 2230721228]

    df = df[(df['StartTime'] >= pd.to_datetime(w1_start)) & (df['StartTime'] <= pd.to_datetime(w2_end) + pd.Timedelta('1 day'))]
    df['cc_involved'] =  (df['Direction'] == 'inbound') | (df['From'].isin(cc_agent))
    df = df[df['cc_involved']]
    df = df.apply(customer_phone, axis = 1)
    df.drop(['To','From'],axis = 1,inplace = True)
    df['phone'] = pd.to_numeric(df['phone'])
    df.sort_values(['phone','StartTime'], ascending = [True,True], inplace = True)
    df = df.groupby('phone').apply(missed_analysis)
    df['week'] = ['W1' if (x>=w1_start) & (x<=w1_end + pd.Timedelta('1 day')) else 'W2' for x in df['StartTime']]

    fig = plt.figure()
    grouped = df.groupby(['callback_status','week'])
    total = df.groupby('week')['callback_status'].count()

    sns.set(rc = {'figure.figsize': (22,12)})
    #http://stackoverflow.com/questions/29286217/is-there-a-good-way-to-display-sample-size-on-grouped-boxplots-using-python-matp?rq=1
    cb_time = df.boxplot(column = 'callback_time(min)', by = ['callback_status','week'], whis = [10,75], showfliers = False)
    cb_time.set_xticklabels(["%s\n$n$=%d,$P$=%4.2f\n$\mu$=%6.2f,$90Perc$=%2.1f"%(k, len(v), 100*len(v)/float(total['W1']) if k[1] == 'W1' else  100*len(v)/float(total['W2']), v['callback_time(min)'].mean(),v['callback_time(min)'].quantile(.9)) for k,v  in grouped])
    cb_time.set(title = '')
    plt.suptitle('Distribution of callback times for missed calls', fontsize = 28)
    plt.xlabel('Callback_Status', fontsize = 24)
    plt.ylabel('Callback-Time(in min)', fontsize = 24)
    cb_time.text(.2,.9,'W1 ='+w1_start.strftime('%d%b%y')+'-'+w1_end.strftime('%d%b%y')+', W2 ='+w2_start.strftime('%d%b%y')+'-'+w2_end.strftime('%d%b%y'), transform = cb_time.transAxes, ha='center', va='center', fontsize = 18)
    cb_time.tick_params(axis = 'x', labelsize = 14)
    plt.savefig(os.path.join(desktop,'MissedCall-callbackTime'))
    df = df[(df['cc_involved'] == 1) & (df['Status'].isin(['unsuccessful','completed']))]
    df['BillableDuration'] = df['BillableDuration'].div(60)

    grouped = df.groupby(['Direction','Status','week'])
    total = df.groupby('week')['Status'].count()
    handling_time = df.boxplot(column = 'BillableDuration', by = ['Direction','Status','week'], whis = [10,75], showfliers = False)
    handling_time.set_xticklabels(["%s\n$n$=%d,$P$=%4.2f\n$\mu$=%6.2f,$90Perc$=%2.1f"%(k, len(v), 100*len(v)/float(total['W1']) if k[2] == 'W1' else 100*len(v)/float(total['W2']), v['BillableDuration'].mean(), v['BillableDuration'].quantile(.9)) for k,v  in grouped])
    handling_time.set(title = '')
    plt.suptitle('Distribution of Handling times of calls handled by CC', fontsize = 28)
    plt.xlabel('Call_Status', fontsize = 24)
    plt.ylabel('Handling Time (in min)', fontsize = 24)
    handling_time.tick_params(axis = 'x', labelsize = 14)
    plt.tight_layout()
    handling_time.text(.2,.9,'W1 ='+w1_start.strftime('%d%b%y')+'-'+w1_end.strftime('%d%b%y')+', W2 ='+w2_start.strftime('%d%b%y')+'-'+w2_end.strftime('%d%b%y'), transform = handling_time.transAxes, ha='center', va='center', fontsize = 18)
    plt.savefig(os.path.join(desktop,'HandlingTime'))


if __name__=='__main__':
    main()
