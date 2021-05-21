# -*- coding: utf-8 -*-
"""
Created on Thu May 13 19:00:26 2021

@author: krishnay
"""

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import os
import datetime
from webdriver_manager.chrome import ChromeDriverManager
import winsound
    

curr_dir = os.getcwd()

class CoWin():
    '''
    Get sound ALerts on avaliable time slot and book appointment
    '''

    def __init__(self):

        self._cowin_url = "https://selfregistration.cowin.gov.in/"
        #self._cowin_url = "https://www.cowin.gov.in/home
        self.set_user_prefrences()
        self.driver = self.set_proxy_details()
        
    def set_user_prefrences(self):
        '''
        Func to read user inputs
        for which appointment is to be made
        '''
        inputs = []
        with open("Input.csv","r") as f:
            for line in f.readlines():
                inputs.append([l.replace("\n","") for l in line.split("|")])
        self._mobile_no = inputs[1][0]
        self._vaccinename = inputs[1][1]
        self._agelimit = inputs[1][2]
        self._pincodes = inputs[1][3].split(",")
        self._username = inputs[1][4]
    

   
    def set_proxy_details(self):
        '''Func to set proxy for driver'''

        opts = Options()
        # Add headers
        user_agent =  ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/39.0.2171.95 Safari/537.36')
        opts.add_argument(f'user-agent={user_agent}')
        # Remove the Automation Info
        opts.add_argument('--disable-infobars')
        #opts.add_argument("headless")
        opts.add_argument('--disable-gpu')
        opts.add_argument("--log-level=3")  # fatal


        #driver = webdriver.Chrome("chromedriver.exe", chrome_options=opts)
        driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=opts)
        #driver.minimize_window()
        print ("Proxy details set for the session")
        return driver
     
    
    def login(self):
        '''
        Login to cowin portal 
        Takes mobile number as input

        Returns
        -------
        None.

        '''
        
        try:
            self.driver.get(self._cowin_url)
            time.sleep(10)
            query = WebDriverWait(self.driver, 120).until(
                                EC.presence_of_element_located((By.TAG_NAME, "input")))
            query.send_keys(self._mobile_no)
            time.sleep(2)
            # click on get otp button
            self.driver.find_element_by_class_name('covid-button-desktop').click()
            # manually enter OTP on site
            print("Please enter OTP on Cowin portal and click on Verify & proceed\n")
            time.sleep(80)
            
            query = WebDriverWait(self.driver, 120).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "beneficiary-box")))
            query = query.find_elements_by_class_name("sepreetor")     
            
            for row in query:
                user = row.find_element_by_class_name("fulanmecls").text.lower()
                print(user)
                if self._username.lower() in user:
                    row.find_element_by_link_text("Schedule").click()
                
            # scroll
            print("Scroll down....")
            self.driver.find_element_by_tag_name("body").click()
            self.driver.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
            
            query = self.driver.find_elements_by_class_name("sepreetor")     
            time.sleep(2)
            for row in query:
                if self._username.lower() in row.find_element_by_class_name("fulanmecls").text.lower():
                    print(f"Found user {self._username}")
                    time.sleep(1)
                    row.find_element_by_link_text("Schedule").click()
                        
            
            #self.driver.find_element_by_class_name('next-btn').click()
            #print("Logged in successfully !!!")
            #print ("Select users for whom appointment is to be made, use already open chrome !")
            
            # select for whom to schedule
            #WebDriverWait(self.driver, 180).until(EC.element_to_be_clickable((By.CLASS_NAME, 'register-btn'))).click()
            
            time.sleep(2)
        except Exception as e:
            print ("Exception occured while scheduling appointment !")
            print (e)
            
            
        
        
    def check_appointent(self):
        """
        look for appointment and create sound alerts !!!
        """
        try:
                
            while 1:
                # check for appointments  
                print ("Checking for appointments.....")
                for pincode in self._pincodes:
                    query = WebDriverWait(self.driver, 60).until(
                                        EC.presence_of_element_located((By.ID, "mat-input-2")))
                    query.clear()
                    query.send_keys(pincode)
                    time.sleep(2)
                    # press search button
                    self.driver.find_element_by_class_name('pin-search-btn').click()
                    # check if bookings available
                    # slot-available-wrap
                    center_ul_list = self.driver.find_elements_by_class_name("slot-available-wrap")
                    
                    # for every center look into UL and check for appointment status
                    for center_ul in center_ul_list:
                        for slot in center_ul.find_elements_by_tag_name("li"):
                            status = slot.text
                            if (not status.startswith("Booked")) and (not status.startswith("NA")):
                                # check if meeting criteria
                                if (self._vaccinename!='' or self._vaccinename!=' ') and self._agelimit+"+" in status:
                                    print ("Slots available, proceed with bookings.... ")
                                    try:
                                        slot.find_element_by_link_text(status.split("\n")[0]).click()
                                        return 1
                                    except Exception as e:
                                        print (e)          
                                
                                if self._vaccinename.upper() in status and self._agelimit+"+" in status:
                                    print ("Slots available, proceed with bookings.... ")
                                    try:
                                        slot.find_element_by_link_text(status.split("\n")[0]).click()
                                        return 1
                                    except Exception as e:
                                        print (e)
                            print("No slots available for now....sleep and check again...")        
                                    
                    time.sleep(2)
                # sleep for 10 seconds before checking again
                time.sleep(10)
        except Exception as e:
            print (e)
            return -1
                  

def main():
    
    cowin_obj = CoWin()
    cowin_obj.login()
    while 1:
        run = cowin_obj.check_appointent()
        if run==-1:
            # re-login
            cowin_obj.driver.delete_all_cookies()
            cowin_obj.login()
        elif run==1:
            # make repeated sound to alert user, in order to enter capctha and confirm booking
            duration = 1000*120  # milliseconds
            freq = 440  # Hz
            winsound.Beep(freq, duration)
            break
        
    
    
if __name__=='__main__':
    main()
