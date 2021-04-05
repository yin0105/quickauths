from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from logging.handlers import RotatingFileHandler
import json
from insurance.EligibilityStatus.Prime.PatientNewRequestData import PatientNewRequestData
import os.path
from random import *

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
            with open('insurance/NewRequest/Prime/config.json') as f:
                data = json.load(f)
            user_name = settings.username
            user_password = settings.password
            chromeOptions = webdriver.ChromeOptions()
            prefs = {'download.default_directory': os.getcwd() + f'{self.download_directory}'}

            if data['with_browser'] == '0':
                chromeOptions.add_argument("--headless")
            if data['with_browser'] == '1':
                chromeOptions.add_argument("--start-maximized")    
            chromeOptions.add_experimental_option("prefs", prefs)
            self.driver = webdriver.Chrome('insurance/chromedriver', chrome_options=chromeOptions)

            self.driver.get("https://portal.primecommunitycare.net/ipa/general/index.php")
            # login to system
            username_path = "//input[@id='TaRtxt_username']"
            username = self.is_element_exist(username_path, 5)
            username.send_keys(user_name)
            pw = self.get_element_by_path("//input[@id='TaRpas_password']")
            pw.send_keys(user_password)
            self.get_element_by_path("//input[@type='submit']").click()
            time.sleep(1)

            # handle Popup
            try:
                time.sleep(1)
                self.driver.switch_to.default_content()
                self.driver.frame_switch("TB_iframeContent")
                close_popup = self.frame_switch("//a[@class='close trackAtt']")
                close_popup.click()
            except:
                print('No Popup')
                pass

            #Side Menu to get to eligibility verification page
            self.driver.switch_to.default_content()
            eligibility_button_path = '//*[@id="section_title_26"]'
            eligibility_button = self.is_element_exist(eligibility_button_path, 5)
            eligibility_button.click()

            time.sleep(1)
            member_verification_path = '//*[@id="li_106"]/a'
            member_verification = self.is_element_exist(member_verification_path, 5)
            member_verification.click()
            time.sleep(1)
            self.driver.switch_to.default_content()
            self.frame_switch("viewFrame")
            logger.debug('Done: switching to viewFrame')
            i = 0

            for member in members:
                request = PatientNewRequestData()
                request.MemberId = member.member_ID
                logger.info(f'Processing memberId: {member.member_ID}')
                try:
                    member_id_path = '//*[@id="txtMemberID"]'
                    member_id = self.is_element_exist(member_id_path, 5)
                    member_id.clear()
                    member_id.send_keys(member.member_ID)

                    logger.info('Clicking Verify Button')
                    verify_eligibility = self.driver.find_element_by_xpath('//*[@id="btnSearch"]')
                    verify_eligibility.click()
                    time.sleep(.50)

                    logger.info('Searching for member search result')
                    member_name_search = '//*[@id="grdMembersView"]/tbody/tr[2]/td[3]'
                    member_name = self.is_element_exist(member_name_search, 5)

                    if member_name != None:
                        member_full_name = member_name.text
                        member_name_array = member_full_name.split()
                        if len(member_name_array) >= 3:
                            if len(member_name_array[-1]) <= 1:
                                request.FirstName = member_name_array[-2]
                                request.LastName = member_name_array[0]
                            else:
                                request.FirstName = member_name_array[-1]
                                request.LastName = member_name_array[0]
                        else:
                            request.FirstName = member_name_array[-1]
                            request.LastName = member_name_array[0]

                        print(f'Found Member: {member_full_name}')

                        dob = self.get_element_by_path('//*[@id="grdMembersView"]/tbody/tr[2]/td[5]').text
                        request.DOB = dob
                        print(f'Patient DOB: {dob}')

                        plan = self.driver.find_element_by_xpath('//*[@id="grdMembersView"]/tbody/tr[2]/td[7]').text
                        request.Plan = plan
                        print(f'Plan Name is: {plan}')

                        eligibility_value = self.get_element_by_path('//*[@id="grdMembersView_ctl02_lblHPStatus"]').text
                        request.Eligibility = eligibility_value
                        print(f'Patient is: {eligibility_value}')

                    else:
                        print(f'Error: {member.member_ID}')
                        request.Message = f'Error: {member.member_ID}'
                        logger.debug(f'Unable to find new member {member.member_ID}')
                        continue

                except Exception as ex:
                    logger.error(f'ERROR. member: {member.member_ID}, Exception: {ex}')
                    print(f'ERROR. member: {member.member_ID}, Exception: {ex}')

                i = i + 1
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

    def is_element_exist(self, val, timeout=2):
        try:
            logger.debug(f'finding element {val} with timeout {timeout}')
            print(f'finding element {val} with timeout {timeout}')
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, val)))
            return element
        except:
            print(f'Unable to find element {val}')

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
