import sys
import os
import pandas as pd

def merge_df(df1,df2):
	return df1.combine_first(df2)

def verify_nobooking_data(nobookings, bookings):
	return nobookings[~(nobookings['Number'].isin(bookings.loc[bookings['Status'] <> 'cancelled', 'Phone']))]

def marketing_master_booking_data(filename):
	#i only read the file and not the dataframe because pandas thinks that i am working on a copy here and raises warning...so just to be on safe side, i read the data inside the function
	column_to_use = ['Customer name','Email','Phone','Locality','Status','City','Feedback','requested_date','Customer DMC','Rating']
	df = pd.read_csv(filename, usecols = column_to_use)
	df = df[df['Status'] <> 'cancelled']
	#converting the requested_date to datetime format...even the function in comments works great
	#df.loc[:,'requested_date'] = df.loc[:,'requested_date'].apply(lambda x: pd.to_datetime(x))
	df['requested_date'] = pd.to_datetime(df['requested_date'], errors = 'coerce')
	#need to sort so that the latest booking with latest customr DMC comes to the top of the group and i apply 'first' to extract it
	df.sort_values(by='requested_date',ascending = False, inplace = True)
			
	df.set_index('Phone', inplace = True)
	grouped = df.groupby(level = 0)
	df['no booking for 45 days'] =  (pd.to_datetime('today').date() - grouped['requested_date'].max()).dt.days > 45
	df['no booking for 30 days'] =  (pd.to_datetime('today').date() - grouped['requested_date'].max()).dt.days > 30 
	df['no booking for 60 days'] =  (pd.to_datetime('today').date() - grouped['requested_date'].max()).dt.days > 60 
	df['last booking date'] = grouped['requested_date'].max()
	df['successful bookings'] = grouped['requested_date'].count()
	agg_f = ({\
			'Customer name':'first',\
			'Email':'first',\
			'Locality':'first',\
			'City':'first',\
			'Feedback':'mean',\
			'Rating':'first',\
			'successful bookings':'first',\
			'last booking date':'first',\
			'no booking for 30 days':'first',\
			'no booking for 45 days':'first',\
			'no booking for 60 days':'first',\
			'Customer DMC':'first'})

	grouped.agg(agg_f).to_csv(os.path.join(os.path.dirname(filename),'output\marketing_master_booking_data123.csv'))

	return 

def ops_delivery_data(filename,month):
	columns_to_use = ['Booking ID','Locality','Apartment','Building','Street','Landmark','Status','requested_date','Pickup by','Delivery by','Delivery scheduled time','City']
        df = pd.read_csv(filename, usecols = columns_to_use)
	df = df[df['Status'] <> 'cancelled']
	df['requested_date'] = pd.to_datetime(df['requested_date'], errors ='coerce')
	df['Delivery scheduled time'] = pd.to_datetime(df['Delivery scheduled time'], errors = 'coerce')
	DB = ['VLokal Bangalore','Roadrunnr Bangalore','Roadrunnr mumbai','Shadofax Mumbai','Parsel Mumbai','Shadowfax Gurgaon','shadowfax Banglore']
	PB = ['Fayaz ','Santhosh ']

	delivery_df = df.copy(deep = True)
	delivery_df = delivery_df[delivery_df['Delivery scheduled time'].notnull()]
	delivery_df = delivery_df[delivery_df['Delivery scheduled time'].apply(lambda x: x.strftime('%Y-%m')) == str(month)]
	df = df[df['requested_date'].apply(lambda x: x.strftime('%Y-%m')) == str(month)]
	writer = pd.ExcelWriter(os.path.join(os.path.dirname(filename),'output\ops_delivery_data.xlsx'))

	write_multiple_dfs(delivery_df,DB,writer,'Delivery by')
	write_multiple_dfs(df,PB,writer,'Pickup by')
	writer.save()
	
	return


def write_multiple_dfs(df,sheet_list,writer,key):
	for s in sheet_list:
		df[df[key] == s].to_excel(writer, sheet_name = s)

	return

def main():
	if len(sys.argv) < 3:
		print 'invalid usage'
		print 'usage: python filename.py {--merge_nobooking_datadumps | --merge_booking_datadumps | --verify_nobooking_data | --marketing_master_booking_data | --ops_delivery_data} files'
		print 'the files should be in chronological order with the most recent file first'
		print 'for option = ops_delivery_data, the last argument should be the month for which data is required'
		sys.exit(1)
	
	option = sys.argv[1]
	filename = sys.argv[2:]
	if option == '--merge_nobooking_datadumps':
		merged_data_dump = merge_df(pd.read_csv(filename[0], index_col = 'Number'),pd.read_csv(filename[1], index_col = 'Number'))
		merged_data_dump.to_csv(os.path.join(os.path.dirname(filename[0]),'output\merged_data_dump.csv'), index = True)
	elif option == '--merge_booking_datadumps':
		merged_data_dump = merge_df(pd.read_csv(filename[0], index_col = 'Booking ID'),pd.read_csv(filename[1], index_col = 'Booking ID'))
		merged_data_dump.to_csv(os.path.join(os.path.dirname(filename[0]),'output\merged_data_dump.csv'), index = True)
	elif option == '--verify_nobooking_data':
		verified_nobookings_data = verify_nobooking_data(pd.read_csv(filename[0]), pd.read_csv(filename[1]))
		verified_nobookings_data.to_csv(os.path.join(os.path.dirname(filename[0]), 'output\wverified_data_dump.csv'), index = False)
	elif option == '--marketing_master_booking_data':
		marketing_master_booking_data(filename[0])
	elif option == '--ops_delivery_data':
		month = filename[-1]
		filename.pop()
		ops_delivery_data(filename[0],month)
	else:
		print 'invalid option'
		print 'usage: python filename.py {--merge_nobooking_datadumps | --merge_booking_datadumps | --verify_nobooking_data | --marketing_master_booking_data | --ops_delivery_data} files'
		print 'the files should be in chronological order with the most recent file first'
		print 'for option = ops_delivery_data, the last argument should be the month for which data is required'
		sys.exit(1)
	

if __name__ == '__main__':
	main()
