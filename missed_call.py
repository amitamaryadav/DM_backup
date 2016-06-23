import pandas as pd
import sys
import pdb


total = 0
inb = 0
out = 0
l = []
missed_not_answered = []

def f(df):

    global total
    global inb
    global out
    flag = 0
    #pdb.set_trace()
    for row in df.itertuples():
        if row[2] =='missed-call':
            if flag == 0:
                t1 = row[3]
                missed_not_answered.append(row[3])
                total = total + 1
                flag = 1
        elif (row[1] == 'inbound') & (row[2] == 'completed') & (flag == 1):
            inb = inb + 1
            flag = 0
            missed_not_answered.pop()
        elif (row[1] == 'outbound-api') & (flag == 1):
            out = out + 1
            flag = 0
            t = row[3] - t1
            missed_not_answered.pop()
            l.append(t.seconds/60)
                
def f1(df):
    if df['Direction'] == 'outbound-api': 
        df['From'] = df['To']

    return df


    
def main():
    filename = sys.argv[1]
    columns_to_use = ['Direction','From','Status','StartTime','To']
    df = pd.read_csv(filename, usecols = columns_to_use)
    df['StartTime'] = pd.to_datetime(df['StartTime'])
    #pdb.set_trace()
    df = df.apply(f1, axis = 1)
    df.drop('To',axis = 1,inplace = True)
    #df = df[df['StartTime'].dt.hour < 19]
    df.sort_values(['From','StartTime'], ascending = [True,True], inplace = True)
    df.set_index('From', inplace = True)

    df.groupby(level = 0).apply(f)

    print total
    print inb
    print out

    s = pd.Series(l)
    pd.Series(missed_not_answered).to_csv('missed_not_answered.csv')
    

    s1 =  pd.qcut(s, 5)
    s1.to_csv('missed_calls2.csv')


if __name__=='__main__':
    main()
