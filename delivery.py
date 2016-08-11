import pandas as pd
import sys
import pdb
import os
import matplotlib.pyplot as plt


def f(delivery, city):
    ofd = delivery[delivery['visit_status'] == 'done']['ofd_attempts'].sum()
    not_ofd = delivery['Visit ID'].count() - ofd
    delivery_funnel = pd.Series(ofd+not_ofd, index = ['total_visits'])
    delivery_funnel['ofd_visits'] = ofd
    delivery_funnel['not_ofd_visits'] = not_ofd
    success = delivery[delivery['visit_status'] == 'done']['Booking ID'].nunique()
    delivery_funnel['successful_deliveries'] = success
    ofd_unsuccessful = ofd-success
    delivery_funnel['ofd_unsuccessful'] = ofd_unsuccessful

    single_ofd_bookings = delivery[(delivery['visit_status'] == 'done') & (delivery['ofd_attempts'] == 1)]
    delivery_funnel['single_ofd'] = single_ofd_bookings['Booking ID'].nunique()
    delivery_funnel['without_slot'] = single_ofd_bookings[single_ofd_bookings['requested_date'].isnull()]['Booking ID'].nunique()
    delivery_funnel = delivery_funnel.append(single_ofd_bookings[single_ofd_bookings['requested_date'].notnull()].groupby('updation_slot')['Booking ID'].nunique().reindex(['delivered_before_slot','t-t+1','t+1-t+2','t+2-t+3','t+3-t+4','>t+4']))

    multiple_ofd_bookings = delivery[(delivery['visit_status'] == 'done') & (delivery['ofd_attempts'] >1)]
    delivery_funnel['multiple_ofd'] = multiple_ofd_bookings['Booking ID'].nunique()
    delivery_funnel['without_slot_mulOFD'] = multiple_ofd_bookings[multiple_ofd_bookings['requested_date'].isnull()]['Booking ID'].nunique()
    delivery_funnel = delivery_funnel.append(multiple_ofd_bookings[multiple_ofd_bookings['requested_date'].notnull()].groupby('updation_slot')['Booking ID'].nunique().reindex(['delivered_before_slot','t-t+1','t+1-t+2','t+2-t+3','t+3-t+4','>t+4']))

    delivery_funnel['total_bookings'] = single_ofd_bookings['Booking ID'].nunique() + multiple_ofd_bookings['Booking ID'].nunique()

    return delivery_funnel


def updation_creation_slot(df):
    if (df['visit_status'] == 'done'):
        if (df['updation_time'] - df['requested_datetime']) <= pd.Timedelta('0 hours'):
            df['updation_slot'] = 'delivered_before_slot'
        elif (df['updation_time'] - df['requested_datetime']) <= pd.Timedelta('1 hours'):
            df['updation_slot'] = 't-t+1'
        elif (df['updation_time'] - df['requested_datetime']) <= pd.Timedelta('2 hours'):
            df['updation_slot'] = 't+1-t+2'
        elif (df['updation_time'] - df['requested_datetime']) <= pd.Timedelta('3 hours'):
            df['updation_slot'] = 't+2-t+3'
        elif (df['updation_time'] - df['requested_datetime']) <= pd.Timedelta('4 hours'):
            df['updation_slot'] = 't+3-t+4'
        else:
            df['updation_slot'] = '>t+4'
    
    elif df['visit_status'] == 'cancelled':
        if (df['cancellation_time'] - df['requested_datetime']) <= pd.Timedelta('0 hours'):
            df['updation_slot'] = 'cancelled_before_slot'
        elif (df['cancellation_time'] - df['requested_datetime']) <= pd.Timedelta('1 hours'):
            df['updation_slot'] = 't-t+1'
        elif (df['cancellation_time'] - df['requested_datetime']) <= pd.Timedelta('2 hours'):
            df['updation_slot'] = 't+1-t+2'
        else:
            df['updation_slot'] = '>t+2'
    '''
    tmp1 = df['creation_time'].hour + df['creation_time'].minute/60.0
    if tmp1 <= df['requested_time']:
        df['creation_slot'] = '<t'
    elif tmp1 <= df['requested_time'] + .5:
        df['creation_slot'] = 't to t+.5'
    elif tmp1 <= df['requested_time'] + 1:
        df['creation_slot'] = 't+.5 to t+1'
    else: df['creation_slot'] = '>t+1'
    '''

    return df



def main():
    date1 = '30-Jul-2016'
    date2 = '05-Aug-2016'
    delivery_file = sys.argv[1]
    delivery = pd.read_csv(delivery_file)

    delivery.rename(columns = {'Delivery Requested Time':'requested_time','Delivery Requested date':'requested_date','Scheduled time':'scheduled_time','Updation time':'updation_time','Visit Creation time':'creation_time','Cancellation time':'cancellation_time','Visit cancellation reason':'visit_cancel_reason','Visit status':'visit_status'}, inplace = True)


    delivery['cancellation_time'] = pd.to_datetime(delivery['cancellation_time'], errors = 'coerce')
    delivery['creation_time'] = pd.to_datetime(delivery['creation_time'], errors = 'coerce')
    delivery['updation_time'] = pd.to_datetime(delivery['updation_time'], errors = 'coerce')
    delivery['requested_time'] = delivery['requested_time'].str.split('-').str[0]
    delivery['requested_time_m'] = delivery['requested_time'].str.rstrip().astype(str) + ':00:00'
    delivery['requested_datetime'] = pd.to_datetime(delivery['requested_date'] + ' ' + delivery['requested_time_m'], errors = 'coerce')

    delivery['requested_date'] = pd.to_datetime(delivery['requested_date'])
    delivery['requested_time'] = pd.to_numeric(delivery['requested_time'], errors = 'coerce')
    delivery['ofd_attempts'] = delivery['OFD happened at'].str.split(',').str.len()

    delivery.set_index('Booking ID', inplace = True)
    delivery['ofd_attempts'] = delivery.groupby(level = 0)['ofd_attempts'].max()
    delivery.reset_index(inplace = True)
    delivery = delivery[(delivery['creation_time'] >= pd.to_datetime(date1)) & (delivery['creation_time'] <= pd.to_datetime(date2) + pd.Timedelta('1 day'))]

    delivery = delivery.apply(updation_creation_slot, axis = 1)
    f(delivery[delivery['City'] == 'Mumbai'], 'Mumbai').to_csv('delivery_mumbai.csv')


if __name__=='__main__':
    main()
