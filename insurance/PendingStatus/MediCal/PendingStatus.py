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
import os

logging.basicConfig(handlers=[RotatingFileHandler(filename='insurance/logs/SystemLog.log', mode='a', maxBytes=512000, backupCount=4)],
                    level='DEBUG',
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m/%d/%Y% I:%M:%S %p')

logger = logging.getLogger('my_logger')

class MediCalPendingStatus:
    driver = {}

    def Pending_Status(self, members, settings):
        print('*********Staring MediCal Pending Status*********')
        with open('insurance/config.json') as f:
            data = json.load(f)

        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

        chromeOptions.add_argument("--headless")
        chromeOptions.add_argument("--window-size=1680, 1050")
        chromeOptions.add_argument("--disable-dev-shm-usage")
        chromeOptions.add_argument("--no-sandbox")

        self.driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chromeOptions)

        self.driver.get("https://www.medi-cal.ca.gov/MCWebPub/Login.aspx?ReturnUrl=%2fCommon%2fMenu.aspx")

        # Logging in
        self.is_element_exist('//*[@id="MainContent_txtUserID"]').send_keys(settings.username)
        self.get_element_by_path('//*[@id="MainContent_txtPassword"]').send_keys(settings.password)
        self.get_element_by_path('//*[@id="MainContent_btnSubmit"]').click()
        self.get_element_by_path("//span[contains(text(),'eTAR')]").click()
        self.is_element_exist("//a[contains(text(),'Inquire Only')]").click()
        self.is_element_exist("//a[contains(text(),'Inquire on a TAR')]").click()

        approvals_list = []
        process_list = []
        i = 0
        for member in members:
            request = PatientNewRequestData()
            request.ReferenceNumber = member.refNumber
            logger.info(f'Processing eTar: {member.refNumber}')
            print(f'Processing eTar: {member.refNumber}')

            try:
                try:
                    self.is_element_exist("//a[contains(text(),'TAR Inquiry')]").click()
                except:
                    pass
                time.sleep(.5)
                self.is_element_exist("//input[@name='TarNum']").send_keys(member.refNumber.strip())
                print(f'refNumber entered:{member.refNumber}')
                self.get_element_by_path('//*[@id="middle_column"]/table[2]/tbody/tr[3]/td/center/table/tbody/tr/td/input').click()

                time.sleep(.5)
                alert = self.driver.switch_to.alert
                time.sleep(.5)
                alert.accept()

                rec_id = self.is_element_exist("//tr[2]/td[4]/span").text
                request.Id = rec_id
                print(rec_id)

                lastname = self.get_element_by_path("//tr[2]/td[10]/span").text
                request.LastName = lastname
                print(lastname)

                # datesubmitted = get_element_by_path("//tr[2]/td[11]/span")
                # request.DateSubmitted = datetime.datetime.strptime(str(datesubmitted), '%m%d%Y').strftime('%m/%d/%Y')
                # print(datesubmitted)

                try:
                    status_list = []
                    statuses = self.driver.find_elements_by_xpath(f"//span[contains(text(),'Status')]/../../../tr")
                    val = 2
                    for s in statuses:
                        try:
                            status = s.find_element_by_xpath(f'../tr[{val}]/td[12]/span[1]').text
                            print(status)
                            status_list.append(status)
                            val = val + 1
                        except:
                            pass
                    status_list_str = '/'.join([str(elem) for elem in status_list])
                    print(status_list_str)
                    request.AuthStatus = status_list_str

                    cpt_list = []
                    unit_list = []
                    if status_list[0] == "Approved" or status_list[1] == "Approved" or status_list[2] == "Approved":
                        print('Checking Approved CPTs')
                        etar_number = self.get_element_by_path(f"//a[contains(text(),'{member.refNumber}')]")
                        etar_number.click()
                        first_name = self.get_element_by_path("//td[contains(text(),'First Name')]/../../tr[2]/td[2]").text
                        cpts = self.driver.find_elements_by_xpath("//a[contains(text(),'Service Code')]")
                        i = 1
                        for cpt in cpts:
                            cpt_i = cpt.find_element_by_xpath("../../../tr[2]/td[2]").text
                            cpt_list.append(cpt_i)
                            i = i + 1

                        units = self.driver.find_elements_by_xpath("//td[contains(text(),'Total Units')]")
                        i = 1
                        for unit in units:
                            unit_i = unit.find_element_by_xpath("../../tr[2]/td[1]").text
                            unit_list.append(unit_i)
                            i = i + 1

                        print(cpt_list)
                        print(unit_list)

                        unit_list_sort = sorted(unit_list[1:], key=int)
                        request.Visits = unit_list_sort[0]
                        print(f'Visits= {request.Visits}')

                        cpt_unit_list = {cpt_list[i]: unit_list[i] for i in range(len(cpt_list))}
                        cpts_units = str(''.join(['{}({}), '.format(c, u) for c, u in cpt_unit_list.items()]))
                        # cpts_units = str(cpts_units)
                        approved = cpts_units
                        print(approved)

                        dob = self.get_element_by_path("//td[contains(text(),'Date of Birth')]/../../tr[2]/td[2]").text
                        dob = datetime.datetime.strptime(str(dob), '%m%d%Y').strftime('%m/%d/%Y')

                        request.DOB = dob
                        request.DOBMonth = dob[0:2]
                        request.DOBDay = dob[3:5]
                        request.DOBYear = dob[6:10]

                        from_date = self.get_element_by_path("//td[contains(text(),'From Date')]/../../tr[4]/td[1]").text
                        from_date = datetime.datetime.strptime(str(from_date), '%m%d%Y').strftime('%m/%d/%Y')

                        thru_date = self.get_element_by_path("//td[contains(text(),'Thru Date')]/../../tr[4]/td[2]").text
                        thru_date = datetime.datetime.strptime(str(thru_date), '%m%d%Y').strftime('%m/%d/%Y')
                        print(f'Authorization Dates: {from_date}-{thru_date}')

                        # request.CPTs = cpt_list
                        # request.Units = unit_list
                        request.Approved = approved
                        request.FirstName = first_name
                        request.DateSubmitted = from_date
                        request.ExpirationDate = thru_date
                        request.Insurance = 'Medi-Cal'

                        approvals_list.append(request)
                except:
                    logger.error(f'ERROR. Unable to find auth status: {member.member_ID}')
                    print(f'ERROR. Unable to find auth status: {member.member_ID}')
                    request.Message = f'ERROR. Unable to find auth status: {member.member_ID}'
                    request.AuthStatus = 'Error'
                    process_list.append(request)
                    continue

                # inquire_only = get_element_by_path("//a[contains(text(),'TAR Inquiry')]").click()

            except Exception as ex:
                logger.error(f'ERROR. Unable to find eTar: {member.refNumber}, {ex}')
                print(f'ERROR. Unable to find eTar: {member.refNumber}, {ex}')
                request.Message = f'ERROR. Unable to find eTar: {member.refNumber}'
                process_list.append(request)
                continue

            i = i + 1
            process_list.append(request)

        self.driver.close()
        self.driver.quit()

        print('All Members Processed')

        for lst in process_list:
            pprint(vars(lst))
        return {"process_list": process_list, "approvals_list": approvals_list}

    def is_element_exist(self, val, timeout=5):
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