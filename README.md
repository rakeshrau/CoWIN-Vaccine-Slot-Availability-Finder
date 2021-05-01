# CoWIN Vaccine Availability Finder
Python Script to leverage CoWIN's Public API functionality to find hospitals with vaccine availability in selected district from current date till one week.
The script executes every 10 seconds and sounds an alarm when a hospital in selected districts has vaccines available. The list of hospitals is saved to an putput file.
> CoWIN Public API Web Page: [Link](https://apisetu.gov.in/public/marketplace/api/cowin)

## Install Requirements
```sh
pip3 install -r requirements.txt
```
## Code Execution
```sh
python3 vaccineSchedule.py
```

## Inputs Required
| Input | Description |
| ------ | ------ |
| Minimum Age | Age for vaccine availability (18/45) |
| State Name | State for vaccine availability |
| District Name | District from list displayed post entering state name |
> Multiple district names can be specified separated by a comma (,)

## Execution

If there is a hospital in list of districts which has a vaccine available, then an alarm will sound. The list of hospitals, date of availablity and other details are saved to `available_hospitals.csv`

## Code Flow
CoWIN's Metadata API's are called to retrive list of states and corresponding state_id's
As per user's input, CoWIN's Metadata API is called to retrieve list of districts and corresponding district_id's for the state
User's input of districts is parsed
The following steps are repeated every 10 seconds:
- CoWIN's Appointment Availability API's are called to retrieve the list of hospitals in selected districts
- The retrieved data is cleaned, processed & filtered according to minimum age and vaccine availability.
In case there are hospitals with required filters present with vaccines, a beep sound is played for 5 seconds
- The list of filtered hospitals, along with other necessary information, is saved to `available_hospitals.csv`

## Output Column Description
| Column Name | Description |
| ------ | ------ |
| TIMESTAMP | Timestamp of entry generation |
| HOSPITAL_NAME | Name of hospital |
| DISTRICT_NAME | District associated with hospital |
| PINCODE | Pincode associated with hospital (for easier search while scheduling) |
| FEE_TYPE | Whether vaccine is free/paid |
| AVAILABLE_DATE | Date of availability of vaccine |
| AVAILABLE_CAPACITY | Doses of vaccine available |
> There might be multiple entries for a particular hospital due to vaccine availability on different dates

## Sample Execution
Sample Execution when no hospitals are found:  
![](https://i.ibb.co/59sSW6n/no-hospitals.png)
Sample Execution when hospitals are found:  
![](https://i.ibb.co/N689MBx/hospitals.png)
Sample CSV Output File:  
![](https://i.ibb.co/Wn0ntFf/excel.png)

## Future Work
- Adding search by PIN code functionality 
- Creating UI for form input and displaying CSV file
- Deploy to IBM Cloud for easy of access
- Add functionality to send text message to notify about vaccine availability
- For scaling, develop a notification service, where user will be able to enter phone number and districts on a web page and they receive a text message notification when vaccine is available. The script would be running on the server side/
