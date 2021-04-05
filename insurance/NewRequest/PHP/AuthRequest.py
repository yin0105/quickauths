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
from selenium.webdriver.common.keys import Keys
import os



logging.basicConfig(handlers=[RotatingFileHandler(filename='insurance/logs/SystemLog.log', mode='a', maxBytes=512000, backupCount=4)],
                    level='DEBUG',
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m/%d/%Y% I:%M:%S %p')

logger = logging.getLogger('my_logger')

class AuthRequest:
    driver = {}

    def start_execution(self, members, settings):
        with open('insurance/config.json') as f:
            data = json.load(f)
        print(data)
        logger.info(data)

        submitted_by_dev = data['submitted_by_dev']
        user_name = settings.username
        user_password = settings.password

        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

        chromeOptions.add_argument("--headless")
        chromeOptions.add_argument("--window-size=1680, 1050")
        chromeOptions.add_argument("--disable-dev-shm-usage")
        chromeOptions.add_argument("--no-sandbox")

        self.driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chromeOptions)
        # self.driver = webdriver.Chrome(executable_path="insurance/chromedriver", chrome_options=chromeOptions)


        ###Login###
        try:
            self.driver.get("https://provider.partnershiphp.org/UI/Login.aspx")
            username = self.get_element_by_path('//*[@id="ctl00_contentUserManagement_txtUserName"]').send_keys(user_name)
            password = self.get_element_by_path('//*[@id="ctl00_contentUserManagement_txtPassword"]').send_keys(user_password)
            submitbutton = self.get_element_by_path('//*[@id="ctl00_contentUserManagement_btnLogin_input"]').click()
        except:
            print("Error Logging In")
            logger.error("Error Logging In")
            self.driver.close()
            self.driver.quit()

        # auth_button = self.is_element_exist('//*[@id="pm-dashboard"]/li[5]/a', 5).click()
        # tar_entry_button = self.is_element_exist('//*[@id="ContentPlaceHolder1_liTAREntry"]/a', 5).click()
        auth_button = self.is_element_exist("//span[contains(text(),'Authorizations')]/..", 5).click()
        tar_entry_button = self.is_element_exist("//span[contains(text(),'TAR Entry')]/..", 5).click()

        process_list = []
        i = 1
        for member in members:
            # Check Eligibility
            request = PatientNewRequestData()
            request.Id = member['MemberId']
            request.DateSubmitted = member['StartDateFormatted']
            logger.info('Processing member:', member['MemberId'])
            try:
                if i > 1:
                    try:
                        new_auth_button = self.is_element_exist("//span[contains(text(),'Authorizations')]/..", 5).click()
                        tar_entry = self.is_element_exist("//span[contains(text(),'TAR Entry')]/..").click()
                        time.sleep(.5)
                    except:
                        print('Error getting to New Auth, will log back in')
                        self.driver.get("https://provider.partnershiphp.org/UI/Login.aspx")
                        username = self.is_element_exist(
                            '//*[@id="ctl00_contentUserManagement_txtUserName"]').send_keys(user_name)
                        password = self.get_element_by_path(
                            '//*[@id="ctl00_contentUserManagement_txtPassword"]').send_keys(user_password)
                        submitbutton = self.get_element_by_path(
                            '//*[@id="ctl00_contentUserManagement_btnLogin_input"]').click()
                        auth_button = self.is_element_exist("//span[contains(text(),'Authorizations')]/..", 5).click()
                        tar_entry_button = self.is_element_exist("//span[contains(text(),'TAR Entry')]/..", 5).click()
                        # auth_button = self.is_element_exist('//*[@id="pm-dashboard"]/li[5]/a', 5).click()
                        # tar_entry_button = self.is_element_exist('//*[@id="ContentPlaceHolder1_liTAREntry"]/a',
                        #                                          5).click()

                self.driver.switch_to.default_content()
                cin_box = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_ucSearchMember_rdCin"]', 5).send_keys(
                    member['MemberId'])
                print('MemberID entered', member['MemberId'])
                logger.debug('MemberID entered', member['MemberId'])
                search_member_button = self.is_element_exist('//input[@id="ContentPlaceHolder1_ucSearchMember_btnSearch"]',
                                                             5).click()
                try:
                    popup = self.get_element_by_path("//div[contains(text(),'Invalid Member')]")
                    if popup:
                        self.is_element_exist("//div[contains(text(),'Invalid Member')]/../div[2]/a/span/span", 2).click()
                        logger.error(f'PopUP Alert ERROR. member: {member.member_ID}')
                        request.Eligibility = 'Error finding Member ID'
                        process_list.append(request)
                        i = i + 1
                        continue
                except:
                    pass
            except:
                logger.error('ERROR Entering Member ID and Searching')
                print('ERROR Entering Member ID and Searching')
                request.Message = 'ERROR Entering Member ID and Searching'
                process_list.append(request)
                request.Success = False
                i = i + 1
                continue
            try:
                search_anchor = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_ucSearchMember_rdGridMember_ctl00_ctl04_lnkAction"]', 10)
                time.sleep(.5)

                last_name = self.is_element_exist(
                    '//*[@id="ctl00_ContentPlaceHolder1_ucSearchMember_rdGridMember_ctl00__0"]/td[3]', 5).text
                first_name = self.is_element_exist(
                    '//*[@id="ctl00_ContentPlaceHolder1_ucSearchMember_rdGridMember_ctl00__0"]/td[4]', 5).text
                print(f'Member Found: {first_name} {last_name}')
                logger.debug(f'Member Found: {first_name} {last_name}')
                dob = self.is_element_exist(
                    '//*[@id="ctl00_ContentPlaceHolder1_ucSearchMember_rdGridMember_ctl00__0"]/td[6]', 5).text
                print(f'Member DOB: {dob}')
                logger.debug(f'Member DOB: {dob}')

                request.LastName = last_name
                request.FirstName = first_name

                select_button = self.is_element_exist(
                    '//*[@id="ctl00_ContentPlaceHolder1_ucSearchMember_rdGridMember_ctl00_ctl04_lnkAction"]', 5).click()
                # time.sleep(4)
            except:
                logger.error('ERROR Finding Member')
                print('ERROR Finding Member')
                request.Message = 'ERROR Finding Member, Check MemberID'
                process_list.append(request)
                request.Success = False
                i = i + 1
                continue

                ### Eligibility Screen #2
            page_anchor = self.is_element_exist('//*[@id="content"]/div[2]/div[1]/div[1]/div[1]/div/div[1]/div/h3', 5)
            time.sleep(.5)
            try:
                print('Checking Eligbility')
                eligibility = self.is_element_exist('//*[@id="ContentPlaceHolder1_ucSearchMember_lblMbrEligible"]').text
                if eligibility == 'Yes':
                    request.Eligibility = 'Eligible'
                    print('Member is Eligibile')
                else:
                    request.Eligibility = 'Not Eligible'
                    print('Member is Ineligible')

                print('Enter New eTar Button')
                enter_new_etar = self.is_element_exist('//*[@id="ContentPlaceHolder1_ucSearchMember_btnETAREntry"]',
                                                       5).click()
                try:
                    print('Clearing End Date')
                    end_date = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_radEndDate_dateInput"]').clear()
                except:
                    pass
                end_date = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_radEndDate_dateInput"]').send_keys(member['EndDateFormatted'])
                print('End Date Entered')

                tar_type = self.is_element_exist('//*[@id="ContentPlaceHolder1_ddlTARTypes"]/option[2]').click()
                print('TAR type Selected')

                select_provider_drop = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_providerSearch_ProviderProfileDropdown_Arrow"]').click()
                print('Selecting Provider')
                time.sleep(1)
                select_provider = self.is_element_exist(
                    '//*[@id="ctl00_ContentPlaceHolder1_providerSearch_ProviderProfileDropdown_DropDown"]/div/ul/li[1]',
                    5).click()
                print('Selected Provider from Dropdown')
                time.sleep(.5)
                self.driver.execute_script("window.scrollTo(0, 500)")
                print('Scroll Down Executed')
                current_location = self.is_element_exist('//*[@id="ContentPlaceHolder1_ddlPatientCurrentLocation"]/option[2]').click()
                print('Location Selected')

                print(f"Urgency = {member['Urgent']}")
                if member['Urgent'] == 'U':
                    self.is_element_exist('//*[@id="ContentPlaceHolder1_ddlIsUrgent"]/option[1]').click()
                    self.is_element_exist('//*[@id="ContentPlaceHolder1_txtReasonUrgentTARlength"]').send_keys('See Below in Medical Justification')
                print('Updated Urgent Box')

                #Adding Diagnosis
                try:
                    diagnose_items = [n for n in member['ICDs'] if n is not None]
                    print('Adding Diagnosis')
                    logger.info('Adding Diagnosis')
                    request.ICD10 = diagnose_items
                    icd = 'primary'
                    for diag in diagnose_items:
                        diagnosis = self.driver.find_element_by_id(f'ctl00_ContentPlaceHolder1_{icd}_diagSearch_diagnosisDropdown_Input')
                        print("ICD10:", diag)
                        diagnosis.send_keys(diag)
                        if icd == 'primary':
                            time.sleep(5)
                        else:
                            time.sleep(1)
                        self.is_element_exist(f'//*[@id="ctl00_ContentPlaceHolder1_{icd}_diagSearch_diagnosisDropdown_DropDown"]/div[2]/ul/li/table/tbody/tr', 5).click()
                        time.sleep(1)
                        if len(diagnose_items) > 1:
                            icd = 'secondary'
                    print('ICD10s Added')
                except:
                    logger.error('ERROR Adding Diagnosis')
                    print('ERROR Adding Diagnosis')
                    request.Message = 'ERROR Adding Diagnosis, Check ICD Codes'
                    process_list.append(request)
                    request.Success = False
                    i = i + 1
                    continue

                self.driver.execute_script("window.scrollTo(0, 800)")
                print('Scrolled Down')
                time.sleep(.5)

                #Adding Services
                try:
                    service_items = [
                        n for n in member['CPTs'] if n['type'] is not None]
                    print('Adding services')
                    logger.info('Adding services')
                    for service in service_items:
                        service_items_element = self.is_element_exist(
                            '//*[@id="ctl00_ContentPlaceHolder1_rdAlert_ctl00_ctl03_ctl01_btnAddServiceCode"]').click()
                        print(f"service: {service['type']} - {service['value']}")
                        logger.info(f"service: {service['type']} - {service['value']}")
                        service_data_element = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_rdAlert_ctl00_ctl03_ctl01_userProcedureSearch_procedureDropdown_Input"]').send_keys(service['type'])
                        time.sleep(1)
                        service_data_search = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_rdAlert_ctl00_ctl03_ctl01_userProcedureSearch_procedureDropdown_DropDown"]/div[2]/ul/li[1]/table/tbody/tr', 5).click()
                        time.sleep(1)
                        units = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_rdAlert_ctl00_ctl03_ctl01_txtUnits"]').send_keys(service['value'])
                        quantity = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_rdAlert_ctl00_ctl03_ctl01_txtQuantity"]').send_keys(service['value'])
                        add_new_service_button = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_rdAlert_ctl00_ctl03_ctl01_ctl00"]/div[2]/div/div/div/div[2]/div/div[2]/button[1]').click()
                        print(f"Total {service['type']} units =", service['value'])
                except:
                    logger.error('ERROR Adding Service Items')
                    print('ERROR Adding Service Items')
                    request.Message = 'ERROR Adding Service Items, Check CPTs'
                    process_list.append(request)
                    request.Success = False
                    i = i + 1
                    continue

                medical_justification = self.is_element_exist('//*[@id="ContentPlaceHolder1_txtAdditionalNoteslength"]').send_keys(member['Message'])
                print('Entered medical_justification')
                time.sleep(.5)

                html = self.driver.find_element_by_tag_name('html')
                html.send_keys(Keys.PAGE_UP)
                print('Scrolled to Top of Page')

                #Upload File
                try:
                    filesArray = member['FilePath'].split(",")
                    files = [n for n in filesArray if n is not None and n != '']
                    print(f'Got files variable: {len(files)}')
                    if len(files) > 0:
                        print('len of files is > 0')
                        time.sleep(2)
                        attachment_button = self.is_element_exist('//*[@id="btnAttachment"]').click()
                        print('Attachment Button Clicked')
                        time.sleep(1)
                        self.frame_switch('mfp-iframe')
                        for file in files:
                            logger.info(f'Adding file: {file} for member: {member["MemberId"]}')
                            print(f'Adding file: {file} for member: {member["MemberId"]}')
                            choose_file = self.is_element_exist('//*[@id="attachment_FUAttachment"]')
                            if choose_file is None:
                                request.Message = request.Message + f'Unable to add the document: {file}'
                                logger.error(f'Failed to add file: {file} to member: {member["MemberId"]}')
                                continue
                            choose_file.send_keys(file)
                            upload_file = self.get_element_by_path('//*[@id="attachment_btnUpload"]').click()
                            logger.info('upload file buttone clicked')
                            time.sleep(.5)
                        close_upload_file = self.get_element_by_path('//*[@id="form1"]/button').click()
                        print('Files Attached')
                    else:
                        print(f'Zero files for member: {member["MemberId"]}')
                        logger.info(f'Zero files for member: {member["MemberId"]}')

                except:
                    logger.error(f'Error uploading file fo member: {member["MemberId"]}')
                    print(f'Error uploading file fo member: {member["MemberId"]}')
                    request.Message = 'Error uploading file fo member'
                    process_list.append(request)
                    request.Success = False
                    i = i + 1
                    continue

                print('PRE_SUBMIT: Member Authorization Details Entered in portal')

                #Submit Authorization
                time.sleep(.5)
                if submitted_by_dev == '0':
                    try:
                        self.is_element_exist('//*[@id="content"]/div[3]/div[2]/div/div/div[3]/div/button').click()
                        print('Submit Button Clicked')
                    except:
                        logger.error(f'Error Clicking Submit Button: {member["MemberId"]}')
                        print(f'Error Clicking Submit Button: {member["MemberId"]}')
                        request.Message = 'Error Clicking Submit Button'
                        process_list.append(request)
                        request.Success = False
                        i = i + 1
                        continue

                    dob_array = dob.split("/")
                    request.DOB = dob
                    request.DOBMonth = dob_array[0]
                    request.DOBDay = dob_array[1]
                    request.DOBYear = dob_array[2]
                    request.Frequency = member['Freq']
                    request.VisitsPer = member['VisitsPer']
                    request.PerWeeks = member['PerWeeks']
                    request.Insurance = 'Medi-Cal'
                    request.Visits = (int(member['VisitsPer']) * int(member['PerWeeks']))
                    request.Case = member['Case']
                    request.AuthStatus = 'Submitted'

                    #Getting Reference Number
                    try:
                        time.sleep(.5)
                        print('Getting Reference Number')
                        refNumber = self.is_element_exist('//*[@id="ContentPlaceHolder1_spanTARID"]').text
                        print(f' Reference Number Acquired: {refNumber}')
                        request.ReferenceNumber = refNumber
                    except:
                        logger.error(f'Error Getting Reference Number: {member["MemberId"]}')
                        print(f'Error Clicking Getting Reference Number: {member["MemberId"]}')
                        request.Message = 'Error Getting Reference Number After Submission'
                        process_list.append(request)
                        request.Success = True
                        i = i + 1
                        continue

                self.driver.switch_to.default_content()
                if submitted_by_dev == '1':
                    dob_array = dob.split("/")
                    request.DOB = dob
                    request.DOBMonth = dob_array[0]
                    request.DOBDay = dob_array[1]
                    request.DOBYear = dob_array[2]
                    request.Frequency = member['Freq']
                    request.VisitsPer = member['VisitsPer']
                    request.PerWeeks = member['PerWeeks']
                    request.Insurance = 'Medi-Cal'
                    request.Visits = (int(member['VisitsPer']) * int(member['PerWeeks']))
                    request.Case = member['Case']
                    request.AuthStatus = 'Developer Test'
                    request.ReferenceNumber = '000000000'
                    request.Success = True

            except Exception as ex:
                logger.error(f'ERROR. member: {member["MemberId"]}, Exception: {str(ex)}')
                print(f'ERROR. member: {member["MemberId"]}, Exception: {str(ex)}')
                request.Message = f'ERROR. member: {member["MemberId"]}, Exception: {str(ex)}'
                process_list.append(request)
                request.Success = False
                i = i + 1
                continue

            i = i + 1
            process_list.append(request)
            time.sleep(.5)

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

    def frame_switch(self, val, timeout=5):
        try:
            frame = WebDriverWait(self.driver, timeout).until(EC.frame_to_be_available_and_switch_to_it((By.CLASS_NAME, val)))
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
            self.driver.quit()
            print(str(ex))
            self.driver.quit()

            return {"success": False, "message": str(ex), "request_list": []}
