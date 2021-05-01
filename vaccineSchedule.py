import os
import json
import time
import requests
import schedule
import pandas as pd
from datetime import datetime

def get_state_codes():
	
	url = 'https://cdn-api.co-vin.in/api/v2/admin/location/states'
	headers = {'accept': 'application/json','Accept-Language': 'en_US'}
	resp = requests.get(url, headers=headers)
	resp_dict = resp.json()
	state_codes_dict = {}
	for state in resp_dict['states']:
		state_codes_dict[state['state_name']] = state['state_id']
	return state_codes_dict
 
def get_district_codes(state_id):
	
	url = 'https://cdn-api.co-vin.in/api/v2/admin/location/districts/'+ str(state_id)
	headers = {'accept': 'application/json','Accept-Language': 'en_US'}
	resp = requests.get(url, headers=headers)
	resp_dict = resp.json()
	district_codes_dict = {}
	for district in resp_dict['districts']:
		district_codes_dict[district['district_name']] = district['district_id']
	return district_codes_dict

def get_district_id_dict(district_input_list,district_codes_dict):
	
	districts_input_list = districts_input_str.split(',')
	district_id_dict = {}
	for dist in districts_input_list:
		district_id_dict[district_codes_dict[str(dist).strip()]] = str(dist).strip()
	return district_id_dict


def get_available_hospitals_by_district(distcode,minage,curr_date):

	url = 'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict'
	headers = {'accept': 'application/json','Accept-Language': 'en_US'}
	params = {'district_id':str(distcode),'date':str(curr_date)}
	resp = requests.get(url, params=params, headers=headers)
	resp_dict = resp.json()
	available_hospitals = []
	for center in resp_dict['centers']:
		for session in center['sessions']:
			if ((session['min_age_limit'] == int(minage)) and (session['available_capacity']> 0)):
				available_hospitals.append(center)
	return available_hospitals

def process_hospitals_list(available_hospitals, curr_dt, minage,new_hospital_df):
	
	dict_insert = {}
	for center in available_hospitals:
		for session in center['sessions']:
			if ((session['min_age_limit'] == int(minage)) and (session['available_capacity']> 0)):
				dict_insert['TIMESTAMP'] = str(curr_dt.strftime('%Y-%m-%d %H:%M:%S'))
				dict_insert['HOSPITAL_NAME'] = str(center['name'])
				dict_insert['DISTRICT_NAME'] = str(center['district_name'])
				dict_insert['PINCODE'] = str(center['pincode'])
				dict_insert['FEE_TYPE'] = str(center['fee_type'])
				dict_insert['AVAILABLE_DATE'] = str(session['date'])
				dict_insert['AVAILABLE_CAPACITY'] = str(session['available_capacity'])
			new_hospital_df = new_hospital_df.append(dict_insert,ignore_index=True)
	return new_hospital_df

def play_alarm():
	
	duration = 3  # seconds
	freq = 440  # Hz
	os.system('play -nq -t alsa synth {} sine {}'.format(duration, freq))

def search_all_districts(district_id_dict,minage):
	
	curr_dt = datetime.now()
	curr_date = curr_dt.strftime("%d-%m-%Y")
	print('Run Time: ' + str(curr_dt.strftime("%H:%M:%S")))
	for distid in list(district_id_dict.keys()):
		new_hospital_df = pd.DataFrame(columns=['TIMESTAMP','HOSPITAL_NAME','DISTRICT_NAME','PINCODE','FEE_TYPE','AVAILABLE_DATE','AVAILABLE_CAPACITY'])
		print('Searching for available hospitals in: ' + str(district_id_dict[distid]))
		available_hospitals = get_available_hospitals_by_district(distid,int(min_age),str(curr_date))
		new_hospital_df = process_hospitals_list(available_hospitals,curr_dt,int(min_age),new_hospital_df)
		if new_hospital_df.shape[0] > 0:
			new_hospital_df.to_csv('available_hospitals.csv',mode='a',header=False,index=False)
			print('************************************************')
			print('Hospitals Available')
			print(list(set(list(new_hospital_df['HOSPITAL_NAME']))))
			print('************************************************')
			play_alarm()
		else:
			print('> No Hospitals Available')
	print('----------------------------------------------------------------')

if __name__ == '__main__':

	fileslist = os.listdir('./')
	if not 'available_hospitals.csv' in fileslist:
		new_hospital_df = pd.DataFrame(columns=['TIMESTAMP','HOSPITAL_NAME','DISTRICT_NAME','PINCODE','FEE_TYPE','AVAILABLE_DATE','AVAILABLE_CAPACITY'])
		new_hospital_df.to_csv('available_hospitals.csv',index=False)
	
	min_age_check = 0
	while min_age_check == 0:
		try:
			min_age = int(input('Enter Minimum Age (18/45): '))
		except:
			print('Minimum age invalid. Please try again.')
		else:
			min_age_check = 1

	state_codes_dict = get_state_codes()
	state_name_check = 0
	while state_name_check == 0:
		try:
			state_name = str(input('Enter State Name: '))
			state_id = state_codes_dict[state_name]
		except:
			print('State Name Invalid. Please try again.')
		else:
			state_name_check = 1

	district_codes_dict = get_district_codes(state_id)
	print('Districts in State: ')
	print(str(list(district_codes_dict.keys())))

	district_name_check = 0
	while district_name_check == 0:
		try:
			districts_input_str = str(input('Enter District Names (separated by commas): '))
			district_id_dict = get_district_id_dict(districts_input_str,district_codes_dict)
		except:
			print('District Name(s) Invalid. Please try again.')
		else:
			district_name_check = 1

	print('----------------------------------------------------------------')
	schedule.every(10).seconds.do(search_all_districts,district_id_dict,min_age)
	while True:
		schedule.run_pending()
		time.sleep(5)
