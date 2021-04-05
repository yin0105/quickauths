import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from insurance.WebPT.WebptEntryData import *
import time
import json
import logging
from logging.handlers import RotatingFileHandler
from pprint import pprint
import os


logging.basicConfig(handlers=[RotatingFileHandler(filename='SystemLog.log', mode='a', maxBytes=512000, backupCount=4)],
                    level='DEBUG',
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m/%d/%Y%I:%M:%S %p')

logger = logging.getLogger('my_logger')

class WebPT:
    driver = {}

    def EMR_Auth_Entry(self, authorizations, settings):
        print('*********STARTING EMR AUTH ENTRY*********')
        with open(f'insurance/config.json') as f:
            data = json.load(f)
        print(data)
        logger.info(data)

        submitted_by_dev = data['submitted_by_dev']

        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

        chromeOptions.add_argument("--headless")
        chromeOptions.add_argument("--window-size=1680, 1050")
        chromeOptions.add_argument("--disable-dev-shm-usage")
        chromeOptions.add_argument("--no-sandbox")

        self.driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chromeOptions)

        self.driver.implicitly_wait(2)
        self.driver.get("https://auth.webpt.com/")

        self.is_element_exist("//input[@id='login-username']").send_keys(settings.username)
        self.get_element_by_path("//input[@id='login-password']").send_keys(settings.password)
        self.get_element_by_path("//input[@id='login-button']").click()

        try:
            self.is_element_exist("//button[contains(text(),'Yes, oust them!')]", 2).click()
        except:
            pass
        print("Logged into WebPT")
        
        webpt_list = []
        i = 0
        for auth in authorizations:
            webpt = WebptEntryData()
            webpt.DOB = auth['DOB']
            webpt.FirstName = auth['FirstName']
            webpt.LastName = auth['LastName']
            webpt.DateSubmitted = auth['DateSubmitted']
            webpt.ReferenceNumber = auth['ReferenceNumber']
            webpt.member_ID = auth['MemberId']
            # webpt.Message = auth['Message']
            try:
                try:
                    print(f"Starting on Member:, {auth['FirstName']} {auth['LastName']}")
                    try:
                        self.is_element_exist("//a[contains(text(),'Display Patients')]").click()
                        print('Display Patients Clicked')
                        try:
                            alert = self.driver.switch_to.alert
                            time.sleep(1)
                            alert.accept()
                        except:
                            pass
                        last_name_box = self.is_element_exist("//input[@id='LastNameID']", 5)
                        last_name_box.send_keys(auth['LastName'])
                        logger.info('Added Last Name for Search')
                        self.get_element_by_path("//input[@id='ext-comp-1007']").send_keys(auth['DOB'][:2])
                        self.get_element_by_path("//input[@id='ext-comp-1009']").send_keys(auth['DOB'][3:5])
                        self.get_element_by_path("//input[@id='ext-comp-1011']").send_keys(auth['DOB'][6:])
                        logger.info('Added DOB')
                        self.get_element_by_path("//*[@id='ext-gen101']").click()
                        self.get_element_by_path("//div[contains(text(),'Active')]").click()
                        logger.info('Active Status Selected')
                        button = self.get_element_by_path('//*[@class=" x-btn-text base-default-button-text"]')
                        time.sleep(.5)
                        button.send_keys(Keys.ENTER)
                        self.is_element_exist("//a[@class='ta--patient-search-results--chart-link']", 5).click()
                        print("Last Name Search Worked")
                        logger.info('Last Name Search Worked')
                    except:
                        print("Last name search failed")
                        logger.info('Last Name Search Failed')
                        last_name_box.clear()
                        first_name_box = self.get_element_by_path("//input[@id='FirstNameID']")
                        first_name_box.send_keys(auth['FirstName'])
                        button.send_keys(Keys.ENTER)
                        logger.info('Added First Name for Search')
                        # time.sleep(1)
                        self.is_element_exist("//a[@class='ta--patient-search-results--chart-link']", 5).click()
                        print("First name search worked!")
                        logger.info('First Name Search Worked')
                except:
                    logger.debug(f'Error Finding Member: {auth["FirstName"]} {auth["LastName"]}')
                    print(f'Error Finding Member: {auth["FirstName"]} {auth["LastName"]}')
                    webpt.Message = f'Error Name Search: {auth["FirstName"]} {auth["LastName"]}'
                    webpt_list.append(webpt)
                    continue

                    # when there are 2 active cases, this gets rid of the alert
                try:
                    self.get_element_by_path("//button[@id='ext-gen18']").click()
                except:
                    pass

                text_box_text = self.is_element_exist("//*[@class='wPTStylePatientAdditionalInfo']").text
                text_box_split = text_box_text.splitlines()
                rx = f"{text_box_split[0]}"
                logger.info('Captured Control Box')

                self.get_element_by_path("//a[contains(text(),'Patient Info')]").click()
                logger.info('Patient Info Clicked')

                try:
                    print(auth)
                    if auth['Case'] != 'Default':
                        case_element = self.driver.find_element_by_xpath(f"//div[contains(text(),'{auth['Case']}')]")
                        case_name = case_element.text
                    elif auth['Case'] == 'Default':
                        cases = self.driver.find_elements_by_xpath('//*[@id="ext-gen73"]/div[*]/table/tbody/tr/td[1]/div')
                        for c in cases:
                            fullstring = c.text
                            substring = "Discharged"
                            if substring in fullstring:
                                continue
                            else:
                                case_element = c
                                case_name = c.text
                                break
                except:
                    print(f'Error Finding Active Case: {auth["FirstName"]} {auth["LastName"]}')
                    logger.debug(f'Error Finding Active Case: {auth["FirstName"]} {auth["LastName"]}')
                    webpt.Message = f'Error Finding Active Case: {auth["FirstName"]} {auth["LastName"]}'
                    webpt_list.append(webpt)
                    continue
###Control Box###
                try:
                    print(f"Active Case = {case_name}")
                    logger.info(f'Found Active case {case_name}')
                    webpt.Case = case_name
                    clickable = case_element.find_element_by_xpath('../parent::tr/td[10]/div')
                    print('Clicked Case Element')
                    logger.info('Clicked Case Element')
                    clickable.click()
                    time.sleep(1)
                    delete_0_icd = self.get_element_by_path("//div[@class='delete-code-button']")
                    while delete_0_icd != 00 and not None:
                        try:
                            delete_0_icd = self.get_element_by_path("//div[@class='delete-code-button']")
                            delete_0_icd.click()
                            print("Deleted old ICD10 Code")
                            logger.info('Deleted Old ICD')
                        except:
                            break

                    #Sorting ICD10 Codes
                    def key(data):
                        if data[0] == "M":
                            return 1
                        elif data[0] == 'S':
                            return 2
                        elif data[0] == 'R':
                            return 3
                        elif data[0] != 'M' or 'S' or 'R':
                            return 4

                    auth['ICD10'].sort(key=key)
                    print('Sorted:', auth['ICD10'])

                    self.get_element_by_path("//a[contains(text(),'Add new code')]").click()
                    for a in auth['ICD10']:
                        try:
                            icd10_box = self.driver.find_element_by_class_name('icd-search--search-query')
                            icd10_box.send_keys(str(a), Keys.ENTER)
                            logger.info('ICD Seaching')
                            self.get_element_by_path("//tr[@class='icd-finder--code-block is-billable'][1]").click()
                            logger.info('ICD Found and Clicked')
                            print("Added ICD10", str(a))
                            icd10_box.clear()
                        except:
                            logger.debug(f'Error Adding ICD: {a}')
                            print(f'Error Adding ICD: {a}')
                            webpt.Message = f'Error Adding ICD: {a}'
                            webpt_list.append(webpt)
                            continue
                    time.sleep(.5)
                    add_all_codes_button = self.get_element_by_path(
                        "//div[@class='icd-builder--buttons--container']/button[1]")
                    add_all_codes_button.click()
                    logger.info('Add All Codes Button Clicked')
                    text_box = self.get_element_by_path(
                        "//textarea[@class='x-form-textarea x-form-field base-default-textarea ta--case-mgr--additional-info']")
                    text_box.clear()
                    message_text_box = f"""{rx}
{auth['Insurance']}. AUTH SUBMITTED to {auth['Insurance']} @ {auth['Frequency']} for {auth['Visits']} visits on {auth['DateSubmitted']} -Bot"""
                    text_box.send_keys(message_text_box)
                    print("Control Box Comment Added")
                    logger.info('Control Box Comment Added')
                    self.driver.execute_script("window.scrollTo(0, 200)")
                    if submitted_by_dev == '0':
                        ok_box = self.get_element_by_path("//button[contains(text(),'Ok')]")
                        ok_box.click()
                        logger.info('Control Box OK Button Clicked')
                    if submitted_by_dev == '1':
                        self.get_element_by_path('//button[contains(text(),"Cancel")]').click()
                        logger.info('Clicked Cancel Button - Dev Mode')
                except:
                    logger.debug(f'Error Control Box: {auth["FirstName"]} {auth["LastName"]}')
                    print(f'Error Control Box: {auth["FirstName"]} {auth["LastName"]}')
                    webpt.Message = f'Error Control Box: {auth["FirstName"]} {auth["LastName"]}'
                    webpt_list.append(webpt)
                    continue


                self.get_element_by_path("//button[contains(text(),'Save Patient')]").click()
                logger.info('Save Button Clicked')

                self.get_element_by_path("//a[contains(text(),'Patient Info')]").click()
                logger.info('Patient Info Button Clicked')

###Prescription###
                try:
                    if auth['Case'] != 'Default':
                        case_element = self.driver.find_element_by_xpath(f"//div[contains(text(),'{auth['Case']}')]")
                        case_name = case_element.text
                    elif auth['Case'] == 'Default':
                        cases = self.driver.find_elements_by_xpath('//*[@id="ext-gen73"]/div[*]/table/tbody/tr/td[1]/div')
                        for c in cases:
                            fullstring = c.text
                            substring = "Discharged"
                            if substring in fullstring:
                                continue
                            else:
                                case_element = c
                                case_name = c.text
                                break
                except:
                    print(f'Error Finding Active Case: {auth["FirstName"]} {auth["LastName"]}')
                    logger.debug(f'Error Finding Active Case: {auth["FirstName"]} {auth["LastName"]}')
                    webpt.Message = f'Error Finding Active Case: {auth["FirstName"]} {auth["LastName"]}'
                    webpt_list.append(webpt)
                    continue
                try:
                    time.sleep(1)
                    edit_prescription_button = case_element.find_element_by_xpath('../parent::tr/td[8]/div')
                    edit_prescription_button.click()
                    print('Clicked Prescription Element')
                    logger.info('Clicked Prescription Element')

                    self.is_element_exist('//label[contains(text(),"Start Date:")]/../div/div/input').send_keys(auth['DateSubmitted'])
                    logger.info('Start Date Added')
                    self.driver.find_element_by_xpath('//label[contains(text(),"End Date:")]/../div/div/input').send_keys(
                        (datetime.date.today() + datetime.timedelta(days=int(365))).strftime('%m/%d/%Y'))
                    logger.info('End Date Added')
                    self.driver.find_element_by_xpath('//label[contains(text(),"Number of Visits:")]/../div/input').send_keys(auth['Visits'])
                    logger.info('Total Visits Added')
                    frequency_box = self.driver.find_element_by_xpath(
                        '//label[contains(text(),"Frequency:")]/../div/div/input')
                    frequency_box.send_keys(auth['VisitsPer'])
                    frequency_box.send_keys(Keys.ENTER)
                    logger.info('Frequency Added')
                    duration_box = self.driver.find_element_by_xpath(
                        '//label[contains(text(),"Duration:")]/../div/div/input')
                    duration_box.send_keys(auth['PerWeeks'])
                    duration_box.send_keys(Keys.ENTER)
                    logger.info('Frequency Added')
                    self.driver.find_element_by_xpath('//button[contains(text(),"Add")]').click()
                    logger.info('Add Button Clicked')
                    time.sleep(.5)
                    if submitted_by_dev == '0':
                        self.driver.find_element_by_xpath('//button[contains(text(),"Ok")]').click()
                        logger.info('Prescription OK Button Clicked')
                    if submitted_by_dev == '1':
                        self.driver.find_element_by_xpath('//div[contains(text(),"Close")]').click()
                        logger.info('Prescription Close Button Clicked to prevent changes')

                except:
                    logger.debug(f'Error Prescription Box: {auth["FirstName"]} {auth["LastName"]}')
                    print(f'Error Prescription Box: {auth["FirstName"]} {auth["LastName"]}')
                    webpt.Message = f'Error Prescription Box: {auth["FirstName"]} {auth["LastName"]}'
                    webpt_list.append(webpt)
                    continue

                self.get_element_by_path("//button[contains(text(),'Save Patient')]").click()
                logger.info('Prescription Saved')

###Chart Note###
                try:
                    self.is_element_exist("//a[contains(text(),'Chart Notes')]").click()
                    self.is_element_exist("//tbody/tr[1]/td[1]/a[1]/img[1]").click()
                    message = f"AUTH SUBMITTED to {auth['Insurance']} @ {auth['Frequency']} for {auth['Visits']} visits on {auth['DateSubmitted']} -BOT."
                    logger.info('Adding Message')
                    self.get_element_by_path("//textarea[@id='Note']").send_keys(message)
                    if submitted_by_dev == '0':
                        self.get_element_by_path("//tbody/tr[1]/td[1]/input[1]").click()
                        print("Chart Note added")
                        logger.info('Message Added')
                except:
                    logger.debug(f'Error Chart Note: {auth["FirstName"]} {auth["LastName"]}')
                    print(f'Error Chart Note: {auth["FirstName"]} {auth["LastName"]}')
                    webpt.Message = f'Error Chart Note: {auth["FirstName"]} {auth["LastName"]}'
                    webpt_list.append(webpt)
                    continue

            except Exception as ex:
                logger.error(f'Error Member: {auth["FirstName"]} {auth["LastName"]}, Exception:{ex}')
                print(f'Error Member: {auth["FirstName"]} {auth["LastName"]}, Exception:{ex}')
                webpt.Message = f'Error#: {ex}'
                webpt_list.append(webpt)
                continue

            webpt.EMRMessage = 'Auth Entered'

            i = i + 1
            webpt_list.append(webpt)

        self.driver.close()
        for lst in webpt_list:
            pprint(vars(lst))

        return webpt_list

    def EMR_Approval_Entry(self, approvals, settings):
        print('*********STARTING EMR APPROVAL ENTRY*********')
        with open(f'insurance/config.json') as f:
            data = json.load(f)
        print(data)
        logger.info(data)

        submitted_by_dev = data['submitted_by_dev']

        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

        chromeOptions.add_argument("--headless")
        chromeOptions.add_argument("--window-size=1680, 1050")
        chromeOptions.add_argument("--disable-dev-shm-usage")
        chromeOptions.add_argument("--no-sandbox")

        self.driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chromeOptions)

        self.driver.get("https://auth.webpt.com/")

        self.get_element_by_path("//input[@id='login-username']").send_keys(settings.username)
        self.get_element_by_path("//input[@id='login-password']").send_keys(settings.password)
        self.get_element_by_path("//input[@id='login-button']").click()

        try:
            self.is_element_exist("//button[contains(text(),'Yes, oust them!')]").click()
        except:
            pass
        print("Logged into webpt")

        process_list = []
        i = 0
        for app in approvals:
            try:
                webpt = WebptEntryData()
                webpt.ReferenceNumber = app['ReferenceNumber']
                webpt.DOB = app['DOB']
                webpt.FirstName = app['FirstName']
                webpt.LastName = app['LastName']
                webpt.ExpirationDate = app['ExpirationDate']
                webpt.member_ID = app['Id']

                print(f"Starting on Member:', {app['FirstName']} {app['LastName']}")
                try:
                    try:
                        self.get_element_by_path("//a[contains(text(),'Display Patients')]").click()
                        last_name_box = self.is_element_exist("//input[@id='LastNameID']", 5)
                        last_name_box.send_keys(app['LastName'])
                        logger.info('Added Last Name to Search')
                        # self.get_element_by_path("//input[@id='ext-comp-1007']").send_keys(app['DOBMonth'])
                        # self.get_element_by_path("//input[@id='ext-comp-1009']").send_keys(app['DOBDay'])
                        self.get_element_by_path("//input[@id='ext-comp-1011']").send_keys(app['DOBYear'])
                        logger.info('Added DOB')
                        self.get_element_by_path("//*[@id='ext-gen101']").click()
                        self.get_element_by_path("//div[contains(text(),'Active')]").click()
                        logger.info('Active Status Selected')
                        button = self.get_element_by_path('//*[@class=" x-btn-text base-default-button-text"]')
                        button.send_keys(Keys.ENTER)
                        time.sleep(.5)
                        self.is_element_exist("//a[@class='ta--patient-search-results--chart-link']", 5).click()
                        print("Last name search worked!")
                        logger.info('Last Name Search Worked')
                    except:
                        print("Last name search failed")
                        logger.info('Last Name Search Failed')
                        last_name_box.clear()
                        first_name_box = self.get_element_by_path("//input[@id='FirstNameID']")
                        first_name_box.send_keys(app['FirstName'])
                        button.send_keys(Keys.ENTER)
                        logger.info('Added First Name for Search')
                        time.sleep(.5)
                        self.is_element_exist("//a[@class='ta--patient-search-results--chart-link']", 5).click()
                        print("First name search worked!")
                        logger.info('First Name Search Worked')
                except:
                    logger.debug(f"Error Finding Member: {app['FirstName']} {app['LastName']}")
                    print(f"Error Finding Member: {app['FirstName']} {app['LastName']}")
                    webpt.Message = f"Error Finding Member: {app['FirstName']} {app['LastName']}"
                    process_list.append(webpt)
                    continue

                # when there are 2 active cases, this gets rid of the alert
                try:
                    self.get_element_by_path("//button[@id='ext-gen18']").click()
                except:
                    pass

                # Get Control Box Info
                text_box_text = self.is_element_exist("//*[@class='wPTStylePatientAdditionalInfo']").text
                text_box_split = text_box_text.splitlines()
                rx = f"{text_box_split[0]}"
                logger.info('Captured Control Box')

                self.get_element_by_path("//a[contains(text(),'Patient Info')]").click()
                logger.info('Patient Info Clicked')

### AUTHORIZATION ENTRY ###
                # Need to Pull Case Name from the database
                cases = self.driver.find_elements_by_xpath('//*[@id="ext-gen73"]/div[*]/table/tbody/tr/td[1]/div')
                for case in cases:
                    try:
                        fullstring = case.text
                        substring = "Discharged"
                        if substring in fullstring:
                            continue
                        else:
                            webpt.Case = case.text
                            print("Active Case =", case.text)
                            logger.info(f'Found Active case {case.text}')
                            edit_auth_button = case.find_element_by_xpath('../parent::tr/td[9]/div')
                            edit_auth_button.click()
                            print('Clicked Auth Entry Element')
                            logger.info('Clicked Auth Entry Element')

                            auth_num_box = '//label[contains(text(),"Authorization #:")]/../div/input'
                            auth_num_box_element = self.is_element_exist(auth_num_box)
                            auth_num_box_element.send_keys(app['ReferenceNumber'])
                            logger.info('Added Reference Number to Auth Box')

                            auth_visits_box = '//label[contains(text(),"Auth Visits:")]/../div/input'
                            auth_visits_box_element = self.is_element_exist(auth_visits_box)
                            # auth_visits_box_element.send_keys(app['Visits'])
                            auth_visits_box_element.send_keys('0')
                            logger.info('Added Auth Visits')

                            effective_start_box = '//label[contains(text(),"Effective Start:")]/../div/div/input'
                            effective_start_box_element = self.is_element_exist(effective_start_box)
                            effective_start_box_element.send_keys(app['DateSubmitted'])
                            logger.info('Added Start Date')

                            effective_end_box = '//label[contains(text(),"Effective End:")]/../div/div/input'
                            effective_end_box_element = self.is_element_exist(effective_end_box, 5)
                            effective_end_box_element.send_keys(app['ExpirationDate'])
                            logger.info('Added End Date')

                            time.sleep(1)
                            self.get_element_by_path('//button[contains(text(),"Add")]').click()
                            logger.info('Clicked Add Button')
                            time.sleep(1)
                            if submitted_by_dev == '0':
                                self.driver.find_element_by_xpath('//button[contains(text(),"Ok")]').click()
                                logger.info('Prescription OK Button Clicked')
                            if submitted_by_dev == '1':
                                self.driver.find_element_by_xpath('//div[contains(text(),"Close")]').click()
                                logger.info('Prescription Close Button Clicked to prevent changes')

                    except:
                        logger.debug(f"Error Authorization Box: {app['FirstName']} {app['LastName']}")
                        print(f"Error Authorization Box: {app['FirstName']} {app['LastName']}")
                        webpt.Message = f"Error Authorization Box: {app['FirstName']} {app['LastName']}"
                        process_list.append(webpt)
                        continue

                time.sleep(1)
                self.get_element_by_path("//button[contains(text(),'Save Patient')]").click()
                logger.info('Authorization Saved')

                self.is_element_exist("//a[contains(text(),'Patient Info')]").click()
                logger.info('Patient Info Button Clicked')

###Control Box###
                cases = self.driver.find_elements_by_xpath('//*[@id="ext-gen73"]/div[*]/table/tbody/tr/td[1]/div')
                for case in cases:
                    try:
                        fullstring = case.text
                        substring = "Discharged"
                        if substring in fullstring:
                            continue
                        else:
                            clickable = case.find_element_by_xpath('../parent::tr/td[10]/div')
                            clickable.click()
                            time.sleep(1)
                            text_box = self.is_element_exist("//textarea[@class='x-form-textarea x-form-field base-default-textarea ta--case-mgr--additional-info']")
                            text_box.clear()

                            webpt.Approved = app['Approved']

                            message = f"""{rx}
APPROVED, EXPIRE: {app['ExpirationDate']}
-->{app['Approved']}<--
{app['Insurance']} -Bot"""
                            text_box.send_keys(message)
                            self.driver.execute_script("window.scrollTo(0, 200)")
                            if submitted_by_dev == '0':
                                ok_box = self.get_element_by_path("//button[contains(text(),'Ok')]")
                                ok_box.click()
                                logger.info('Control Box OK Button Clicked')
                            if submitted_by_dev == '1':
                                self.get_element_by_path('//button[contains(text(),"Cancel")]').click()
                                logger.info('Clicked Cancel Button - Dev Mode')
                    except:
                        logger.debug(f"Error Control Box: {app['FirstName']} {app['LastName']}")
                        print(f"Error Control Box: {app['FirstName']} {app['LastName']}")
                        webpt.Message = f"Error Control Box: {app['FirstName']} {app['LastName']}"
                        process_list.append(webpt)
                        continue

                self.get_element_by_path("//button[contains(text(),'Save Patient')]").click()
                logger.info('Prescription Saved')

###Chart Notes###
                try:
                    self.is_element_exist("//a[contains(text(),'Chart Notes')]").click()
                    self.is_element_exist("//tbody/tr[1]/td[1]/a[1]/img[1]").click()
                    message_1 = f"""{app['Insurance']} APPROVED *???* Visits, EXPIRE {app['ExpirationDate']}
-->{app['Approved']}<---Bot"""
                    self.is_element_exist("//textarea[@id='Note']").send_keys(message_1)
                    print("Chart Note added")
                    if submitted_by_dev == '0':
                        self.get_element_by_path("//tbody/tr[1]/td[1]/input[1]").click()
                except:
                    logger.debug(f"Error Chart Note: {app['FirstName']} {app['LastName']}")
                    print(f"Error Chart Note: {app['FirstName']} {app['LastName']}")
                    webpt.Message = f"Error Chart Note: {app['FirstName']} {app['LastName']}"
                    process_list.append(webpt)
                    continue

            except Exception as ex:
                logger.error(f"Error Member: {app['FirstName']} {app['LastName']}, Exception:{ex}")
                print(f"Error Member: {app['FirstName']} {app['LastName']}, Exception:{ex}")
                webpt.Message = f"Error Member: {app['ReferenceNumber']}"
                process_list.append(webpt)
                continue

            webpt.EMRMessage = 'Approval Entered'
            i = i + 1
            process_list.append(webpt)

        time.sleep(1)
        self.driver.close()
        for lst in process_list:
            pprint(vars(lst))
        return process_list

    def get_element_by_path(self, element_path):
        logger.debug(f'finding element: {element_path}')
        print(f'finding element {element_path}')
        return self.driver.find_element_by_xpath(element_path)

    def is_element_exist(self, val, timeout=5):
        try:
            logger.debug(f'finding element {val} with timeout {timeout}')
            print(f'finding element {val} with timeout {timeout}')
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, val)))
            return element
        except:
            print('Unable to find element')