# -*- coding: utf-8 -*-
"""
Created on Wed May  8 16:38:16 2021

@author: krishna kumar
"""

import datetime
import base64
import requests
import logging
import pandas as pd
import sys
import time
import os, shutil
import urllib
from urllib.parse import urlencode
from collections import OrderedDict
from plyer import notification


curr_dir = os.getcwd()

pincode_bool = True
pincode_list = []
district_bool = False
district_list = []
min_age = None
vaccine_type = None
output_cols = ['center_id', 'name', 'address', 'state_name', 'district_name','block_name', 'pincode',
                         'fee_type','date', 'available_capacity', 'fee', 'min_age_limit','vaccine', 'slots']

logging.basicConfig(filename=os.path.join(curr_dir, "test.log") ,
                        level=logging.DEBUG,
                        format="%(asctime)s:%(levelname)s:%(message)s")



class coWin():

    '''
    Class to handle all the utilities
    related to coWin portal
    '''

    def __init__(self):
        self._stateId_api = "https://cdn-api.co-vin.in/api/v2/admin/location/states"  # get state id of all states in India
        self._districtId_api = "https://cdn-api.co-vin.in/api/v2/admin/location/districts/" # get district within sates
        self._cowinbyDistrictid_api = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByDistrict?district_id" # get vaccination centers by district
        self._cowinbyPinCode_api = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByPin?pincode" # get vaccination centers by pincode
        #self._cowinbyPinCode_api = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode"
        #self._cowinbyDistrictid_api = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id"
        self._headers = self.set_headers()
        self._proxy = self.set_proxy()
        
        self._pincode_list = pincode_list
        self._district_list = district_list
        self._min_age = min_age
        self._vaccine_type = vaccine_type
        
        # get state ids; remains constant
        self.stateids_df = pd.DataFrame()
        self.district_df = pd.DataFrame()

        if district_bool==True:
            # get district ids for mentioned district name
            self.get_state_ids()
            for state in self.stateids_df.state_id.values:
                self.district_df = self.district_df.append(self.get_district_ids(state))
                time.sleep(0.2)
            
            self.district_df = self.district_df[self.district_df['district_name'].isin(district_list)]
        


    def build_url(self, searchKey, searchValue, date):
        """
        builds a url
        """

        if str.lower(searchKey) in str.lower(self._cowinbyDistrictid_api):
            return self._cowinbyDistrictid_api.split("?")[0]+"?" + urlencode([(searchKey, searchValue),
                                                            ('date', date)])
        elif str.lower(searchKey) in str.lower(self._cowinbyPinCode_api):
            return self._cowinbyPinCode_api.split("?")[0]+"?" + urlencode([(searchKey, searchValue),
                                                            ('date', date)])


    def http_response_error(self, status):
        '''Func to display response status recieved from server'''

        if status == 200:
            print ('Status: {} / SUCCESS :  Request was handled successfully'.format(status))
            logging.info('Status: {} / SUCCESS :  Request was handled successfully'.format(status))
        elif status == 500:
            print ('Status: {} / UNKNOWN_ERROR : Internal Server Error- Internal server error has occurred in our platform'.format(status))
            logging.info('Status: {} / UNKNOWN_ERROR : Internal Server Error- Internal server error has occurred in our platform'.format(status))
        elif status == 503:
            print ('Status: {} / SVC_UNAVAILABLE The server is currently unable to handle the request due to a temporary overloading or maintenance of the server'.format(status))
            logging.info('Status: {} / SVC_UNAVAILABLE The server is currently unable to handle the request due to a temporary overloading or maintenance of the server'.format(status))
        elif status == 405:
            print ('Status: {} / METHOD_NOT_ALLOWED Unsupported HTTP Method: A request was made for a resource using a request method not supported by that resource  (e.g. using POST instead of GET)'.format(status))
            logging.info('Status: {} / METHOD_NOT_ALLOWED Unsupported HTTP Method: A request was made for a resource using a request method not supported by that resource  (e.g. using POST instead of GET)'.format(status))
        elif status == 400:
            print ("Status: {} / BAD REQUEST PARAMETER_ABSENT/data_invalid/data_format_rejected - There's a required parameter which is not present in the request".format(status))
            logging.info("Status: {} / BAD REQUEST PARAMETER_ABSENT/data_invalid/data_format_rejected - There's a required parameter which is not present in the request".format(status))
        elif status == 401:
            print ('Status: {} / UNAUTHORIZED: Failed to authenticate the request CONSUMER_KEY_UNKNOWN/TOKEN_INVALID/UNAUTHORIZED'.format(status))
            logging.info('Status: {} / UNAUTHORIZED: Failed to authenticate the request CONSUMER_KEY_UNKNOWN/TOKEN_INVALID/UNAUTHORIZED'.format(status))
        elif status == 572:
            print ('Status: {} / TOKEN_EXPIRED The TEMPORARY access token generated by the platform has expired and can no longer be used'.format(status))
            logging.info('Status: {} / TOKEN_EXPIRED The TEMPORARY access token generated by the platform has expired and can no longer be used'.format(status))
        elif status == 403:
            print ('Status: {} / PERMISSION_DENIED Subscriber has temporarily disallowed access to his private data'.format(status))
            logging.info('Status: {} / PERMISSION_DENIED Subscriber has temporarily disallowed access to his private data'.format(status))
        elif status == 570:
            print ('Status: {} / REQUEST_NOT_FOUND Registration request not found'.format(status))
            logging.info('Status: {} / REQUEST_NOT_FOUND Registration request not found'.format(status))
        else:
            print ('Error status: {} /'.format(status))
            logging.info('Error status: {} /'.format(status))


    def set_headers(self):
        '''headers for API calls'''

        '''
        {
                'Content-Type': 'application/json; charset=utf-8',
                'Content-Encoding': 'gzip',
                'Accept-Encoding': 'gzip, deflate, br',
                'User-Agent': 'PostmanRuntime/7.26.3',
                'cache-control':'no-cache',
                'Accept':'*/*',
                #'Host': 'https://cdn-api.co-vin.in'
            }
        '''

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
                   "Upgrade-Insecure-Requests": "1","DNT": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                   "Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"}

        return headers

    def set_proxy(self):

        '''
        return {
                'host':"10.17.9.170",
                'port':'8080',
                'match':"http+https://*/*"
            }
        '''

        http_proxy  = "http://10.10.1.10:3128"
        https_proxy = "https://10.10.1.11:1080"

        proxy ={
              "http"  : http_proxy,
              "https" : https_proxy
            }

        proxy = urllib.request.getproxies()
        return proxy




    def get_state_ids(self):
        '''func to get state ids for India '''

        response = requests.get(url = self._stateId_api, headers = self._headers)
        self.http_response_error(response.status_code)
        if response.status_code==200:
            df = pd.DataFrame.from_dict(response.json()['states'])
            df['state_name'] = df['state_name'].str.strip()
            self.stateids_df = df
        else:
            print("Error in json response for state ids")
            self.stateids_df = pd.DataFrame(columns = ['state_id', 'state_name'])


    def get_district_ids(self, state_id):
        '''func to get district ids
        for given state ids
        '''

        response = requests.get(url = self._districtId_api + str(state_id),
                                headers = self._headers)
        self.http_response_error(response.status_code)
        if response.status_code==200:
            df = pd.DataFrame.from_dict(response.json()['districts'])
            df['district_name'] = df['district_name'].str.strip()
            return df
        else:
            print("Error in json response for district ids")
            return pd.DataFrame(columns = ['district_id', 'district_name'])

    def availability(self,  searchKey, searchValue, date):
        '''checks vaccine availbility by input type
        gens url for input type i.e. district or pincode
        returns availbility response
        '''

        url = self.build_url(searchKey, searchValue, date)
        response = requests.get(url = url, headers = self._headers)
        self.http_response_error(response.status_code)
        if response.status_code==200 and len(response.json()['sessions'])>0:
            df = pd.DataFrame.from_dict(response.json()['sessions'])
            if df.empty==False and df[df['available_capacity']>0].empty==False :
                df = df[(df['available_capacity']>0)]
                df['slots'] = df['slots'].apply(lambda row: "<pre>"+'<br>'.join(row)+"</pre>")
                #df['date'] = df['date'].apply(lambda row: "<pre>"+str(date)+"</pre>")
                df = df[output_cols]
                
                if min_age!=None:
                    df = df[df['min_age_limit']==min_age]
                if vaccine_type!=None:
                    df = df[df['vaccine']==vaccine_type]
                    
                return df
            else:
                return pd.DataFrame(columns=output_cols)
        else:
            print(f"No slot avialable for {searchKey}: {searchValue}")
            logging.info((f"No slot avialable for {searchKey}: {searchValue}"))
            return pd.DataFrame(columns=output_cols)

def send_desktop_notification(message):
    '''
    Func to send desktop notifications for vaccine availbilty

    Returns
    -------
    None.

    '''
    
    title = 'CoWin vaccine availability !!!'
    message= 'Vaccine available.....'
    notification.notify(title= title,
                    message= message,
                    app_icon = os.path.join(curr_dir,"icon.ico"),
                    timeout= 100,
                    toast=False)



def set_user_preferences():
    
    global pincode_bool,pincode_list,district_bool,district_list,min_age,vaccine_type

    print("Welcome to CoWin Vaccine Alerts !\nPlease enter your preferences\n")
    pincode_bool = input("Do you want to search by Pincode ? Type y for yes / n for no\n")
    pincode_bool = True if (str.lower(pincode_bool)=='y') else False
    if pincode_bool:
        pincode_list = (input("\nEnter pincode to track vaccine availability, \
                              \ne.g. single pincode -> 111111 \n entering multiple pincodes -> 1111,1112\n")).split(",")
        print(f"Tracking vaccine slots for pincodes {pincode_list}\n")
        pincode_list = [ int(pin) for pin in pincode_list]
    district_bool = input("Do you want to search by District ? Type y for yes / n for no\n")
    district_bool = True if (str.lower(district_bool)=='y') else False
    if district_bool:
        district_list = (input("\nEnter district name to track vaccine availability, \
                              \ne.g. single district -> Mumbai \n entering multiple pincodes -> Mumbai,Thane,Kochi\n")).split(",")
        district_list = [ str.capitalize(str.lower(dist)) for dist in district_list]
        print(f"Tracking vaccine slots for {district_list}\n")
    
    print("Set filters as per minimum age and/or vaccine type\n")
    min_age = input("Enter minimum age eligibility\n 18 or 45 \nPress enter key to track both\n")
    min_age = None if min_age=='' else int(min_age)
    
    vaccine_type = input("Enter vaccine type, e.g. covaxin or covishield\nPress enter key to track both\n")
    vaccine_type = None if vaccine_type=='' else str.upper(vaccine_type)
    
    

def main(cowin_obj):

    d = datetime.datetime.now().date()
    #date = d.strftime("%d-%m-%Y")

    #d = d.strftime("%d-%m-%Y")
    #cowin_obj = coWin()
    available_count = 0
    if pincode_bool==True:
        print ("search avilability by pincode...")
        msg_body = 'coWin portal: Vaccine availability from {} to {} <br>'.format(d, d+datetime.timedelta(days=7))
        # get pincodes master
        result_df = pd.DataFrame()
        for i in range(7):
            date = (d+datetime.timedelta(days=i)).strftime("%d-%m-%Y")
            for pincode in pincode_list:
                print(pincode, date)
                df = cowin_obj.availability('pincode', pincode, date)
                time.sleep(2)
                if df.empty==False:
                    result_df = result_df.append(df, ignore_index=True)
                    available_count += 1

    if district_bool==True:
        print("Search avilability by district...")
         
        districtdf = pd.DataFrame()
        for i in range(7):
            date = (d+datetime.timedelta(days=i)).strftime("%d-%m-%Y")
                
            for _, row in cowin_obj.district_df.iterrows():
                #dist_df = pd.DataFrame()
                temp = cowin_obj.availability('district_id', row['district_id'], date)
                time.sleep(2)
                if temp.empty==False:
                    #dist_df = dist_df.append(temp, ignore_index=True)
                    available_count += 1
                    districtdf = districtdf.append(temp, ignore_index=True)

    if available_count>=1:
        print("Slots available...")
        if result_df.empty==False:
            msg_body +=  "\nVaccine available at pincodes {} for dates {} \n".format(set(result_df['pincode'].values.tolist()),
                                                                                set(result_df['date'].values.tolist()))
        
        if districtdf.empty==False:
            msg_body +=  "\nVaccine available at district {} @ pincodes {} for dates {}".format(
                            set(districtdf['district_name'].values.tolist()),
                            set(districtdf['pincode'].values.tolist()),
                            set(districtdf['date'].values.tolist()))
        
        send_desktop_notification(msg_body)
        

# driver code
if __name__ == "__main__":
    
    # get user inputs
    set_user_preferences()
    
    cowin_obj = coWin()
    
    while 1:
        main(cowin_obj)
        print("-------------------------------------------------------------------------")
        
        time.sleep(60*5)
    