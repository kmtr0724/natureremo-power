#!/usr/bin/python3
import time
import json
import requests
import datetime
from pytz import timezone,utc
from influxdb import InfluxDBClient


def getToken():
    f = open("/usr/local/bin/token")
    token = f.read()
    f.close()
    return token.strip()


def getAPIdata():
	try:
		r2 = requests.get("https://api.nature.global/1/appliances",
		    headers = {"accept":"application/json","Authorization":"Bearer " + getToken()}
		)
		r2.raise_for_status()
		return r2.json()
	except:
		return False

def getPowerData():
	json_data = getAPIdata()
	if json_data == False:
		return 1

	echonet_properties = json_data[0]['smart_meter']['echonetlite_properties']
	power_data_array = {}
	for data in echonet_properties:
	    tmp_array = {}
	    tmp_array['value'] = data['val']
	    tmp_array['date'] = data['updated_at']
	    power_data_array[data['epc']] = tmp_array

	coefficient = int(power_data_array[211]['value'])
	normal_direction_cumulative_electric_energy = int(power_data_array[224]['value'])
	
	current_energy = int(power_data_array[231]['value'])
	current_energy_date = datetime.datetime.strptime(power_data_array[231]['date'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)
	current_energy_date = current_energy_date.astimezone(timezone('Asia/Tokyo'))

	total_energy = normal_direction_cumulative_electric_energy * coefficient * 0.1
	total_energy_date = datetime.datetime.strptime(power_data_array[224]['date'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)
	total_energy_date = total_energy_date.astimezone(timezone('Asia/Tokyo'))

	client = InfluxDBClient('localhost', 8086, '', '', 'power')
	json_body = [
	    {
	        "measurement": "current_power",
	        "time": current_energy_date,
	        "fields": {
	            "w": current_energy
	        }
	    }
	]
	client.write_points(json_body)

	json_body2 = [
	    {
	        "measurement": "total_power",
	        "time": total_energy_date,
	        "fields": {
	            "kwh": total_energy
	        }
	    }
	]
	client.write_points(json_body2)

	#print("current=" + str(current_energy) + " d=" + str(current_energy_date) + "total=" + str(total_energy) + " d=" + str(total_energy_date))
while(1):
	getPowerData()
	time.sleep(25)


