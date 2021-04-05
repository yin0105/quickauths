import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from logging.handlers import RotatingFileHandler
import json
from insurance.NewRequest.MediCal.PatientNewRequestData import PatientNewRequestData
from pprint import pprint
import re
import os

logging.basicConfig(handlers=[RotatingFileHandler(filename='insurance/logs/SystemLog.log', mode='a', maxBytes=512000, backupCount=4)],
                    level='DEBUG',
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m/%d/%Y%I:%M:%S %p')

logger = logging.getLogger('my_logger')

class AuthRequest:
    driver = {}

    def start_execution(self, members, settings):
        with open('insurance/config.json') as f:
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

        self.driver.get("https://www.medi-cal.ca.gov/MCWebPub/Login.aspx?ReturnUrl=%2fCommon%2fMenu.aspx")

        # Logging in
        self.driver.implicitly_wait(1)
        user_name = settings.username  # data['user_name']
        user_password = settings.password  # data['user_password']
        username = self.driver.find_element_by_css_selector("#MainContent_txtUserID")
        username.send_keys(user_name)
        password = self.driver.find_element_by_css_selector("#MainContent_txtPassword")
        password.send_keys(user_password)
        submitbutton = self.driver.find_element_by_css_selector("#MainContent_btnSubmit")
        submitbutton.click()

        # webpt_entry_list = []
        process_list = []
        i = 0
        for member in members:
            # Check Eligibility
            request = PatientNewRequestData()
            request.Id = member['MemberId']
            request.DateSubmitted = member['StartDateFormatted']
            try:
                elegibilitybutton_path = "//span[contains(text(),'Eligibility')]"
                self.is_element_exist(elegibilitybutton_path).click()
                singlesubscriberbutton_path = "//li[@class='oItem']//a[contains(text(),'Single Subscriber')]"
                self.is_element_exist(singlesubscriberbutton_path).click()
                subid_path = "//input[@id='MainContent_RecipID']"
                self.is_element_exist(subid_path).send_keys(member['MemberId'])
                print("Working on:", member['MemberId'])
                dob_path_path = "//input[@id='MainContent_RecipDOB']"
                self.is_element_exist(dob_path_path).send_keys(member['DOB'])
                date_path_path = "//input[@id='MainContent_RecipDOI']"
                self.is_element_exist(date_path_path).send_keys(member['StartDateFormatted'])
                date_path_2_path = "//input[@id='MainContent_RecipDOS']"
                self.is_element_exist(date_path_2_path).send_keys(member['StartDateFormatted'])
                submitbutton2 = self.driver.find_element_by_css_selector("#MainContent_Submit")
                submitbutton2.click()

                # Eligibility Screen
                self.is_element_exist("//span[@id='MainContent_lblMessages']")
                name_array_status = self.is_element_exist(
                    "/html[1]/body[1]/main[1]/form[1]/div[3]/div[1]/div[1]/div[2]/div[2]/div[2]/table[1]/tbody[1]/tr[1]/td[2]/table[1]/tbody[1]/tr[1]/td[1]/font[2]/center[1]/b[1]").text
                name_array = re.split(',', name_array_status)
                if len(name_array) == 2:
                    request.FirstName = name_array[-1].strip()
                    request.LastName = name_array[0].strip()
                if len(name_array) == 1:
                    request.FirstName = name_array[0].strip()
                print(f'Found Member: {request.FirstName} {request.LastName}')

                if self.is_element_exist(f'//*[@src="/Images/GreenLt.gif"]'):
                    print(f'{request.FirstName} {request.LastName}: Eligible')
                    request.Eligibility = 'Eligible'
                elif self.is_element_exist(f'//*[@src="/Images/YeloLt.gif"]'):
                    print(f'{request.FirstName} {request.LastName}: Pending Change')
                    request.Eligibility = 'Pending Change'
                elif self.is_element_exist(f'//*[@src="/Images/RedLt.gif"]'):
                    print(f'{request.FirstName} {request.LastName}: Not Eligbile')
                    request.Eligibility = 'Not Eligible'

                if request.Eligibility == "Eligible" or "Pending Change":
                    WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'eTAR')]")))
                    self.driver.find_element_by_xpath("//span[contains(text(),'eTAR')]").click()
                    WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//li[@class='oItem']//a[contains(text(),'Medical Services')]")))
                    self.driver.find_element_by_xpath("//li[@class='oItem']//a[contains(text(),'Medical Services')]").click()
                    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(),'Create a New TAR')]")))
                    self.driver.find_element_by_xpath("//a[contains(text(),'Create a New TAR')]").click()
                    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//tr//tr[2]//td[1]//span[1]//a[1]")))
                    self.driver.find_element_by_xpath("//tr//tr[2]//td[1]//span[1]//a[1]").click()
                    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, "txtTARCompBy")))
                    self.driver.find_element_by_name("txtTARCompBy").send_keys(member['ContactName'])
                    self.driver.find_element_by_xpath("//input[@name='Submit']").click()
                    
                    # Patient Information
                    id_box = self.is_element_exist("//input[@name='MedicalID']")
                    id_box.send_keys(member['MemberId'])

                    last_name_box = self.get_element_by_path("//input[@name='PatLstNme']")
                    last_name_box.send_keys(request.LastName)

                    first_name_box = self.get_element_by_path("//input[@name='PatFrstNme']")
                    first_name_box.send_keys(request.FirstName)

                    dob_box = self.get_element_by_path("//input[@name='PatDOB']")
                    dob_box.send_keys(member['DOB'].replace('/', ''))

                    male_button = self.get_element_by_path("//tr//tr//tr[2]//td[3]//input[1]")
                    female_button = self.get_element_by_path("//td[3]//input[2]")
                    if member['gender'] == "M" or "Male":
                        male_button.click()
                    else:
                        female_button.click()
                    
                    self.get_element_by_path("//input[@name='Submit']").click()
                    
                    # Selecting Service
                    self.get_element_by_path("//a[contains(text(),'Speech')]").click()

                    service_items = [n for n in member['CPTs'] if n['type'] is not None]
                    print('Adding services')
                    logger.info('Adding services')
                    service_count = 1
                    for service in service_items:
                        print(f'Service: {service["type"]} - {service["value"]}')
                        logger.info(f'service: {service["type"]} - {service["value"]}')

                        service_box = self.get_element_by_path("//input[@name='ServiceCode']")
                        service_box.send_keys(service['type'])

                        service_units_box = self.get_element_by_path("//input[@name='TotUnitsReq']")
                        service_units_box.send_keys(service['value'])
                        print(f"Total {service['type']} units =", service['value'])
                        print(member['DOB'])
                        if str(service['type']) == 'x3920':
                            freq_box = self.get_element_by_path("//input[@name='Frequency']")
                            freq_box.send_keys(service['value'])
                            self.get_element_by_path("//select[@name='FrequencyInd']").click()
                            self.get_element_by_path(
                                "//select[@name='FrequencyInd']//option[contains(text(),'Month')]").click()
                        elif str(service['type']) == 'x3900' or str(service['type']) == '97010':
                            freq_box = self.get_element_by_path("//input[@name='Frequency']")
                            freq_calc = int(service['value'])//int(member['PerWeeks'])
                            freq_box.send_keys(freq_calc)
                            self.get_element_by_path("//select[@name='FrequencyInd']").click()
                            self.get_element_by_path(
                                "//select[@name='FrequencyInd']//option[contains(text(),'Week')]").click()
                        elif str(service['type']) == 'x3904':
                            freq_box = self.get_element_by_path("//input[@name='Frequency']")
                            freq_calc = int(service['value'])//int(member['PerWeeks'])
                            freq_box.send_keys(freq_calc)
                            self.get_element_by_path("//select[@name='FrequencyInd']").click()
                            self.get_element_by_path(
                                "//select[@name='FrequencyInd']//option[contains(text(),'Week')]").click()

                        ant_box = self.get_element_by_path("//input[@name='AntLength']")
                        ant_box.send_keys(member['PerWeeks'])
                        self.get_element_by_path("//select[@name='AntLengthInd']").click()
                        self.get_element_by_path("//select[@name='AntLengthInd']//option[contains(text(),'Week')]").click()

                        fromdate = self.driver.find_element_by_css_selector(
                            'td.content table:nth-child(5) tbody:nth-child(1) tr:nth-child(2) td:nth-child(1) > input:nth-child(1)')
                        print("Start date:", member['StartDateFormatted'].replace('/', ''))
                        fromdate.click()
                        fromdate.send_keys(member['StartDateFormatted'].replace('/', ''))

                        thrudate = self.driver.find_element_by_css_selector(
                            "td.content table:nth-child(5) tbody:nth-child(1) tr:nth-child(2) td:nth-child(2) > input:nth-child(1)")
                        print("Thru date:", member['EndDateFormatted'].replace('/', ''))
                        thrudate.click()
                        thrudate.send_keys(member['EndDateFormatted'].replace('/', ''))

                        soc = self.get_element_by_path(
                            "//body[1]/div[3]/div[2]/form[1]/table[1]/tbody[1]/tr[2]/td[2]/table[1]/tbody[1]/tr[1]/td[1]/table[1]/tbody[1]/tr[3]/td[1]/table[4]/tbody[1]/tr[2]/td[3]/input[1]")
                        soc.click()
                        soc.send_keys(member['StartDateFormatted'].replace('/', ''))

                        dd = self.get_element_by_path(
                            "//body[1]/div[3]/div[2]/form[1]/table[1]/tbody[1]/tr[2]/td[2]/table[1]/tbody[1]/tr[1]/td[1]/table[1]/tbody[1]/tr[3]/td[1]/table[4]/tbody[1]/tr[2]/td[4]/input[1]")
                        dd.click()
                        dd.send_keys(member['EndDateFormatted'].replace('/', ''))

                        self.get_element_by_path("//select[@name='POS']")
                        self.get_element_by_path("//body//option[29]").click()

                        self.get_element_by_path("//select[@name='Serv_ICDCodeType']").click()
                        self.get_element_by_path(
                            "//select[@name='Serv_ICDCodeType']//option[contains(text(),'ICD-10')]").click()

                        diagnose_items = [n for n in member['ICDs'] if n is not None]
                        request.ICD10 = diagnose_items
                        i = 0
                        for diag in diagnose_items:
                            if int(i) < 1:
                                icd10box = self.driver.find_element_by_name("Serv_ICD9_1")
                                print("ICD10:", diagnose_items[i])
                                icd10box.send_keys(diagnose_items[i])
                                if int(i) + 1 <= len(diagnose_items):
                                    i = i + 1
                                    continue
                            if int(service_count) <= int(1):
                                if int(i) >= 1:
                                    self.get_element_by_path(f"//tbody/tr[{i+11}]/td[1]/select[1]").click()
                                    self.get_element_by_path(f"//*[@id='middle_column']/form/table/tbody/tr[2]/td[2]/table/tbody/tr/td/table[1]/tbody/tr[3]/td/table[14]/tbody/tr[{i+11}]/td[1]/select/option[2]").click()

                                    icd10box_2Diag = self.get_element_by_path(f"//tbody/tr[{i+11}]/td[2]/input[1]")
                                    print("ICD10:", diagnose_items[i])
                                    icd10box_2Diag.send_keys(diagnose_items[i])
                                    if int(i) + 1 <= len(diagnose_items):
                                        i = i + 1

                        if int(service_count) <= int(1):
                            messagebox = self.driver.find_element_by_name("Medical_Just")
                            messagebox.send_keys(str(member['MedicalJustification']))

                            physician_pres_box = self.driver.find_element_by_name("PhysPresc")
                            print(member['Message'])
                            physician_pres_box.send_keys(member['Message'])

                            phys_name_box = self.driver.find_element_by_name("PhysName")
                            print("Referring Physician Name:", member['RequestingMD'])
                            phys_name_box.send_keys(member['RequestingMD'])

                            pres_date_box = self.driver.find_element_by_name("PrescriptDte")
                            pres_date_box.send_keys(member['PrescriptionDateFormatted'].replace('/', ''))

                        if int(service_count) + 1 <= len(service_items):
                            self.get_element_by_path("//input[@name='CmdSubmit']").click()
                            alert = self.driver.switch_to.alert
                            time.sleep(1)
                            alert.dismiss()
                            service_count = service_count + 1
                            continue
                    if submitted_by_dev == '0':
                        cont_button = self.driver.find_element_by_name("Submit")
                        cont_button.click()
                        alert = self.driver.switch_to.alert
                        alert.dismiss()
                        print(f"Auth Submitted for {request.FirstName} {request.LastName}")

                        # Submit Page
                        time.sleep(1)
                        submit_etar = self.is_element_exist("//body/div[@id='main_content_1']/div[@id='left_column']/div[2]/ul[1]/li[3]/a[1]")
                        submit_etar.click()
                        print("eTar Submitted, now uploading file")

                        upload_button = self.is_element_exist("//tbody/tr[2]/td[1]/input[1]")
                        upload_button.click()

                        auth_cont = self.is_element_exist("//input[@id='submit1']")
                        auth_cont.click()

                        submit_attachment_button = self.is_element_exist("//tbody/tr[1]/td[1]/p[5]/input[1]")
                        submit_attachment_button.click()

                        try:
                            filesArray = member['FilePath'].split(",")
                            files = [n for n in filesArray if n is not None]
                            if len(files) > 0:
                                input = 1
                                for file in files:
                                    logger.info(f'Adding file: {file} for member: {member["MemberId"]}')
                                    print(f'Adding file: {file} for member: {member["MemberId"]}')
                                    choose_file = self.get_element_by_path(f"//tbody/tr[1]/td[1]/div[3]/p[1]/input[{input}]")
                                    if choose_file is None:
                                        request.Message = request.Message + f'Unable to add the document: {file}'
                                        logger.error(f'Failed to add file: {file} to member: {member["MemberId"]}')
                                        continue
                                    choose_file.send_keys(file)
                                    input = input + 1
                            else:
                                print(f'Zero files for member: {member["MemberId"]}')
                                logger.info(f'Zero files for member: {member["MemberId"]}')
                            upload_files = self.is_element_exist("//tbody/tr[1]/td[1]/center[1]/p[1]/input[1]")
                            upload_files.click()
                            print("File uploaded")
                        except:
                            logger.debug(f'Unable to upload file fo member: {member["MemberId"]}')
                            print(f'Unable to upload file fo member: {member["MemberId"]}')
                            request.Message = f'Unable to upload file fo member: {member["MemberId"]}'
                            process_list.append(request)
                            continue

                        #eTAR Number
                        time.sleep(1)
                        final_message = self.is_element_exist(
                            '//*[@id="middle_column"]/div[2]/form/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr[2]/td').text
                        if final_message is None:
                            message = f'eTAR summary screen is not loaded: {member["MemberId"]}'
                            request.Message = message
                            logger.error(f'eTAR summary screen is not loaded for member: {member["MemberId"]}')
                            self.driver.close()
                            process_list.append(request)
                            raise Exception(message)
                        print(final_message)
                        array_1 = re.split('[.]', final_message)
                        array_2 = re.split('[ ]', array_1[0])
                        request.ReferenceNumber = array_2[-1]
                        request.Success = True
                        print(request.ReferenceNumber)

                        dob_array = member['DOB'].split("/")
                        request.DOB = member['DOB']
                        request.DOBMonth = dob_array[0]
                        request.DOBDay = dob_array[1]
                        request.DOBYear = dob_array[2]
                        request.Frequency = member['Freq']
                        request.VisitsPer = member['VisitsPer']
                        request.PerWeeks = member['PerWeeks']
                        request.Insurance = 'Medi-Cal'
                        request.Visits = (int(member['VisitsPer'])*int(member['PerWeeks']))
                        request.Case = member['Case']
                        request.PrescriptionDate = member['PrescriptionDateFormatted']
                        request.AuthStatus = 'Submitted'
                        # request.Message = 'Successful'

                        self.is_element_exist('//*[@id="left_column"]/div[2]/ul[2]/li[1]/a').click()

                    if submitted_by_dev == '1':
                        self.is_element_exist('//*[@id="left_column"]/div[3]/table/tbody/tr/td/ul/li[1]/a').click()
                        dob_array = member['DOB'].split("/")
                        request.DOB = member['DOB']
                        request.DOBMonth = dob_array[0]
                        request.DOBDay = dob_array[1]
                        request.DOBYear = dob_array[2]
                        request.Frequency = member['Freq']
                        request.VisitsPer = member['VisitsPer']
                        request.PerWeeks = member['PerWeeks']
                        request.Insurance = 'Medi-Cal'
                        request.Visits = (int(member['VisitsPer'])*int(member['PerWeeks']))
                        request.Case = member['Case']
                        request.PrescriptionDate = member['PrescriptionDateFormatted']
                        request.AuthStatus = 'Developer Test'
                        request.ReferenceNumber = '0000000'
                        request.Success = True
                        # request.Message = 'Successful'

                else:
                    logger.debug(f'{request.Id} is not eligible, check ID or DOB')
                    print(f'{request.Id} is not eligible, check ID or DOB')
                    request.Message = f'{request.Id} is not eligible, check ID or DOB'
                    process_list.append(request)
                    continue
            except Exception as ex:
                logger.error(f'ERROR. member: {member["MemberId"]}, Exception: {str(ex)}')
                print(f'ERROR. member: {member["MemberId"]}, Exception: {str(ex)}')
                request.Message = f'ERROR. member: {member["MemberId"]}, Exception: {str(ex)}'
                process_list.append(request)
                continue

            # request.AuthStatus = 'Submitted'
            i = i + 1
            process_list.append(request)
            time.sleep(1)

        for lst in process_list:
            pprint(vars(lst))
        # if len(process_list) == 0:
        self.driver.close()
        self.driver.quit()
        return {"success": True, "request_list": process_list}

    def is_element_exist(self, val, timeout=10):
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
        print(f'finding element {element_path}')
        return self.driver.find_element_by_xpath(element_path)

    def remove_null_value(self, value):
        logger.debug(f'remove_null_value {value}')
        if value is not None:
            return True
        return False

    def SubmitAuthRequest(self, memberList, settings):
        logger.info(
            '============================ Start program ==============================')
        try:
            print('MemberId: ' + str(memberList[0]['MemberId']))
            # start processing data
            return self.start_execution(memberList, settings)
        except Exception as ex:
            #raise Exception(ex)
            print(str(ex))
            return {"success": False, "message": str(ex), "request_list": []}