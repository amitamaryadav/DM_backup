import sys
import os
import pandas as pd


def main():
    filename = sys.argv[1]
    data = pd.read_csv(filename)
    data['Assigned on'] = pd.to_datetime(data['Assigned on'], errors = 'coerce')
    #http://stackoverflow.com/questions/37538080/pandas-inconsistent-date-time-format - question raised here...awaiting answers

    #data['Assigned on'] = data['Assigned on'].ffill()
    #data['month'] = data['Assigned on'].apply(lambda x: x.strftime('%Y-%m'))
    #print data.groupby('month').agg({'Amount':'sum'})
'''
    bins = [100,500,1000,2000,5000,50000]
    data['amount_ranges'] = pd.cut(data['Amount'], bins = bins)

    pivot = data.groupby(['month','amount_ranges']).agg({'Amount':['count','sum']})
    print pivot
'''

if __name__ == '__main__':
    main()
