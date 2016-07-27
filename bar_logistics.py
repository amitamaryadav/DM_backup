import pandas as pd
import sys
import pdb
import os
import matplotlib.pyplot as plt

def f(bookings, city):
    pdb.set_trace()
    requested = bookings['Booking ID'].count()
    actionable = bookings[~((bookings['Cancel reason'].isin(['fake','out_of_geographical_area','duplicate'])) | (bookings['Cancel reason'].str.contains('customer_cancellation')))]['Booking ID'].count()
    stockout = bookings[(bookings['Cancel reason'].notnull()) & (bookings['Cancel reason'].str.contains('stock_out'))]['Booking ID'].count()

    picked_bookings = bookings[bookings['Status'] <> 'cancelled']
    picked = picked_bookings['Booking ID'].count()

    tmp1 = (picked_bookings['Pickup actual time'] - picked_bookings['requested_date']).dt.days
    tmp2 = picked_bookings['Pickup actual time'].dt.hour + picked_bookings['Pickup actual time'].dt.minute/60 
    within_slot_pickup = picked_bookings[(tmp1 == 0) & (tmp2 > picked_bookings['requested_time']) & (tmp2 < picked_bookings['requested_time'] + 2)]['Booking ID'].count()
    outside_slot_pickup = picked - within_slot_pickup
    cart_corrected = picked_bookings[(picked_bookings['Tags'].notnull()) & (picked_bookings['Tags'].str.contains('Cart_Corrected'))]['Booking ID'].count()
    TAT_breach = picked_bookings[picked_bookings['TAT'] >= 96]['Booking ID'].count()

    delivery_slots_bookings = picked_bookings[picked_bookings['Delivery requested at'].notnull()]
    delivery_slots = delivery_slots_bookings[delivery_slots_bookings['Delivery requested at'].notnull()]['Booking ID'].count()

    tmp3 = delivery_slots_bookings['Delivery actual time'].dt.hour + delivery_slots_bookings['Delivery actual time'].dt.minute/60 
    within_slot_delivery = delivery_slots_bookings[(tmp3 > delivery_slots_bookings['Delivery requested at'].dt.hour) & (tmp3 < delivery_slots_bookings['Delivery requested at'].dt.hour + 2)]['Booking ID'].count()
    outside_slot_delivery = delivery_slots - within_slot_delivery

    bookings['Delivery date'] = bookings['Delivery scheduled time'].dt.date
    successful_del = bookings[(bookings['Status'] <> 'cancelled') & (bookings['Delivery actual time'].notnull())]['Booking ID'].count()

    logistics = [actionable, picked, stockout, outside_slot_pickup, cart_corrected, TAT_breach, delivery_slots, outside_slot_delivery, successful_del]
    labels = ['Actionable','Picked', 'Stockout','Picked_outside_Slot','Wrong_DB_update','TAT_breach','with_Del_slots','Del_outside_Slot','Succ_del']
    per = [100*round(x/float(actionable),1) for x in logistics]
    df = pd.DataFrame({'abs':logistics,'per':per}, index = labels)

    fig = plt.figure()
    barplot = df['per'].plot.bar()
    barplot.set_xticklabels([(i[0],i[1],i[2]) for i in df.itertuples()])
    barplot.set_title('Logistics analysis as a fraction of actionable bookings')
    plt.tight_layout()
    desktop = 'c:/users/amit/desktop'
    plt.savefig(os.path.join(desktop,city))
    return 

def main():
    filename = sys.argv[1]
    bookings = pd.read_csv(filename, skiprows = range(1,100000))

    bookings['Pickup actual time'] = pd.to_datetime(bookings['Pickup actual time'])
    bookings['Delivery actual time'] = pd.to_datetime(bookings['Delivery actual time'])
    bookings['Delivery scheduled time'] = pd.to_datetime(bookings['Delivery scheduled time'])
    bookings['Delivery requested at'] = pd.to_datetime(bookings['Delivery requested at'])
    bookings['Delivery requested time'] = bookings['Delivery requested at'].dt.hour
    bookings['requested_date'] = pd.to_datetime(bookings['requested_date'])

    bookings = bookings[(bookings['requested_date'] >= '23-jun-2016') & (bookings['requested_date'] <= '29-jun-2016')]
    f(bookings[bookings['City'] == 'Mumbai'], 'Mumbai')
    f(bookings[bookings['City'] == 'Bangalore'], 'Bangalore')




if __name__=='__main__':
    main()
