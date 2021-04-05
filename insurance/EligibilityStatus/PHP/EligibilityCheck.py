from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from logging.handlers import RotatingFileHandler
import json
from insurance.EligibilityStatus.PHP.PatientSearchData import PatientSearchData
from pprint import pprint
import os



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

###Login###
        self.driver.get("https://provider.partnershiphp.org/UI/Login.aspx")
        username = self.is_element_exist('//*[@id="ctl00_contentUserManagement_txtUserName"]').send_keys(user_name)
        password = self.get_element_by_path('//*[@id="ctl00_contentUserManagement_txtPassword"]').send_keys(user_password)
        submitbutton = self.get_element_by_path('//*[@id="ctl00_contentUserManagement_btnLogin_input"]').click()
        eligibilitybutton = self.is_element_exist("//*[@class='pm-eligibility']/a", 5).click()
        eligibilitybutton2 = self.is_element_exist("//span[contains(text(),'eELIGIBILITY')]/..", 5).click()

        process_list = []
        i = 0
        for member in members:
            try:
                request = PatientSearchData()
                request.MemberId = member.member_ID
                logger.info(f'Processing memberId: {member.member_ID}')
                print(f'Checking eligibility for {member.member_ID}')
                time.sleep(.5)

                if i > 0:
                    try:
                        self.is_element_exist('//*[@id="ContentPlaceHolder1_btnSearchMember"]', 5).click()
                        time.sleep(.5)
                    except:
                        print('Attempt #2 to get to Eligibility Module from except')
                        self.driver.get("https://provider.partnershiphp.org/UI/Login.aspx")
                        username = self.is_element_exist(
                            '//*[@id="ctl00_contentUserManagement_txtUserName"]', 5).send_keys(user_name)
                        password = self.get_element_by_path(
                            '//*[@id="ctl00_contentUserManagement_txtPassword"]').send_keys(user_password)
                        submitbutton = self.get_element_by_path(
                            '//*[@id="ctl00_contentUserManagement_btnLogin_input"]').click()
                        eligibilitybutton = self.is_element_exist("//*[@class='pm-eligibility']/a", 5).click()
                        eligibilitybutton2 = self.is_element_exist("//span[contains(text(),'eELIGIBILITY')]/..", 5).click()

                cin_box = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_ucSearchMember_rdCin"]').send_keys(member.member_ID)
                print('MemberID entered')
                search_member_button = self.is_element_exist('//input[@id="ContentPlaceHolder1_ucSearchMember_btnSearch"]')
                search_member_button.click()
                # time.sleep(1)

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

            # Eligibility Screen #1
                time.sleep(1)
                try:
                    last_name = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_ucSearchMember_rdGridMember_ctl00__0"]/td[3]').text
                    first_name = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_ucSearchMember_rdGridMember_ctl00__0"]/td[4]').text
                    dob = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_ucSearchMember_rdGridMember_ctl00__0"]/td[6]').text
                    print(f'Member Found: {first_name} {last_name}')
                    logger.debug(f'Member Found: {first_name} {last_name}')
                    request.LastName = last_name
                    request.FirstName = first_name

                    select_button = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_ucSearchMember_rdGridMember_ctl00_ctl04_lnkAction"]').click()
                    # time.sleep(4)

                    page_anchor = self.is_element_exist('//*[@id="content"]/div[2]/div[1]/div[1]/div[3]/div/div[1]/div/h3')
                    time.sleep(.5)

                # Eligibility Screen #2
                    eligibility = self.is_element_exist('//*[@id="ContentPlaceHolder1_ucSearchMember_lblMbrEligible"]').text
                    if eligibility == 'Yes':
                        request.Eligibility = 'Eligible'
                    else:
                        request.Eligibility = 'Not Eligible'
                    print(f'Eligibility: {eligibility}')
                    logger.info(f'Eligibility: {eligibility}')
                    thru_date = self.is_element_exist('//*[@id="ctl00_ContentPlaceHolder1_ucSearchMember_rdGridEligibilitySpan_ctl00__0"]/td[3]').text
                    print(thru_date)
                    logger.info(f'Thru Date: {thru_date}')
                    request.ThruDate = thru_date
                    request.Status = 'Success'

                    other_insurance = self.driver.find_element_by_xpath('//*[@id="ctl00_ContentPlaceHolder1_ucSearchMember_rdGridEligibilitySpan_ctl00__0"]/td[13]').text
                    print(other_insurance)
                    request.OtherIns = other_insurance

                except:
                    logger.error(f'ERROR. member: {member.member_ID} Not Found, Exception: {ex}')
                    print(f'ERROR: {ex}')
                    request.Eligibility = 'Eligibility check Error'
                    process_list.append(request)
                    i = i + 1
                    continue

            except Exception as ex:
                logger.error(f'ERROR. member: {member.member_ID}, Exception: {ex}')
                print(f'ERROR: {ex}')
                request.Eligibility = 'Error Member ID'
                process_list.append(request)
                i = i + 1
                continue

            i = i + 1
            process_list.append(request)

        self.driver.close()
        self.driver.quit()
        print('All Members Processed')

        for lst in process_list:
            pprint(vars(lst))
        
        return process_list

    def is_element_exist(self, val, timeout=10):
        try:
            logger.debug(f'Finding element {val} with timeout {timeout}')
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