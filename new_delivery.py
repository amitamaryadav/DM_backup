import pandas as pd
import numpy as np
import sys
import ipdb
import os
import matplotlib.pyplot as plt

def f(delivery):
    ofd = delivery[delivery['OFD_time'].notnull()]['Visit ID'].count()
    not_ofd = delivery['Visit ID'].count() - ofd
    delivery_funnel = pd.Series(ofd+not_ofd, index = ['total_visits'])
    delivery_funnel['ofd_visits'] = ofd
    delivery_funnel['not_ofd_visits'] = not_ofd
    success = delivery[delivery['visit_status'] == 'done']['Visit ID'].count()
    delivery_funnel['successful_deliveries'] = success
    ofd_unsuccessful = ofd-success
    delivery_funnel['ofd_unsuccessful'] = ofd_unsuccessful

    #ofd_unsuccessful reasons
    delivery['visit_cancel_reason'] = delivery['visit_cancel_reason'].str.replace('not.available.at.*.address.*','not_available_at_address', case = False)
    delivery['visit_cancel_reason'] = delivery['visit_cancel_reason'].str.replace('not.able.to.locate.the.address.*','not_able_to_locate_the_address', case = False)
    delivery['visit_cancel_reason'] = delivery['visit_cancel_reason'].str.replace('not.opening.the.door.*','not_opening_the_door', case = False)
    delivery['visit_cancel_reason'] = delivery['visit_cancel_reason'].str.replace('cash.not.available.*','cash_not_available', case = False)
    delivery['visit_cancel_reason'] = delivery['visit_cancel_reason'].str.replace('traffic.problem.*','traffic_problem', case = False)
    delivery['visit_cancel_reason'] = delivery['visit_cancel_reason'].str.replace('db.refused.*','DB_refused_to_go', case = False)
    undelivered_reasons = delivery[(delivery['OFD_time'].notnull()) & (delivery['visit_status'] == 'cancelled')].groupby('visit_cancel_reason')['Visit ID'].count().sort_values(ascending = False)
    #temp code
    not_OFD_reasons = delivery[(delivery['OFD_time'].isnull()) & (delivery['visit_status'] == 'cancelled')].groupby('visit_cancel_reason')['Visit ID'].count().sort_values(ascending = False)
    delivery_funnel = delivery_funnel.append(undelivered_reasons)
    delivery_funnel = delivery_funnel.append(not_OFD_reasons)
    undelivered_updation = delivery[(delivery['OFD_time'].notnull()) & (delivery['visit_status'] == 'cancelled')].groupby('updation_slot')['Visit ID'].count().reindex(['<T','T_T+0.5','T+0.5_T+1','T+1_T+1.5','T+1.5_T+2','T+2_T+3','T+3_T+4','>T+4'])
    delivery_funnel = delivery_funnel.append(undelivered_updation)

    single_ofd_bookings = delivery[(delivery['visit_status'] == 'done') & (delivery['ofd_attempts'] == 1)]
    delivery_funnel['single_ofd'] = single_ofd_bookings['Booking ID'].nunique()
    delivery_funnel['without_slot'] = single_ofd_bookings[single_ofd_bookings['requested_date'].isnull()]['Booking ID'].nunique()
    delivery_funnel = delivery_funnel.append(single_ofd_bookings[single_ofd_bookings['requested_date'].notnull()].groupby('updation_slot')['Booking ID'].nunique().reindex(['<T','T_T+0.5','T+0.5_T+1','T+1_T+1.5','T+1.5_T+2','T+2_T+3','T+3_T+4','>T+4']))

    multiple_ofd_bookings = delivery[(delivery['visit_status'] == 'done') & (delivery['ofd_attempts'] >1)]
    delivery_funnel['multiple_ofd'] = multiple_ofd_bookings['Booking ID'].nunique()
    delivery_funnel['without_slot_mulOFD'] = multiple_ofd_bookings[multiple_ofd_bookings['requested_date'].isnull()]['Booking ID'].nunique()
    delivery_funnel = delivery_funnel.append(multiple_ofd_bookings[multiple_ofd_bookings['requested_date'].notnull()].groupby('updation_slot')['Booking ID'].nunique().reindex(['<T','T_T+0.5','T+0.5_T+1','T+1_T+1.5','T+1.5_T+2','T+2_T+3','T+3_T+4','>T+4']))

    delivery_funnel['total_bookings'] = single_ofd_bookings['Booking ID'].nunique() + multiple_ofd_bookings['Booking ID'].nunique()

    return delivery_funnel


def slot(df, time_col, time_slot, output_col):
    if (df[time_col] - df[time_slot]) <= pd.Timedelta('0 hour'):
        df[output_col] = '<T'
    elif (df[time_col] - df[time_slot]) <= pd.Timedelta('0.5 hour'):
        df[output_col] = 'T_T+0.5'
    elif (df[time_col] - df[time_slot]) <= pd.Timedelta('1 hour'):
        df[output_col] = 'T+0.5_T+1'
    elif (df[time_col] - df[time_slot]) <= pd.Timedelta('1.5 hour'):
        df[output_col]= 'T+1_T+1.5'
    elif (df[time_col] - df[time_slot]) <= pd.Timedelta('2 hour'):
        df[output_col] = 'T+1.5_T+2'
    elif (df[time_col] - df[time_slot]) <= pd.Timedelta('3 hour'):
        df[output_col] = 'T+2_T+3'
    elif (df[time_col] - df[time_slot]) <= pd.Timedelta('4 hour'):
        df[output_col] = 'T+3_T+4'
    else:
        df[output_col]= '>T+4'

    return df



def identify_OFD_visits(df):
    if ~((~(df['visit_status'] == 'done').any()) & (df['OFD happened at'].isnull().all())):
        if df['OFD happened at'].isnull().all():
            df['OFD happened at'] = df['OFD happened at'].fillna(df['creation_time'].max().strftime('%Y-%m-%d %H:%M:%S'))

        df.sort_values(['Booking ID','Visit ID'], inplace = True)
        OFD_timestamps = df['OFD happened at'].str.split(',').iloc[0]

        #assigning OFD to success visit
        df.loc[df['visit_status'] == 'done', 'OFD_time'] = OFD_timestamps.pop()

        #reversing the list
        OFD_timestamps.reverse()
        for index, row in df.iterrows():
            if len(OFD_timestamps) == 0:
                continue
            if row['cancellation_time'] >= pd.to_datetime(OFD_timestamps[-1]):
                df.loc[index, 'OFD_time'] = OFD_timestamps.pop()


    return df



def add_week(df, date_col, start_date):
    if df[date_col] < start_date + pd.Timedelta('7 days'):
        df['week'] = start_date.strftime('%b-%d') + ' to ' + (start_date + pd.Timedelta('6 days')).strftime('%b-%d')
    elif df[date_col] < start_date + pd.Timedelta('14 days'):
        df['week'] = (start_date + pd.Timedelta('7 days')).strftime('%b-%d') + ' to ' + (start_date + pd.Timedelta('13 days')).strftime('%b-%d')
    elif df[date_col] < start_date + pd.Timedelta('21 days'):
        df['week'] = (start_date + pd.Timedelta('14 days')).strftime('%b-%d') + ' to ' + (start_date + pd.Timedelta('20 days')).strftime('%b-%d')
    else:
        df['week'] = (start_date + pd.Timedelta('21 days')).strftime('%b-%d') + ' to ' + (start_date + pd.Timedelta('27 days')).strftime('%b-%d')


    return df


def main():
    start_date = pd.to_datetime('8-Aug-2016')
    end_date = pd.to_datetime('04-Sep-2016')
    delivery_file = sys.argv[1]
    delivery = pd.read_csv(delivery_file)

    delivery.rename(columns = {'Delivery Requested Time':'requested_time','Delivery Requested date':'requested_date','Scheduled time':'scheduled_time','Updation time':'updation_time','Visit Creation time':'creation_time','Cancellation time':'cancellation_time','Visit cancellation reason':'visit_cancel_reason','Visit status':'visit_status'}, inplace = True)

    #selecting only data where delivery visit was created between the start_date and end_date & only keeping visits with status = 'done' or 'cancelled'
    ###http://stackoverflow.com/questions/29370057/select-dataframe-rows-between-two-dates
    delivery['creation_time'] = pd.to_datetime(delivery['creation_time'], errors = 'coerce')
    mask = (delivery['creation_time'] >=  start_date) & (delivery['creation_time'] <= end_date + pd.Timedelta('1 day'))
    delivery = delivery.loc[mask]
    delivery  = delivery[(delivery['visit_status'].isin(['done','cancelled'])) & (delivery['City'] == 'Mumbai')]

    #add a week column
    delivery = delivery.apply(add_week, args = ('creation_time',start_date,), axis = 1)

    #identifying OFD_visits and attaching respective OFD_timestamp to it
    delivery['cancellation_time'] = pd.to_datetime(delivery['cancellation_time'], errors = 'coerce')
    delivery = delivery.groupby('Booking ID').apply(identify_OFD_visits)

    #merging updation_time and cancellation_time
    delivery['updation_time'] = delivery.apply(lambda x: x['updation_time'] if x['visit_status'] == 'done' else x['cancellation_time'], axis = 1)
    #add a new column updation_slot - when was the delivery visit updated/cancelled w.r.t the time_slot given
    ##preparing requested_timestamp 
    delivery['requested_time'] = delivery['requested_time'].str.split('-').str[0].str.rstrip()
    delivery['requested_datetime'] = pd.to_datetime(delivery['requested_date'] + ' ' + delivery['requested_time'] + ':00:00', errors = 'coerce')
    delivery['updation_time'] = pd.to_datetime(delivery['updation_time'], errors = 'coerce')
    ##Applying final function to add the updation_slot column
    delivery = delivery.apply(slot, args = ('updation_time','requested_datetime','updation_slot',), axis = 1)
    ##Applying final function to add the OFD_slot column
    delivery['OFD_time'] = pd.to_datetime(delivery['OFD_time'], errors = 'coerce')
    delivery = delivery.apply(slot, args = ('OFD_time','requested_datetime','OFD_slot',), axis = 1)

    ##Applying final function to add the creation_time column
    delivery = delivery.apply(slot, args = ('creation_time','requested_datetime','creation_slot',), axis = 1)

    #delivery['requested_date'] = pd.to_datetime(delivery['requested_date'])
    #delivery['requested_time'] = pd.to_numeric(delivery['requested_time'], errors = 'coerce')
    delivery['ofd_attempts'] = delivery['OFD happened at'].str.split(',').str.len()

    delivery.set_index('Booking ID', inplace = True)
    delivery['ofd_attempts'] = delivery.groupby(level = 0)['ofd_attempts'].max()
    delivery.reset_index(inplace = True)

    #delivery[delivery['City'] == 'Mumbai'].groupby(['Locality','requested_time','visit_status','updation_slot','OFD_slot','creation_slot'])['Visit ID'].count().to_csv('t1.csv')

    weeks = delivery['week'].unique()
    for week in weeks:
        f(delivery[delivery['week'] == week]).to_csv('delivery_funnel_'+week+'.csv')


if __name__=='__main__':
    main()
