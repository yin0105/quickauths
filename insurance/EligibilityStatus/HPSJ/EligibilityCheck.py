from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, logging, json, os
from logging.handlers import RotatingFileHandler
from random import *
from insurance.EligibilityStatus.HPSJ.PatientSearchData import PatientSearchData

logging.basicConfig(handlers=[RotatingFileHandler(filename='insurance/logs/SystemLog.log', mode='a', maxBytes=512000, backupCount=4)],
                    level='DEBUG',
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m/%d/%Y%I:%M:%S %p')

logger = logging.getLogger('my_logger')

search_patient_path = '//*[@id="Form1"]/div[4]/div[2]/a[4]'
member_id_path = '//*[@id="txtMemberID"]'
search_member_path = '//*[@id="btnSearch"]'
member_name_path = '//*[@id="tblMain"]/tbody/tr[3]/td[2]/a'
eligibility_value_path = '//*[@id="tblMain"]/tbody/tr[3]/td[10]'
status_element_path = '//*[@id="gvEligHistoryStatus"]/tbody/tr[2]/td[5]'
tru_element_path = '//*[@id="gvEligHistoryStatus"]/tbody/tr[2]/td[2]'


class EligibilityCheck:
    download_directory = '\\data\\'
    input_file_path = 'HPSJ AUTH Project.xlsx'
    user_name = ''
    user_password = ''
    driver = {}
    # with_browser = "1"

    def start_execution(self, members, settings):
        process_list = []
        try:
            with open('insurance/NewRequest/HSPJ/config.json') as f:
                data = json.load(f)
            user_name = settings[0].username
            user_password = settings[0].password
            chromeOptions = webdriver.ChromeOptions()
            prefs = {'download.default_directory': os.getcwd() + f'{self.download_directory}'}

            if data['with_browser'] == '0':
                chromeOptions.add_argument("--headless")
            if data['with_browser'] == '1':
                chromeOptions.add_argument("--start-maximized")    
            chromeOptions.add_experimental_option("prefs", prefs)
            self.driver = webdriver.Chrome('insurance/chromedriver', chrome_options=chromeOptions)

            self.driver.get("https://provider.hpsj.com/dre/default.aspx")
            # login to system
            username = self.driver.find_element_by_xpath(
                '//*[@id="txtUserName"]')
            username.send_keys(user_name)
            password = self.driver.find_element_by_xpath(
                '//*[@id="txtPassword"]')
            password.send_keys(user_password)
            login_button = self.driver.find_element_by_xpath(
                '//*[@id="btnLogin"]')
            login_button.click()
            time.sleep(1)

            self.driver.switch_to.default_content()
            self.driver.switch_to.frame("left")

            search_patient = self.is_element_exist(search_patient_path, 5)
            if search_patient is None:
                logger.error('Unable to find search patient link')
                self.driver.close()
                self.driver.quit()
                return process_list

            search_patient.click()
            time.sleep(1)

            for member in members:
                memberId = member.member_ID
                request = PatientSearchData()
                request.MemberId = memberId
                logger.info(f"Processing memberId: {memberId}")

                self.driver.switch_to.default_content()
                self.driver.switch_to.frame("work")
                self.driver.switch_to.frame("criteria")

                member_id = self.is_element_exist(member_id_path, 2)
                member_id.clear()
                member_id.send_keys(str(memberId))

                search_member = self.is_element_exist(search_member_path)
                search_member.click()

                self.driver.switch_to.default_content()
                self.driver.switch_to.frame("work")
                self.driver.switch_to.frame("results")

                member_name = self.is_element_exist(member_name_path, 2)
                if member_name is None:
                    request.Message = 'Unable to find member details. Please check the member Id'
                    logger.error(
                        'Unable to find new member details. Please check the member Id')
                    process_list.append(request)
                    continue

                eligibility_value = self.is_element_exist(
                    eligibility_value_path)
                if eligibility_value is not None:
                    request.Eligibility = eligibility_value.text

                member_full_name = member_name.text
                member_name_array = member_full_name.split(',')
                if len(member_name_array) == 2:
                    request.FirstName = member_name_array[0]
                    request.LastName = member_name_array[1]
                if len(member_name_array) == 1:
                    request.FirstName = member_name_array[0]

                member_name.click()

                status_element = self.is_element_exist(status_element_path, 2)
                if status_element is not None:
                    request.Status = status_element.text

                tru_element = self.is_element_exist(tru_element_path)
                if tru_element is not None:
                    request.ThruValue = tru_element.text
                process_list.append(request)

            self.driver.close()
            self.driver.quit()
            return process_list
        except Exception as ex:
            print(ex)
            logger.error(ex)
            self.driver.close()
            self.driver.quit()
            return process_list

    def get_element_by_path(self, element_path):
        logger.debug(f'finding element: {element_path}')
        return self.driver.find_element_by_xpath(element_path)

    def is_element_exist(self, val, timeout=2):
        try:
            logger.debug(f'Finding element {val} with timeout {timeout}')
            print(f'finding element {val} with timeout {timeout}')
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, val)))
            return element
        except Exception as ex:
            logger.debug(str(ex))
            logger.debug(f'Unable to find {val}..')
            print(f'Unable to find {val}..')
            return None

    def SubmitRequest(self, memberList, settings):
        logger.info(
            '============================ Start program ==============================')
        try:
            for member in memberList:
                print('MemberId: ' + str(member.member_ID))
            # start processing data
            return self.start_execution(memberList, settings)
        except Exception as ex:
            raise Exception(ex)
