from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
import time
import logging
from logging.handlers import RotatingFileHandler
import json
from insurance.NewRequest.Prime.PatientNewRequestData import PatientNewRequestData
import datetime
from pprint import pprint
import os.path
from random import *

logging.basicConfig(handlers=[RotatingFileHandler(filename='insurance/logs/SystemLog.log', mode='a', maxBytes=512000, backupCount=4)],
                    level='DEBUG',
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m/%d/%Y%I:%M:%S %p')

logger = logging.getLogger('my_logger')

# List of XPATHs
member_id_path = "//input[@name='txtMemberId']"
member_name_path = '//*[@id="lblMemberNameVal"]'

priority_button_path = '//*[@id="ddlPriority"]'
priority = '//*[@id="ddlPriority"]/option[{}]'

same_as_provider_path = '//*[@id="chbSameAsReqProv"]'
comment = '//*[@id="txtNotes"]'
upload_doc_button = '//*[@id="atab2"]'

class AuthRequest:
    download_directory = '\\data\\'
    input_file_path = 'PrimeCCCV.xlsx'
    user_name = ''
    user_password = ''
    submitted_by_dev = '0'
    driver = {}

    def start_execution(self, memberList, settings):

        try:
            print(pprint(settings))
            with open('insurance/NewRequest/Prime/config.json') as f:
                data = json.load(f)
            print(data)
            logger.info(data)

            self.download_directory = data['download_directory']
            user_name = settings.username  # data['user_name']
            user_password = settings.password  # data['user_password']
            submitted_by_dev = data['submitted_by_dev']
            chromeOptions = webdriver.ChromeOptions()
            prefs = {'download.default_directory': f'{self.download_directory}'}

            if data['with_browser'] == '0':
                chromeOptions.add_argument("--headless")
            if data['with_browser'] == '1':
                chromeOptions.add_argument("--start-maximized")
            chromeOptions.add_experimental_option("prefs", prefs)

            try:
                self.driver = webdriver.Chrome('insurance/chromedriver',chrome_options=chromeOptions)
            except Exception as ex:
                print(ex)
                response = {"success": False,
                            "message": "Unable to open web self.driver", "request_list": []}
                return response

            members = memberList

            self.driver.get("https://portal.primecommunitycare.net/ipa/general/index.php")
            username = self.get_element_by_path("//input[@id='TaRtxt_username']")
            username.send_keys(user_name)
            pw = self.get_element_by_path("//input[@id='TaRpas_password']")
            pw.send_keys(user_password)
            submit = self.get_element_by_path("//input[@type='submit']")
            submit.click()

            time.sleep(1)
            try:
                time.sleep(1)
                self.driver.switch_to.default_content()
                self.frame_switch('TB_iframeContent')
                close_popup = self.get_element_by_path("//a[@class='close trackAtt']")
                close_popup.click()
            except:
                print('No Popup')
                pass
            self.driver.switch_to.default_content()
            time.sleep(1)
            self.get_element_by_path("//h3[@id='section_title_23']").click()
        except Exception as ex:
            print(ex)
            response = {"success": False,
                        "message": str(ex), "request_list": []}
            self.self.driver.close()
            self.self.driver.quit()
            return response

        process_list = []
        i = 0
        for member in members:
            request = PatientNewRequestData()
            request.Id = member['id']
            request.MemberId = member['MemberId']
            request.DateSubmitted = datetime.date.today().strftime('%m/%d/%Y')
            logger.info(f'Processing memberId: {member["MemberId"]}')
            print(f'Processing memberId: {member["MemberId"]}')
            try:
                self.driver.switch_to.default_content()
                self.get_element_by_path("//a[contains(text(),'Auth/Referral Submission')]").click()
                time.sleep(1)
                self.driver.switch_to.default_content()
                self.frame_switch('viewFrame')

                time.sleep(1)
                member_id = self.is_element_exist(member_id_path)
                if member_id is None:
                    request.Message = 'Unable to find new member details screen'
                    logger.error('Unable to find new member details screen')
                    process_list.append(request)
                    self.driver.close()
                    self.driver.quit()
                    return {"request_list": process_list}
                print(member)
                member_id.send_keys(member["MemberId"], Keys.ENTER)

                member_name = self.is_element_exist(member_name_path, 1)
                time.sleep(1)
                if member_name is None:
                    request.Message = 'Unable to find new member details. Please check the member Id'
                    print('Unable to find new member details. Please check the member Id')
                    process_list.append(request)
                    return

                member_full_name = member_name.text
                print(f'Found member name: {member_full_name}')
                logger.debug(f'Found member name: {member_full_name}')
                member_name_array = member_full_name.split()
                if len(member_name_array) >= 3:
                    if len(member_name_array[-1]) <= 1:
                        request.FirstName = member_name_array[-2]
                        request.LastName = member_name_array[0]
                    else:
                        request.FirstName = member_name_array[-1]
                        request.LastName = member_name_array[0]

                member_dob_path = '//*[@id="lblDOBVal"]'
                member_dob = self.is_element_exist(member_dob_path, 1)
                request.DOB = member_dob.text

                #Priority 'S', 'U', 'R'
                time.sleep(1)
                priority_arrow_element = self.get_element_by_path(priority_button_path)
                priority_arrow_element.click
                # time.sleep(1)
                priority_id = 1 #Routine/Standard = "S"
                # if member['urgent'].upper() == 'U':
                #     priority_id = 2
                # if member['urgent'].upper() == 'R':
                #     priority_id = 3
                priority_controller = priority.format(str(priority_id))
                priority_controller_element = self.get_element_by_path(priority_controller)
                priority_controller_element.click()

                #Referring Provider Lookup
                time.sleep(1)
                provider_lookup = self.get_element_by_path('//*[@id="pnlReqProvInfo"]/div/div[2]/div[1]/span[1]').click()
                main_handle = self.driver.current_window_handle
                handles = self.driver.window_handles
                for handle in handles:
                    if handle != main_handle:
                        self.driver.switch_to.window(handle)
                        provider_box = self.get_element_by_path('//*[@id="txtprovidid"]')
                        if provider_box is None:
                            request.Message = 'Unable to load provider lookup box section'
                            process_list.append(request)
                            self.driver.close()
                            return
                        provider_box.send_keys(data["provider_id"])
                        provider_search_box = self.get_element_by_path('//*[@id="btnprovsearch"]').click()
                        time.sleep(1)
                        provider_search_results = self.get_element_by_path('//*[@id="grdProvider_ctl02_lnkproviderid"]').click()

                self.driver.switch_to.window(main_handle)
                self.driver.switch_to.default_content()
                self.frame_switch('viewFrame')
                time.sleep(1)
                location = self.get_element_by_path('//*[@id="s2id_ddlReferringOffice"]/a/span[1]').click()
                location_select = self.get_element_by_path("//div[@id='select2-drop']/ul/li[2]").click()

                self.get_element_by_path('//*[@id="chbSameAsReqProv"]').click()

                # add diagnoses items
                time.sleep(1)
                self.driver.switch_to.default_content()
                self.frame_switch('viewFrame')
                diagnose_items = [n for n in member['ICDs'] if n is not None]
                print('Adding diagnoses')
                logger.info('Adding diagnoses')
                i = 1
                for item in diagnose_items:
                    print(f'Diagnoses item: {item}')
                    logger.info(f'Diagnoses item: {item}')
                    diagnose_data_element = self.driver.find_element_by_id(f'txtDiag{i}')
                    print(diagnose_data_element.text)
                    diagnose_data_element.click()
                    diagnose_data_element.clear()
                    diagnose_data_element.send_keys(item + Keys.ENTER)
                    icd_description = self.get_element_by_path(f'//*[@id="txtDiagDesc{i}"]')
                    print(icd_description.text)
                    if icd_description is None:
                        request.Message = f'Unable to find ICD10 Code: {item}'
                        logger.error(f'Unable to find ICD10 Code: {item}')
                        print(f'Unable to find ICD10 Code: {item}')
                        process_list.append(request)
                        self.write_member_details_to_file(process_list)
                        return
                    # time.sleep(1)
                    i = i + 1

                # add Services
                service_items = [n for n in member['CPTs'] if n["type"] is not None]
                print('Adding services')
                logger.info('Adding services')
                cpt_service_count = 2
                for service in service_items:
                    print(f'CPT Service: {service["type"]} - {service["value"]}')
                    logger.info(f'CPT Service: {service["type"]} - {service["value"]}')
                    service_data_element = self.get_element_by_path(f'//*[@id="dtServiceCode"]/tbody/tr[{cpt_service_count}]/td[2]/input')
                    service_data_element.click()
                    service_data_element.clear()
                    service_data_element.send_keys(str(service["type"]) + Keys.ENTER)
                    print(f'{service["type"]} Added')
                    logger.info(f'{service["value"]} units added')

                    service_cpt_units_box_element = self.get_element_by_path(f'//*[@id="dtServiceCode"]/tbody/tr[{cpt_service_count}]/td[7]/input')
                    if service_cpt_units_box_element is None:
                        request.Message = f'Unable to find Service QTY box for memberId: {member.MemberId}'
                        logger.error(f'Unable to find Service QTY box for memberId: {member.MemberId}')
                        process_list.append(request)
                        return
                    action = ActionChains(self.driver)
                    action.click(service_cpt_units_box_element).perform()
                    action.send_keys(Keys.BACKSPACE, str(service["value"])).perform()
                    print(f'{service["value"]} units added')
                    logger.info(f'{service["value"]} units added')
                    #Units Selections
                    self.get_element_by_path(f'//*[@id="dtServiceCode"]/tbody/tr[{cpt_service_count}]/td[8]/select/option[6]').click()

                    #To add another service line
                    if cpt_service_count >= 6:

                        service_cpt_units_box_element.send_keys(Keys.PAGE_DOWN)
                        time.sleep(.5)
                        add_service_line = self.get_element_by_path('//*[@id="saddrowforservice"]/span/span')
                        add_service_line.click()

                    cpt_service_count = cpt_service_count + 1

                #Comment Element
                comment_element = self.get_element_by_path(comment)
                comment_element.send_keys(member['Message'])
                print('Added message')
                logger.info('Added message')

                #Upload Document Button
                print('Switching to upload document tab')
                logger.info('Switching to upload document tab')
                upload_doc_button_path = self.get_element_by_path(upload_doc_button)
                upload_doc_button_path.click()

                #Adding Document
                time.sleep(1)
                member["FilePath"] = os.getcwd() + '/insurance/PRIME SUBMIT 01.pdf'
                files = [n for n in member["FilePath"].split(',') if n is not None]
                logger.info(f'Number of files to attach: {str(len(files))}')
                if len(files) > 0:
                    file_count = 0
                    for file in files:
                        print(f'Adding file: {file} to member: {member["MemberId"]}')
                        logger.info(f'Adding file: {file} to member: {member["MemberId"]}')
                        notes_dropdown_arrow = self.get_element_by_path(f'//*[@id="ddlCategory_new_{file_count}"]/option[5]')
                        notes_dropdown = self.get_element_by_path(f'//*[@id="ddlCategory_new_{file_count}"]/option[5]').click()
                        if notes_dropdown_arrow is None:
                            message = 'Unable to find notes dropdown arrow.'
                            request.Message = message
                            process_list.append(request)
                            raise Exception(message)
                        upload_file = f'//*[@id="att_new_file_{file_count}"]'
                        upload_text_element = self.is_element_exist(upload_file)
                        if upload_text_element is None:
                            message = f'Unable to add the document: {file}'
                            request.Message = request.Message + f'Unable to add the document: {file}'
                            logger.error(f'Failed to add file: {file} to member: {member["MemberId"]}')
                            raise Exception(message)
                        upload_text_element.send_keys(file)
                        time.sleep(1)
                        if int(file_count) + 1 < len(files):
                            self.get_element_by_path('//*[@id="btnDocAdd"]').click()
                            file_count = file_count + 1

                #Submitting for AUTH
                if submitted_by_dev == "0":
                    save_button = self.get_element_by_path('//*[@id="btnSave"]').click()
                    logger.debug(f'Auth Submitted for {member["MemberId"]}')
                    print(f'Auth Submitted for {member["MemberId"]}')

            except Exception as ex:
                logger.error(f'ERROR. member: {member["MemberId"]}, Exception: {ex}')
                print(f'ERROR: {ex}')
                request.Message = f'Error for {member["MemberId"]}, Exception: {ex}'
                process_list.append(request)
                continue

            i = i + 1
            request.Success = True
            process_list.append(request)

        self.driver.close()
        print('All Members Processed')
        for lst in process_list:
            pprint(vars(lst))
        return {"success": True, "request_list": process_list}

    def get_element_by_path(self, element_path):
        logger.debug(f'finding element: {element_path}')
        return self.driver.find_element_by_xpath(element_path)

    def frame_switch(self, val, timeout=2):
        try:
            frame = WebDriverWait(self.driver, timeout).until(EC.frame_to_be_available_and_switch_to_it((By.NAME, val)))
            print(f'Switching to frame: {val}')
            logger.debug(f'Switching to frame: {val}')
            return frame
        except:
            print(f'Unable to Switch Frame: {val}')

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

    def SubmitAuthRequest(self, memberList, settings):
        logger.info(
            '============================ Start program ==============================')
        try:
            for member in memberList:
                print('MemberId: ' + str(member['MemberId']))
            # start processing data
            return self.start_execution(memberList, settings)
        except Exception as ex:
            #raise Exception(ex)
            print(str(ex))
            return {"success": False, "message": str(ex), "request_list": []}