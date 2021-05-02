import os
import json
import requests
from datetime import datetime
import schedule
import time
import pandas as pd
from hashlib import sha256
import sys

def get_auth_token(mobileno, TOKEN_VALID):

	def generate_otp(mobileno):
		url = 'https://cdn-api.co-vin.in/api/v2/auth/generateMobileOTP'
		headers = {'accept': 'application/json','Content-Type': 'application/json'}
		data = {"mobile":str(mobileno),"secret": "U2FsdGVkX1/3I5UgN1RozGJtexc1kfsaCKPadSux9LY+cVUADlIDuKn0wCN+Y8iB4ceu6gFxNQ5cCfjm1BsmRQ=="}
		resp = requests.post(url, json=data, headers=headers)
		# print(resp)	
		if resp.status_code == 200:
			resp_dict = resp.json()
			txnId = resp_dict['txnId']
			return txnId
		else:
			print('Unable to retrieve OTP. Please try again.')

	def authenticate_otp(otp,txnId):
		url = 'https://cdn-api.co-vin.in/api/v2/auth/validateMobileOtp'
		headers = {'accept': 'application/json','Content-Type': 'application/json'}
		data = {"otp":sha256(str(otp).encode('utf-8')).hexdigest(), "txnId":txnId}
		resp = requests.post(url, json=data, headers=headers)
		if resp.status_code == 200:
			resp_dict = resp.json()
			return resp_dict['token']
		else:
			print('OTP incorrect. Unable to retrieve token.')
			return False

	def get_beneficiary_list(authtoken):
		url = 'https://cdn-api.co-vin.in/api/v2/appointment/beneficiaries'
		headers = {'accept': 'application/json','Accept-Language': 'en_US','Authorization': str('Bearer ' + str(authtoken))}
		resp = requests.get(url, headers=headers)
		resp_dict = resp.json()
		# print(resp_dict)
		if resp.status_code == 200:
			beneficiary_list = []
			for ben in resp_dict['beneficiaries']:
				beneficiary_list.append(ben["beneficiary_reference_id"])
			return beneficiary_list
		else:
			print('Token Expired')
			TOKEN_VALID = 0

	txnId = generate_otp(mobileno)
	if txnId:
		otp = str(input('Enter OTP: '))
		authtoken = authenticate_otp(otp,txnId)
		if authtoken:
			TOKEN_VALID = 1
			beneficiary_list = get_beneficiary_list(authtoken)
			print(beneficiary_list)
			return authtoken, beneficiary_list, TOKEN_VALID
		else:
			TOKEN_VALID = 0
			return False, False, TOKEN_VALID
	else:
		TOKEN_VALID = 0
		return False, False, TOKEN_VALID

def schedule_appointment(center_array,beneficiary_list,authtoken, minage):
	url = "https://cdn-api.co-vin.in/api/v2/appointment/schedule"
	headers = {'accept': 'application/json','Accept-Language': 'en_US','Authorization': str('Bearer ' + str(authtoken))}
	new_dict = {}
	center = center_array[0]
	for center in center_array:
		for session in center['sessions']:
			if ((session['min_age_limit'] == int(minage)) and (session['available_capacity'] >= len(beneficiary_list))):
				new_dict['beneficiaries'] = beneficiary_list
				new_dict['dose'] = 1
				new_dict['center_id'] = center['center_id']
				new_dict['session_id'] = session['session_id']
				for slot in session['slots']:
					new_dict['slot'] = slot
					print('Attempting to schedule')

					print('Scheduling Appointment info: ' + str(new_dict))

					resp = requests.post(url, headers=headers, json=new_dict)
					print(f'Booking Response Code: {resp.status_code}')
					print(f'Booking Response : {resp.text}')
					if resp.status_code == 200:
						print('Vaccine Scheduled Successfully')
						print(resp.json())
						with open('scheduling_details.txt','w') as f:
							f.write(str(resp.json()))
						play_alarm()
						sys.exit(1)
					else:
						print('Error with scheduling appointment.')

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


def get_available_hospitals_by_district(distcode,minage,curr_date, numvac):

	url = 'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict'
	headers = {'accept': 'application/json','Accept-Language': 'en_US'}
	params = {'district_id':str(distcode),'date':str(curr_date)}
	resp = requests.get(url, params=params, headers=headers)
	resp_dict = resp.json()
	with open('output1.txt', 'w') as f:
		f.write(str(resp_dict))
	available_hospitals = []
	for center in resp_dict['centers']:
		for session in center['sessions']:
			if ((session['min_age_limit'] == int(minage)) and (session['available_capacity'] >= numvac)):
				available_hospitals.append(center)
	return available_hospitals

def process_hospitals_list(available_hospitals, curr_dt, minage,new_hospital_df, numvac):
	dict_insert = {}
	center_array = []

	for center in available_hospitals:
		for session in center['sessions']:
			if ((session['min_age_limit'] == int(minage)) and (session['available_capacity'] >= numvac)):
				dict_insert['TIMESTAMP'] = str(curr_dt.strftime('%Y-%m-%d %H:%M:%S'))
				dict_insert['HOSPITAL_NAME'] = str(center['name'])
				dict_insert['DISTRICT_NAME'] = str(center['district_name'])
				dict_insert['PINCODE'] = str(center['pincode'])
				dict_insert['FEE_TYPE'] = str(center['fee_type'])
				dict_insert['AVAILABLE_DATE'] = str(session['date'])
				dict_insert['AVAILABLE_CAPACITY'] = str(session['available_capacity'])
				center_array.append(center)
			new_hospital_df = new_hospital_df.append(dict_insert,ignore_index=True)
	return new_hospital_df, center_array

def play_alarm():
	duration = 3  # seconds
	freq = 440  # Hz
	os.system('play -nq -t alsa synth {} sine {}'.format(duration, freq))

def search_all_districts(district_id_dict,minage, authtoken, beneficiary_list, mobileno, TOKEN_VALID):
	curr_dt = datetime.now()
	curr_date = curr_dt.strftime("%d-%m-%Y")
	print('Run Time: ' + str(curr_dt.strftime("%H:%M:%S")))
	for distid in list(district_id_dict.keys()):
		new_hospital_df = pd.DataFrame(columns=['TIMESTAMP','HOSPITAL_NAME','DISTRICT_NAME','PINCODE','FEE_TYPE','AVAILABLE_DATE','AVAILABLE_CAPACITY'])
		print('Searching for available hospitals in: ' + str(district_id_dict[distid]))
		available_hospitals = get_available_hospitals_by_district(distid,int(min_age),str(curr_date), len(beneficiary_list))
		new_hospital_df, center_array = process_hospitals_list(available_hospitals,curr_dt,int(min_age),new_hospital_df, len(beneficiary_list))
		if new_hospital_df.shape[0] > 0:
			new_hospital_df.to_csv('available_hospitals.csv',mode='a',header=False,index=False)
			print('************************************************')
			print('Hospitals Available')
			print(list(set(list(new_hospital_df['HOSPITAL_NAME']))))
			print('************************************************')
			play_alarm()
			print('Proceeding to schedule vaccine')
			while TOKEN_VALID != 1:
				play_alarm()
				authtoken, beneficiary_list, TOKEN_VALID = get_auth_token(mobileno, TOKEN_VALID)
			schedule_appointment(center_array, beneficiary_list, authtoken, minage)	
		else:
			print('> No Hospitals Available')

	print('----------------------------------------------------------------')
	return TOKEN_VALID


if __name__ == '__main__':

	fileslist = os.listdir('./')
	if not 'available_hospitals.csv' in fileslist:
		new_hospital_df = pd.DataFrame(columns=['TIMESTAMP','HOSPITAL_NAME','DISTRICT_NAME','PINCODE','FEE_TYPE','AVAILABLE_DATE','AVAILABLE_CAPACITY'])
		new_hospital_df.to_csv('available_hospitals.csv',index=False)


	TOKEN_VALID = 0
	mobileno_check = 0
	while mobileno_check == 0:
		try:
			mobileno = str(input('Enter Mobile Number: '))
		except:
			print('Mobile Number invalid. Please try again.')
		else:
			mobileno_check = 1

	print('Sending OTP to mobile number ' + str(mobileno))

	while TOKEN_VALID == 0:
		authtoken, beneficiary_list, TOKEN_VALID = get_auth_token(mobileno, TOKEN_VALID)

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
		except KeyError:
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
	while True:
		TOKEN_VALID = search_all_districts(district_id_dict, min_age, authtoken, beneficiary_list, mobileno, TOKEN_VALID)
		time.sleep(10)