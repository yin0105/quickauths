from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from logging.handlers import RotatingFileHandler
import json
from insurance.EligibilityStatus.MediCal.PatientNewRequestData import PatientNewRequestData
import re
import datetime
from pprint import pprint
import os
from random import *


logging.basicConfig(handlers=[RotatingFileHandler(filename='insurance/logs/SystemLog.log', mode='a', maxBytes=512000, backupCount=4)],
                    level='DEBUG',
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m/%d/%Y%I:%M:%S %p')

logger = logging.getLogger('my_logger')

class EligibilityCheck:
    
    members = []
    driver = {}

    def start_execution(self, members, settings):
        with open('insurance/config.json') as f:
            data = json.load(f)
        print(data)
        logger.info(data)

        user_name = settings.username
        user_password = settings.password
        submitted_by_dev = data['submitted_by_dev']

        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

        chromeOptions.add_argument("--headless")
        chromeOptions.add_argument("--window-size=1680, 1050")
        chromeOptions.add_argument("--disable-dev-shm-usage")
        chromeOptions.add_argument("--no-sandbox")

        self.driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chromeOptions)
        # self.driver = webdriver.Chrome(executable_path="insurance/chromedriver", chrome_options=chromeOptions)

        self.driver.get("https://www.medi-cal.ca.gov/MCWebPub/Login.aspx?ReturnUrl=%2fCommon%2fMenu.aspx")

        #Logging in
        username = self.get_element_by_path('//*[@id="MainContent_txtUserID"]').send_keys(user_name)
        password = self.get_element_by_path('//*[@id="MainContent_txtPassword"]').send_keys(user_password)
        submitbutton = self.get_element_by_path('//*[@id="MainContent_btnSubmit"]').click()

        process_list = []
        i = 0
        for member in members:
            try:
                request = PatientNewRequestData()
                request.MemberId = member.member_ID
                request.DateSubmitted = datetime.date.today().strftime('%m/%d/%Y')
                request.DOB = member.dob
                logger.info(f'Processing memberId: {member.member_ID}')
                print(f'Checking eligibility for {member.member_ID}')
                try:
                    eligibilitybutton = self.is_element_exist("//span[contains(text(),'Eligibility')]", 5).click()
                    time.sleep(.5)
                    singlesubscriberbutton = self.is_element_exist("//li[@class='oItem']//a[contains(text(),'Single Subscriber')]").click()
                except:
                    print('Main eligibility button failed, will try logging back in')
                    self.driver.get("https://www.medi-cal.ca.gov/MCWebPub/Login.aspx?ReturnUrl=%2fCommon%2fMenu.aspx")
                    username = self.get_element_by_path('//*[@id="MainContent_txtUserID"]').send_keys(user_name)
                    password = self.get_element_by_path('//*[@id="MainContent_txtPassword"]').send_keys(user_password)
                    submitbutton = self.get_element_by_path('//*[@id="MainContent_btnSubmit"]').click()
                    eligibilitybutton = self.is_element_exist("//span[contains(text(),'Eligibility')]", 5).click()
                    time.sleep(.5)
                    singlesubscriberbutton = self.is_element_exist("//li[@class='oItem']//a[contains(text(),'Single Subscriber')]").click()

                sub_id_box = self.is_element_exist("//input[@id='MainContent_RecipID']", 5).send_keys(member.member_ID)
                dob_box = self.is_element_exist("//input[@id='MainContent_RecipDOB']", 5).send_keys(member.dob.strftime('%m/%d/%Y'))
                date_path_box = self.is_element_exist("//input[@id='MainContent_RecipDOI']").send_keys(datetime.date.today().strftime('%m%d%Y'))
                date_path2_box = self.is_element_exist("//input[@id='MainContent_RecipDOS']").send_keys(datetime.date.today().strftime('%m%d%Y'))
                submitbutton2 = self.driver.find_element_by_xpath('//*[@id="MainContent_Submit"]').click()


                # Eligibility Screen
                try:
                    name_array = self.is_element_exist("/html[1]/body[1]/main[1]/form[1]/div[3]/div[1]/div[1]/div[2]/div[2]/div[2]/table[1]/tbody[1]/tr[1]/td[2]/table[1]/tbody[1]/tr[1]/td[1]/font[2]/center[1]/b[1]", 5).text
                    name_array = re.split(',', name_array)
                    if len(name_array) == 2:
                        first_name = name_array[-1]
                        last_name = name_array[0]
                        request.firstName = first_name
                        request.lastName = last_name
                    elif len(name_array) == 1:
                        first_name = name_array[0]
                        request.firstName = first_name
                    print(f'Member Found: {first_name} {last_name}')
                    logger.debug(f'Member Found: {first_name} {last_name}')

                except Exception as ex:
                    logger.error(f'ERROR Finding Member: {member.member_ID}')
                    print(f'ERROR Finding Member: {ex}')
                    request.Message = f'Error Finding Member: {ex}'
                    request.plan = 'Error Finding Member'
                    process_list.append(request)
                    continue

                try:
                    if self.is_element_exist(f'//*[@src="/Images/GreenLt.gif"]', .5):
                            print('Eligible')
                            request.eligibility = 'Eligible'
                    elif self.is_element_exist(f'//*[@src="/Images/YeloLt.gif"]', .5):
                            print('Pending Change')
                            request.eligibility = 'Pending Change'
                    elif self.is_element_exist(f'//*[@src="/Images/RedLt.gif"]', .5):
                            print('Not Eligible')
                            request.eligibility = 'Not Eligible'
                except Exception as ex:
                    logger.error(f'ERROR Finding Status: {member.member_ID}')
                    print(f'ERROR Finding Status: {ex}')
                    request.Message = f'Error Finding Status: {ex}'
                    request.plan = 'Error Finding Status'
                    process_list.append(request)
                    continue

                status_plan = self.get_element_by_path("//span[@id='MainContent_lblMessages']").text
                status_plan = status_plan.split("DOWN.")[-1].split(': ')
                try:
                    status_plan = f'{status_plan[1].strip()}'
                    print(status_plan)
                    request.plan = status_plan
                except:
                    print('No Plan')
                    logger.debug('No Plan')
                    request.plan = ''

            except Exception as ex:
                logger.error(f'ERROR. member: {member.member_ID}, Exception: {ex}')
                print(f'ERROR: {ex}')
                request.Message = f'Error: {ex}'
                process_list.append(request)
                continue

            i = i + 1
            process_list.append(request)

        self.driver.close()
        self.driver.quit()
        print('All Members Processed')

        for lst in process_list:
            pprint(vars(lst))
        
        return process_list

    def is_element_exist(self, val, timeout=5):
        try:
            logger.debug(f'finding element {val} with timeout {timeout}')
            print(f'finding element {val} with timeout {timeout}')
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, val)))
            return element
        except:
            print('Unable to find element')

    def frame_switch(self, val, timeout=2):
        try:
            frame = WebDriverWait(self.driver, timeout).until(EC.frame_to_be_available_and_switch_to_it((By.NAME, val)))
            print(f'Switching to frame: {val}')
            logger.debug(f'Switching to frame: {val}')
            return frame
        except:
            print(f'Unable to Switch Frame: {val}')

    def get_element_by_path(self, element_path):
        logger.debug(f'finding element: {element_path}')
        return self.driver.find_element_by_xpath(element_path)

    def remove_null_value(value):
        logger.debug(f'remove_null_value {value}')
        if value is not None:
            return True
        return False

    def SubmitRequest(self, memberList, settings):
        logger.info('============================ Start program ==============================')
        try:
            for member in memberList:
                print('MemberId: ' + str(member.member_ID))
            # start processing data
            return self.start_execution(memberList, settings)
        except Exception as ex:
            raise Exception(ex)