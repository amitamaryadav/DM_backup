import pandas as pd
import sys
import ipdb
import os
import matplotlib.pyplot as plt


def f(bookings, pickup, city):
    #requested_bookings
    bookings = bookings[bookings['Status'].isin(['closed','service_complete','cancelled','in_service'])]
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

    ppvc1_breakup = ppvc1.groupby(['visit_cancel_reason'])['Booking ID'].nunique().sort_values(ascending = False)
    ppvc1_breakup_abridged = ppvc1_breakup[['not_opening_the_door','unfavourable_weather_conditions','not_able_to_locate_the_address','Others ','not_available_at_the_address']]
    ppvc1_breakup_abridged['everything_else'] = ppvc1_breakup.sum()-ppvc1_breakup_abridged.sum()
    not_home = ppvc1[(ppvc1['visit_status'] == 'cancelled') & (ppvc1['visit_cancel_reason'].isin(['not_available_at_the_address']))].groupby('updation_slot')['Booking ID'].nunique()
    not_home = not_home.reindex(['cancelled_before_slot','t-t+1','t+1-t+2','>t+2'])
    pickup_funnel = pickup_funnel.append(ppvc1_breakup_abridged)
    pickup_funnel = pickup_funnel.append(not_home)

    #successful_visits_analysis
    success_visits = pickup[pickup['visit_status'] == 'done']
    slot = pd.to_datetime(success_visits['requested_date'].dt.strftime('%Y-%m-%d') + ' ' + success_visits['requested_time'].astype('str') + ':00:00')
    tmp2 = success_visits['updation_time'].dt.hour + success_visits['updation_time'].dt.minute/60.0
    before_slot_pickup = success_visits[success_visits['updation_time'] < slot]['Booking ID'].nunique()
    pickup_funnel['before_slot_pikcup'] = before_slot_pickup
    within_slot_pickup = success_visits[(success_visits['updation_time'] >= slot) & (success_visits['updation_time'] <= slot + pd.Timedelta('2 hour'))]['Booking ID'].nunique()
    pickup_funnel['within_slot_pickup'] = within_slot_pickup
    outside_slot = success_visits[success_visits['updation_time'] > slot + pd.Timedelta('2 hour')]
    outside_slot_pickup = outside_slot.groupby('updation_slot')['Booking ID'].nunique().reindex(['t+2-t+3','>t+3'])
    outside_slot_creation = outside_slot.groupby('creation_slot')['Booking ID'].nunique().reindex(['<t','t to t+.5','t+.5 to t+1','>t+1'])
    pickup_funnel = pickup_funnel.append(outside_slot_pickup)
    pickup_funnel = pickup_funnel.append(outside_slot_creation)
    bookings_with_1_visit = outside_slot[(outside_slot['creation_slot'] == '>t+1') & (outside_slot['Cancelled pickup visits'] == 0)]['Booking ID'].count()
    pickup_funnel['bookings_with_creation_time>t+1_single_visit'] = bookings_with_1_visit

    pickup_funnel = pickup_funnel/float(requested)
    pickup_funnel['Requested_abs'] = requested
    pickup_funnel.to_csv('pickup_funnel_'+city+'.csv')

    return


def updation_creation_slot(df):
    if df['visit_status'] == 'done':
        slot = pd.to_datetime(df['requested_date'].strftime('%Y-%m-%d') + ' ' + str(df['requested_time']) + ':00:00')
        if df['updation_time'] <= slot:
            df['updation_slot'] = 'picked_before_slot'
        elif df['updation_time'] <= slot + pd.Timedelta('1 hour'):
            df['updation_slot'] = 't-t+1'
        elif df['updation_time'] <= slot + pd.Timedelta('2 hour'):
            df['updation_slot'] = 't+1-t+2'
        elif df['updation_time'] <= slot + pd.Timedelta('3 hour'):
            df['updation_slot'] = 't+2-t+3'
        else:
            df['updation_slot'] = '>t+3'

    elif df['visit_status'] == 'cancelled':
        slot = pd.to_datetime(df['requested_date'].strftime('%Y-%m-%d') + ' ' + str(df['requested_time']) + ':00:00')
        if df['cancellation_time'] <= slot:
            df['updation_slot'] = 'cancelled_before_slot'
        elif df['cancellation_time'] <= slot + pd.Timedelta('1 hour'):
            df['updation_slot'] = 't-t+1'
        elif df['cancellation_time'] <= slot + pd.Timedelta('2 hour'):
            df['updation_slot'] = 't+1-t+2'
        else:
            df['updation_slot'] = '>t+2'

    if df['creation_time'] <= slot:
        df['creation_slot'] = '<t'
    elif df['creation_time'] <= slot + pd.Timedelta('0.5 hour'):
        df['creation_slot'] = 't to t+.5'
    elif df['creation_time'] <= slot + pd.Timedelta('1 hour'):
        df['creation_slot'] = 't+.5 to t+1'
    else: df['creation_slot'] = '>t+1'

    return df



def main():
    start_date = '29-aug-2016'
    end_date = '04-sep-2016'
    bookings_file = sys.argv[1]
    pickup_file = sys.argv[2]
    bookings = pd.read_csv(bookings_file, skiprows = range(1,100000))
    pickup = pd.read_csv(pickup_file)
    pickup = pd.merge(pickup, bookings[['Booking ID','Status','Cancel reason','Booking cancel reason','Cancelled pickup visits']], on = 'Booking ID', how = 'inner')
    pickup.to_csv('tmp.csv')

    pickup.rename(columns = {'Requested Time':'requested_time','Requested date':'requested_date','Scheduled time':'scheduled_time','Updation time':'updation_time','Visit Creation time':'creation_time','Cancellation time':'cancellation_time','Visit cancellation reason':'visit_cancel_reason','Visit status':'visit_status','Cancel reason':'booking_cancel_reason'}, inplace = True)

    #formatting the visit cancel reason to combine the same reasons under one heading
    pickup['visit_cancel_reason'] = pickup['visit_cancel_reason'].str.replace('not.available.at.the.address.*','not_available_at_the_address', case = False)
    pickup['visit_cancel_reason'] = pickup['visit_cancel_reason'].str.replace('.*geographical.*','out_of_geographical_area', case = False)
    pickup['visit_cancel_reason'] = pickup['visit_cancel_reason'].str.replace('not.able.to.locate.*.address.*','not_able_to_locate_the_address', case = False)
    pickup['visit_cancel_reason'] = pickup['visit_cancel_reason'].str.replace('not.opening.the.door.*','not_opening_the_door', case = False)
    pickup['visit_cancel_reason'] = pickup['visit_cancel_reason'].str.replace('.*weather.*','unfavourable_weather_conditions', case = False)


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



if __name__=='__main__':
    main()
