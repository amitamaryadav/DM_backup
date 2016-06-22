import sys
import os
import pandas as pd


def sp_productivity(filename,month):
        columns_to_use = ['Booking ID','Status','requested_date','Pickup by','Delivery by','Delivery scheduled time','City']
        df = pd.read_csv(filename, usecols = columns_to_use)
	df = df[df['Status'].isin(['closed','service_complete','in_service'])]
	df['requested_date'] = pd.to_datetime(df['requested_date'], errors ='coerce')
	df['Delivery scheduled time'] = pd.to_datetime(df['Delivery scheduled time'], errors = 'coerce')
        
        df['Delivery by'] = df['Delivery by'].str.strip(' ')
        df['Delivery by'] = df['Delivery by'].str.lower()
        df['Pickup by'] = df['Pickup by'].str.strip(' ')
        df['Pickup by'] = df['Pickup by'].str.lower()
         
        #pickup data
        pickup_df = df.copy(deep = True)
	pickup_df = pickup_df[pickup_df['requested_date'].apply(lambda x: x.strftime('%Y-%m')) == month]
        pickup_df['Date'] = pickup_df['requested_date'].apply(lambda x: x.strftime('%d'))
        pickups = pickup_df.groupby(['Pickup by','Date'])['Booking ID'].count()
        pickups.index.rename(['SP','Date'], inplace = True)

        #delivery data
	delivery_df = df.copy(deep = True)
	delivery_df = delivery_df[delivery_df['Delivery scheduled time'].notnull()]
	delivery_df = delivery_df[delivery_df['Delivery scheduled time'].apply(lambda x: x.strftime('%Y-%m')) == month]
        delivery_df['delivery_date'] = delivery_df['Delivery scheduled time'].apply(lambda x: x.date())
        delivery_df['Date'] = delivery_df['delivery_date'].apply(lambda x: x.strftime('%d'))
        deliveries = delivery_df.groupby(['Delivery by','Date'])['Booking ID'].count()
        deliveries.index.rename(['SP','Date'], inplace = True)
        

        pickups = pickups.reset_index()
        deliveries = deliveries.reset_index()

        pickups.to_csv('pickup.csv')
        deliveries.to_csv('deliveries.csv')
        merged_df = pd.merge(pickups, deliveries, on = ['SP','Date'], how = 'outer')
        print merged_df.head(10)
        merged_df.to_csv('sp_productivity.csv')





def third_party_delivery_data(filename,month):
	columns_to_use = ['Booking ID','Locality','Apartment','Building','Street','Landmark','Status','requested_date','Pickup by','Delivery by','Delivery scheduled time','City']
        df = pd.read_csv(filename, usecols = columns_to_use)
	df = df[df['Status'] <> 'cancelled']
	df['requested_date'] = pd.to_datetime(df['requested_date'], errors ='coerce')
	df['Delivery scheduled time'] = pd.to_datetime(df['Delivery scheduled time'], errors = 'coerce')
        
        df['Delivery by'] = df['Delivery by'].str.strip(' ')
        df['Delivery by'] = df['Delivery by'].str.lower()
        df['Pickup by'] = df['Pickup by'].str.strip(' ')
        df['Pickup by'] = df['Pickup by'].str.lower()
         
	DB = ['vlokal bangalore','roadrunnr bangalore','roadrunnr mumbai','shadofax jumbai','parsel mumbai','shadowfax gurgaon','shadowfax banglore','fayaz','santhosh','dinesh g']
	PB = ['fayaz','santhosh','dinesh g']

	delivery_df = df.copy(deep = True)
	delivery_df = delivery_df[delivery_df['Delivery scheduled time'].notnull()]
	delivery_df = delivery_df[delivery_df['Delivery scheduled time'].apply(lambda x: x.strftime('%Y-%m')) == month]
        delivery_df['delivery_date'] = delivery_df['Delivery scheduled time'].apply(lambda x: x.date())


	third_party_delivery_data_to_excel(delivery_df,DB,writer,'Delivery by')
	third_party_delivery_data_to_excel(df,PB,writer,'Pickup by')
	writer.save()
	
	return


def third_party_delivery_data_to_excel(df,sheet_list,writer,key):
	for s in sheet_list:
		df[df[key] == s].to_excel(writer, sheet_name = key+" "+s)
	return

def main():
	if len(sys.argv) < 3:
		print 'invalid option \n'
		print 'usage: python filename.py {--third_party_delivery_data} files'
		print 'for option = third_party_delivery_data, the last argument should be the month for which data is required'
		sys.exit(1)
	
	option = sys.argv[1]
	filename = sys.argv[2]
        month = sys.argv[3]

	if option == '--third_party_delivery_data':
		third_party_delivery_data(filename,month)
        elif option == '--sp_productivity':
            sp_productivity(filename, month)
	else:
		print 'invalid option \n'
		print 'usage: python filename.py {--third_party_delivery_data} files'
		print 'for option = third_party_delivery_data, the last argument should be the month for which data is required'
		sys.exit(1)
	

if __name__ == '__main__':
	main()
