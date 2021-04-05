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
import os


logging.basicConfig(handlers=[RotatingFileHandler(filename='insurance/logs/SystemLog.log', mode='a', maxBytes=512000, backupCount=4)],
                    level='DEBUG',
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m/%d/%Y% I:%M:%S %p')

logger = logging.getLogger('my_logger')

class PHPPendingStatus:
    driver = {}

    def Pending_Status(self, members, settings):
        print('*********Staring PHP Pending Status*********')
        with open('insurance/config.json') as f:
            data = json.load(f)

        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

        chromeOptions.add_argument("--headless")
        chromeOptions.add_argument("--window-size=1680, 1050")
        chromeOptions.add_argument("--disable-dev-shm-usage")
        chromeOptions.add_argument("--no-sandbox")

        self.driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chromeOptions)

        ###Login###
        try:
            self.driver.get("https://provider.partnershiphp.org/UI/Login.aspx")
            username = self.is_element_exist('//*[@id="ctl00_contentUserManagement_txtUserName"]').send_keys(settings.username)
            password = self.get_element_by_path('//*[@id="ctl00_contentUserManagement_txtPassword"]').send_keys(settings.password)
            submitbutton = self.get_element_by_path('//*[@id="ctl00_contentUserManagement_btnLogin_input"]').click()

            raf = self.is_element_exist("//span[contains(text(),'Authorizations')]/..").click()
            e_tar_status = self.is_element_exist("//span[contains(text(),'eTAR Status Checking')]/..").click()
            # raf = self.is_element_exist('//*[@id="pm-dashboard"]/li[5]/a').click()
            # e_tar_status = self.is_element_exist('//*[@id="ContentPlaceHolder1_liTARStatusChecking"]/a').click()
        except:
            print("Error Logging In")
            logger.error("Error Logging In")
            self.driver.close()
            self.driver.quit()

        approvals_list = []
        process_list = []
        i = 0
        for member in members:
            request = PatientNewRequestData()
            request.ReferenceNumber = member.refNumber
            try:
                if i > 0:
                    raf = self.is_element_exist("//span[contains(text(),'Authorizations')]/..").click()
                    e_tar_status = self.is_element_exist("//span[contains(text(),'eTAR Status Checking')]/..").click()
                    # self.is_element_exist('//*[@id="sidebar"]/div/div[1]/ul/li[6]/a').click()
                    # self.is_element_exist('//*[@id="ContentPlaceHolder1_liTARStatusChecking"]/a').click()
                time.sleep(.5)
                outpatient_drop = self.is_element_exist('//*[@id="radPatientType_Arrow"]').click()
                time.sleep(.5)
                outpatient = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_radPatientType_DropDown"]/div/ul/li[3]').click()
                tar_num_box = self.get_element_by_path('//*[@id="ctl00_ContentPlaceHolder1_txtTarNumber"]').send_keys(member.refNumber)
                search_button = self.get_element_by_path('//*[@id="ContentPlaceHolder1_btnSearch"]').click()
                # time.sleep(5)

                status = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_rdGrideCIF_ctl00__0"]/td[3]/span/b').text
                print(status)
                request.AuthStatus = status
            except:
                request.AuthStatus = 'Error Finding Member'
                i = i + 1
                process_list.append(request)
                continue

            if status == 'Approved':
                try:
                    name = self.get_element_by_path(
                        '//*[@id="ctl00_ContentPlaceHolder1_rdGrideCIF_ctl00__0"]/td[4]/span/b[1]').text
                    request.FirstName = name.split(' ')[0]
                    request.LastName = name.split(' ')[-1]
                    print(request.FirstName, request.LastName)

                    start_stop_date = self.get_element_by_path(
                        '//*[@id="ctl00_ContentPlaceHolder1_rdGrideCIF_ctl00__0"]/td[2]/span').text
                    request.DateSubmitted = start_stop_date.split('-')[0].strip()
                    request.ExpirationDate = start_stop_date.split('-')[-1].strip()
                    print(f'Start Date: {request.DateSubmitted}, End Date: {request.ExpirationDate}')

                    status = self.get_element_by_path(
                        '//*[@id="ctl00_ContentPlaceHolder1_rdGrideCIF_ctl00__0"]/td[3]/span/b').text
                    print(status)
                    request.AuthStatus = status

                    view_tar = self.get_element_by_path('//*[@id="ctl00_ContentPlaceHolder1_rdGrideCIF_ctl00__0"]/td[8]/a[1]').click()
                    time.sleep(1)
                except:
                    logger.error('ERROR Getting Patient Status')
                    print('ERROR Getting Patient Status')
                    request.Message = 'ERROR Getting Patient Status'
                    process_list.append(request)
                    i = i + 1
                    continue

                page_anchor = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_rdTarLineGrid_ctl00__0"]/td[3]')
                time.sleep(.5)

                cpt_list = []
                unit_list = []
                try:
                    cpts = self.driver.find_elements_by_xpath('//*[@id="ctl00_ContentPlaceHolder1_rdTarLineGrid_ctl00"]/tbody/tr[*]/td[2]')
                    c = 1
                    for cpt in cpts:
                        cpt_c = cpt.text
                        cpt_list.append(cpt_c)
                        print(cpt_c)
                        c = c + 1
                except:
                    logger.error('ERROR Creating CPT list')
                    print('ERROR Creating CPT list')
                    request.Message = 'ERROR Creating CPT list'
                    process_list.append(request)
                    i = i + 1
                    continue

                try:
                    units = self.driver.find_elements_by_xpath('//*[@id="ctl00_ContentPlaceHolder1_rdTarLineGrid_ctl00"]/tbody/tr[*]/td[10]')
                    u = 1
                    for unit in units:
                        unit_u = unit.text
                        unit_list.append(unit_u)
                        print(unit_u)
                        u = u + 1
                    unit_list_sort = sorted(unit_list[1:], key=int)
                    request.Visits = unit_list_sort[0]

                except:
                    logger.error('ERROR Creating Units list')
                    print('ERROR Creating Units list')
                    request.Message = 'ERROR Creating Units list'
                    process_list.append(request)
                    i = i + 1
                    continue

                try:
                    cpt_unit_list = {cpt_list[i]: unit_list[i] for i in range(len(cpt_list))}
                    cpts_units = str(''.join(['{}({}), '.format(c, u) for c, u in cpt_unit_list.items()]))
                    approved = cpts_units
                    print(approved)
                    request.Approved = approved
                except:
                    logger.error('ERROR Compiling CPT-Units list')
                    print('ERROR Compiling CPT-Units list')
                    request.Message = 'ERROR Compiling CPT-Units list'
                    process_list.append(request)
                    i = i + 1
                    continue

                try:
                    dob = self.get_element_by_path('//*[@id="ContentPlaceHolder1_AuthMemberDisplay_lblDOB"]').text
                    request.DOB = dob
                    dob_array = dob.split('/')
                    request.DOBMonth = dob_array[0]
                    request.DOBDay = dob_array[1]
                    request.DOBYear = dob_array[2].split(' ')[0]
                    print(request.DOBMonth, request.DOBDay, request.DOBYear)

                except:
                    logger.error('ERROR Getting DOB')
                    print('ERROR Getting DOB')
                    request.Message = 'ERROR Getting DOB'
                    process_list.append(request)
                    i = i + 1
                    continue

                request.Insurance = 'PHP'
                approvals_list.append(request)

            # if len(members) > i + 1:
            #     self.is_element_exist('//*[@id="sidebar"]/div/div[1]/ul/li[6]/a').click()
            #     self.is_element_exist('//*[@id="ContentPlaceHolder1_liTARStatusChecking"]/a').click()

            i = i + 1
            process_list.append(request)

        self.driver.close()
        self.driver.quit()

        print('All Members Processed')

        for lst in process_list:
            pprint(vars(lst))
        return {"process_list": process_list, "approvals_list": approvals_list}

    def is_element_exist(self, val, timeout=10):
        try:
            logger.debug(f'finding element {val} with timeout {timeout}')
            print(f'finding element {val} with timeout {timeout}')
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, val)))
            return element
        except:
            print('Unable to find element')

    def get_element_by_path(self, element_path):
        logger.debug(f'finding element: {element_path}')
        print(f'finding element {element_path}')
        return self.driver.find_element_by_xpath(element_path)