import pandas as pd
import sys
import pdb
import os
import matplotlib.pyplot as plt


def f(bookings, pickup, city):
    #requested_bookings
    requested = bookings['Booking ID'].nunique()
    pickup_funnel = pd.Series(requested, index = ['requested'])
    #non_actionable and its reasons

    non_actionable_bookings = bookings[(bookings['Status'] == 'cancelled') & (~(bookings['Cancel reason'].isin(['reschedule_stock_out','stock_out']))) & (bookings['Cancelled pickup visits'] == 0)]
    non_actionable_breakup1 = non_actionable_bookings.groupby(['Cancel reason'])['Booking ID'].count()
    non_actionable_breakup1.index = non_actionable_breakup1.index.str.replace('^reschedule.*','reschedule')
    non_actionable_breakup1 = non_actionable_breakup1.groupby(level = 0).sum()
    non_actionable_breakup1['others'] = non_actionable_breakup1.sum()-non_actionable_breakup1['customer_cancellation']-non_actionable_breakup1['reschedule']-non_actionable_breakup1['out_of_geographical_area']
    non_actionable_breakup1 = non_actionable_breakup1[non_actionable_breakup1.index.isin(['reschedule','out_of_geographical_area','others'])]

    pickup_funnel = pickup_funnel.append(non_actionable_breakup1)
    non_actionable_breakup2 = non_actionable_bookings.groupby(['Booking cancel reason'])['Booking ID'].count()
    pickup_funnel = pickup_funnel.append(non_actionable_breakup2)
    #pre_visit SO/RSO
    pre_visit_stockout = bookings[(bookings['Cancel reason'].notnull()) & (bookings['Cancel reason'].str.contains('stock_out')) & (bookings['Cancelled pickup visits'] == 0)]['Booking ID'].count()
    pickup_funnel['pre_visit_SO/RSO'] = pre_visit_stockout

    post_visit_stockout = pickup[(pickup['booking_cancel_reason'].notnull()) & (pickup['booking_cancel_reason'].str.contains('stock_out')) & (pickup['Cancelled pickup visits'] <> 0)]['Booking ID'].nunique()
    pickup_funnel['post_visit_SO/RSO'] = post_visit_stockout

    ppvc2 = pickup[(pickup['Status'] == 'cancelled') & (~(pickup['booking_cancel_reason'].str.contains('stock_out').fillna(False))) & (pickup['Cancelled pickup visits'] >= 2)]['Booking ID'].nunique()
    pickup_funnel['ppvc2'] = ppvc2
    ppvc1 = pickup[(pickup['Status'] == 'cancelled') & (~(pickup['booking_cancel_reason'].str.contains('stock_out').fillna(False))) & (pickup['Cancelled pickup visits'] == 1)]['Booking ID'].nunique()
    pickup_funnel['ppvc1'] = ppvc1
    ppvc1 = pickup[(pickup['Status'] == 'cancelled') & (~(pickup['booking_cancel_reason'].str.contains('stock_out').fillna(False))) & (pickup['Cancelled pickup visits'] == 1)]
    ppvc1_breakup = ppvc1.groupby(['visit_cancel_reason'])['Booking ID'].nunique()
    not_home = ppvc1[(ppvc1['visit_status'] == 'cancelled') & (ppvc1['visit_cancel_reason'].isin(['not_available_at_the_address ','Not available at the address ']))].groupby('updation_slot')['Booking ID'].nunique()
    pickup_funnel = pickup_funnel.append([ppvc1_breakup,not_home])

    #successful_visits_analysis
    success_visits = pickup[pickup['visit_status'] == 'done']
    tmp2 = success_visits['updation_time'].dt.hour + success_visits['updation_time'].dt.minute/60.0
    before_slot_pickup = success_visits[(tmp2 <= success_visits['requested_time'])]['Booking ID'].nunique()
    pickup_funnel['before_slot_pikcup'] = before_slot_pickup
    within_slot_pickup = success_visits[(tmp2 > success_visits['requested_time']) & (tmp2 <= success_visits['requested_time'] + 2)]['Booking ID'].nunique()
    pickup_funnel['within_slot_pickup'] = within_slot_pickup
    outside_slot = success_visits[(tmp2 > success_visits['requested_time'] + 2)]
    outside_slot_pickup = outside_slot.groupby('updation_slot')['Booking ID'].nunique()
    outside_slot_creation = outside_slot.groupby('creation_slot')['Booking ID'].nunique()
    pickup_funnel = pickup_funnel.append(outside_slot_pickup)
    pickup_funnel = pickup_funnel.append(outside_slot_creation)

    (pickup_funnel/float(requested)).to_csv('pickup_funnel_'+city+'.csv')

    return


def updation_creation_slot(df):
    if df['visit_status'] == 'done':
        tmp = df['updation_time'].hour + df['updation_time'].minute/60.0 
        if tmp <= df['requested_time']:
            df['updation_slot'] = 'picked_before_slot'
        elif tmp <= df['requested_time'] + 1:
            df['updation_slot'] = 't-t+1'
        elif tmp <= df['requested_time'] + 2:
            df['updation_slot'] = 't+1-t+2'
        elif tmp <= df['requested_time'] + 3:
            df['updation_slot'] = 't+2-t+3'
        else:
            df['updation_slot'] = '>t+3'

    elif df['visit_status'] == 'cancelled':
        tmp = df['cancellation_time'].hour + df['cancellation_time'].minute/60.0 
        if tmp <= df['requested_time']:
            df['updation_slot'] = 'cancelled_before_slot'
        elif tmp <= df['requested_time'] + 1:
            df['updation_slot'] = 't-t+1'
        elif tmp <= df['requested_time'] + 2:
            df['updation_slot'] = 't+1-t+2'
        else:
            df['updation_slot'] = '>t+2'

    tmp1 = df['creation_time'].hour + df['creation_time'].minute/60.0
    if tmp1 <= df['requested_time']:
        df['creation_slot'] = '<t'
    elif tmp1 <= df['requested_time'] + .5:
        df['creation_slot'] = 't to t+.5'
    elif tmp1 <= df['requested_time'] + 1:
        df['creation_slot'] = 't+.5 to t+1'
    else: df['creation_slot'] = '>t+1'

    return df



def main():
    start_date = '9-jul-2016'
    end_date = '15-jul-2016'
    bookings_file = sys.argv[1]
    pickup_file = sys.argv[2]
    bookings = pd.read_csv(bookings_file, skiprows = range(1,100000))
    pickup = pd.read_csv(pickup_file)
    pickup = pd.merge(pickup, bookings[['Booking ID','Status','Cancel reason','Booking cancel reason','Cancelled pickup visits']], on = 'Booking ID', how = 'inner')

    pickup.rename(columns = {'Requested Time':'requested_time','Requested date':'requested_date','Scheduled time':'scheduled_time','Updation time':'updation_time','Visit Creation time':'creation_time','Cancellation time':'cancellation_time','Visit cancellation reason':'visit_cancel_reason','Visit status':'visit_status','Cancel reason':'booking_cancel_reason'}, inplace = True)

    bookings['requested_date'] = pd.to_datetime(bookings['requested_date'])

    pickup['requested_date'] = pd.to_datetime(pickup['requested_date'])
    pickup['cancellation_time'] = pd.to_datetime(pickup['cancellation_time'], errors = 'coerce')
    pickup['creation_time'] = pd.to_datetime(pickup['creation_time'], errors = 'coerce')
    pickup['updation_time'] = pd.to_datetime(pickup['updation_time'], errors = 'coerce')
    pickup['scheduled_time'] = pd.to_datetime(pickup['scheduled_time'], errors = 'coerce')
    pickup['requested_time'] = pd.to_numeric(pickup['requested_time'].str.split('-').str[0])

    bookings = bookings[(bookings['requested_date'] >= start_date) & (bookings['requested_date'] <= end_date)]
    pickup = pickup[(pickup['requested_date'] >= start_date) & (pickup['requested_date'] <= end_date)]

    pickup = pickup.apply(updation_creation_slot, axis = 1)
    f(bookings[bookings['City'] == 'Mumbai'], pickup[pickup['City'] == 'Mumbai'], 'Mumbai')
    #f(bookings[bookings['City'] == 'Bangalore'], pickup[pickup['City'] == 'Bangalore'], 'Bangalore')



if __name__=='__main__':
    main()
