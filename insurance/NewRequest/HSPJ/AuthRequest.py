from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from insurance.NewRequest.HSPJ.PatientNewRequestData import PatientNewRequestData
from pprint import pprint
import time, datetime, logging, json
import os.path
from os import path
from logging.handlers import RotatingFileHandler
from random import *

logging.basicConfig(handlers=[RotatingFileHandler(filename='insurance/logs/SystemLog.log', mode='a', maxBytes=512000, backupCount=4)],
                    level='DEBUG',
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m/%d/%Y%I:%M:%S %p')

logger = logging.getLogger('my_logger')


# list of XPath
loading = '//*[@id="LoadingPanel"]'
download_file_name = 'AuthSummary.pdf'
new_request_path = '//*[@id="Form1"]/div[4]/div[2]/a[1]'
member_id_path = '//*[@id="txtMemberID"]'
search_member_path = '//*[@id="btnSearch"]'
member_name_path = '//*[@id="tblMain"]/tbody/tr[3]/td[2]/a'

submitted_by_arrow = '//*[@id="ctl00_MainContent_SubmittedByProviderLocationInput_Arrow"]'
submitted_by = '//*[@id="ctl00_MainContent_SubmittedByProviderLocationInput_DropDown"]/div/ul/li[4]'
auth_class_arrow = '//*[@id="ctl00_MainContent_AuthClassInput_Arrow"]'
auth_class = '//*[@id="ctl00_MainContent_AuthClassInput_DropDown"]/div/ul/li[4]'
auth_sub_class_arrow = '//*[@id="ctl00_MainContent_AuthSubClassInput_Arrow"]'
auth_sub_class = '//*[@id="ctl00_MainContent_AuthSubClassInput_DropDown"]/div/ul/li[26]'
fax_number = '//*[@id="ctl00_MainContent_PreferredFaxNumberInput"]'
member_continue = '//*[@id="MainContent_MemberContinueButton"]'

# member detail fields
service_provider = '//*[@id="ctl00_MainContent_ProviderList_ctrl2_ctl00_SearchInput"]'
service_provider_search = '//*[@id="MainContent_ProviderList_ctl00_2_SearchButton_2"]'
diagnose_data = '//*[@id="ctl00_MainContent_ctl11_SearchInput"]'
diagnose_search = '//*[@id="MainContent_ctl11_Button"]'
diagnose_search_pop = '//*[@id="ctl00_MainContent_SearchResultsGrid_ctl00_ctl04_SelectButton"]'
diagnose_search_pop_sec = '//*[@id="ctl00_MainContent_SearchResultsGrid_ctl00_ctl05_SelectButton"]'
diagnose_search_pop_sec_not = '/html/body/form/div[9]/div/div[2]/div/div/table/tbody/tr/td'

service_data = '//*[@id="ctl00_MainContent_ctl13_SearchInput"]'
service_value = '//*[@id="ctl00_MainContent_ServicesGrid_ctl00_ctl{count}_QuantityInput"]'
service_search = '//*[@id="MainContent_ctl13_Button"]'
service_from = '//*[@id="ctl00_MainContent_DatesOfServiceInput_FromPicker_dateInput"]'
service_to = '//*[@id="ctl00_MainContent_DatesOfServiceInput_ToPicker_dateInput"]'
comment = '//*[@id="MainContent_AdditionalInformationInput"]'
priority_arrow = '//*[@id="ctl00_MainContent_PriorityInput_Arrow"]'
priority = '//*[@id="ctl00_MainContent_PriorityInput_DropDown"]/div/ul/li[{priority}]'

request_submit = '//*[@id="MainContent_DetailsContinueButton"]'
documents_attached_arrow = '//*[@id="ctl00_MainContent_HasDocumentationInput_Arrow"]'
documents_attached = '//*[@id="ctl00_MainContent_HasDocumentationInput_DropDown"]/div/ul/li[2]'
documents_attached_no = '//*[@id="ctl00_MainContent_HasDocumentationInput_DropDown"]/div/ul/li[3]'
documents_type_arrow = '//*[@id="ctl00_MainContent_DocumentationTypeInput_Arrow"]'
documents_type = '//*[@id="ctl00_MainContent_DocumentationTypeInput_DropDown"]/div/ul/li[3]'
upload_text = '//*[@id="ctl00_MainContent_UploadInputfile0"]'
upload_button = '//*[@id="MainContent_UploadButton"]'
upload_continue_button = '//*[@id="MainContent_DocumentationContinueButton"]'
summary_print = '//*[@id="MainContent_SummaryPrintButton"]'
summary_auth_link = '//*[@id="MainContent_SummaryAuthNumberLink"]'

member_ref_print_button = '//*[@id="MainContent_ctl00_PrintButton"]'
first_name = '/html/body/form/div[9]/div[2]/div[2]/div[1]/div[2]/div/div/table/tbody/tr[9]/td[1]'
date_submitted = '/html/body/form/div[9]/div[2]/div[2]/div[1]/div[2]/div/div/table/tbody/tr[6]/td[2]'

members = []


class AuthRequest:
    download_directory = '\\data\\'
    input_file_path = 'HPSJ AUTH Project.xlsx'
    user_name = ''
    user_password = ''
    submitted_by_dev = '0'
    driver = {}

    def start_execution(self, memberList, settings):

        try:
            print(pprint(settings))
            with open('insurance/NewRequest/HSPJ/config.json') as f:
                data = json.load(f)
            print(data)
            logger.info(data)

            self.download_directory = data['download_directory']
            user_name = settings.userName  # data['user_name']
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
                response = {"success": False,
                            "message": "Unable to open web driver", "request_list": []}
                return response

            members = memberList

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
        except Exception as ex:
            response = {"success": False,
                        "message": str(ex), "request_list": []}
            self.driver.close()
            self.driver.quit()
            return response

        request_list = []
        i = 0
        forward = True
        for member in members:
            forward = True
            memberId = member['MemberId']
            self.clen_up_existing_files()

            request = PatientNewRequestData()
            request.MemberID = memberId
            request.RequestID = member['requestID']
            request.DateSubmitted = datetime.date.today().strftime('%m/%d/%Y')          

            logger.info(f"Processing memberId: {memberId}")
            try:
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame("left")
                new_request = self.is_element_exist(new_request_path, 5)
                if new_request is None:
                    request.Message = 'Unable to find new request link'
                    logger.error('Unable to find new request link')
                    self.driver.close()
                    self.driver.quit()
                    request_list.append(request)
                    return {"request_list": request_list}
                new_request.click()
                print('switching to parent frame')
                logger.debug('switching to parent frame')

                self.driver.switch_to.default_content()
                self.driver.switch_to.frame("work")
                self.driver.switch_to.frame("criteria")

                logger.debug('Done: switching to criteria frame')
                member_id = self.is_element_exist(member_id_path)
                if member_id is None:
                    request.Message = 'Unable to find new member details screen'
                    logger.error('Unable to find new member details screen')
                    self.driver.close()
                    self.driver.quit()
                    request_list.append(request)
                    return {"request_list": request_list}
                member_id.send_keys(str(memberId))
                member_search = self.get_element_by_path(search_member_path)
                member_search.click()

                logger.debug('switching to results frame')
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame("work")
                self.driver.switch_to.frame("results")

                member_name = self.is_element_exist(member_name_path)
                if member_name is None:
                    request.Message = 'Unable to find new member details. Please check the member Id'
                    request.Success = False
                    request_list.append(request)
                    continue

                member_full_name = member_name.text
                member_name_array = member_full_name.split(',')
                if len(member_name_array) == 2:
                    request.FirstName = member_name_array[1]
                    request.LastName = member_name_array[0]
                if len(member_name_array) == 1:
                    request.FirstName = member_name_array[0]
                member_name.click()

                # member classification section
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame("work")
                auth_class_element = self.is_element_exist(auth_class, 5)
                if auth_class_element is None:
                    request.Message = 'Unable to load member classification section'
                    request_list.append(request)
                    self.driver.close()
                    self.driver.quit()
                    return {"request_list": request_list}

                # only need when use test account
                if submitted_by_dev == '1':
                    submitted_by_arrow_element = self.get_element_by_path(
                        submitted_by_arrow)
                    submitted_by_arrow_element.click()
                    submitted_by_element = self.get_element_by_path(
                        submitted_by)
                    submitted_by_element.click()

                logger.info('Searching auth class arrow')
                auth_class_arrow_element = self.get_element_by_path(
                    auth_class_arrow)
                auth_class_arrow_element.click()

                logger.info('Searching auth class')
                auth_class_element = self.get_element_by_path(auth_class)
                auth_class_element.click()

                loading_element = self.get_element_by_path(loading)
                while True:
                    attributes = self.driver.execute_script('var items = {}; for (index = 0; index < arguments['
                                                            '0].attributes.length; ++index) { items[arguments[0].attributes['
                                                            'index].name] = arguments[0].attributes[index].value }; return '
                                                            'items;', loading_element)
                    print(f'attributes{attributes}')
                    if attributes["style"] is not None and str(attributes["style"]) == 'display: none;':
                        break
                    time.sleep(1)
                    print('waiting until close the loading popup')
                print('loading done')

                logger.info('Searching auth sub class arrow')
                auth_sub_class_arrow_element = self.is_element_exist(
                    auth_sub_class_arrow, 1)
                if auth_sub_class_arrow_element is None:
                    request.Message = 'Unable to load member Auth sub class'
                    self.driver.close()
                    self.driver.quit()
                    request_list.append(request)
                    return {"request_list": request_list}
                time.sleep(2)
                auth_sub_class_arrow_element.click()

                logger.info('Searching auth sub class')
                auth_sub_class_element = self.get_element_by_path(
                    auth_sub_class)
                auth_sub_class_element.click()

                logger.info('Searching fax number')
                fax_number_element = self.get_element_by_path(fax_number)
                fax_number_element.send_keys(
                    Keys.HOME, settings.faxNumber)  # '(209) 479-493')

                logger.info('Continuing to next section')
                member_continue_element = self.get_element_by_path(
                    member_continue)
                member_continue_element.click()

                # complete detail fields
                logger.info('Searching service provider')
                service_provider_element = self.is_element_exist(
                    service_provider, 5)
                if service_provider_element is None:
                    request.Message = 'Unable to load service provide screen'
                    logger.error('Unable to load service provide screen')                    
                    self.driver.close()
                    self.driver.quit()
                    request_list.append(request)
                    return {"request_list": request_list}
                service_provider_element.send_keys(
                    settings.speciality + Keys.ENTER)
                print('DONE: Adding service provider')
                logger.info('DONE: Adding service provider')
                time.sleep(.25)
                loading_element2 = self.get_element_by_path(loading)
                while True:
                    attributes = self.driver.execute_script('var items = {}; for (index = 0; index < arguments['
                                                            '0].attributes.length; ++index) { items[arguments[0].attributes['
                                                            'index].name] = arguments[0].attributes[index].value }; return '
                                                            'items;', loading_element2)
                    print(f'attributes{attributes}')
                    logger.info(f'attributes{attributes}')
                    if attributes["style"] is not None and str(attributes["style"]) == 'display: none;':
                        break
                    time.sleep(.25)
                    print('waiting until close the loading popup')
                    logger.info('waiting until close the loading popup')
                print('loading done')
                logger.info('loading done')

                # add diagnoses items
                diagnose_items = [n for n in member['ICDs']
                                  if n is not None and n != '']
                print('Adding diagnoses')
                logger.info('Adding diagnoses')
                for item in diagnose_items:
                    print(item)
                    logger.info(f'Diagnoses ietm: {item}')
                    diagnose_data_element = self.get_element_by_path(
                        diagnose_data)
                    diagnose_data_element.send_keys(Keys.HOME)
                    diagnose_data_element.clear()
                    diagnose_data_element.send_keys(item + Keys.ENTER)
                    time.sleep(.5)

                    logger.info('switching to work=>DiagnosisSearch')
                    self.driver.switch_to.default_content()
                    self.driver.switch_to.frame("work")
                    self.driver.switch_to.frame("DiagnosisSearch")
                    logger.info('Done:switching to work=>DiagnosisSearch')
                    time.sleep(.5)
                    # waiting_until_loading()

                    diagnose_search_pop_sec_element = self.is_element_exist(
                        diagnose_search_pop_sec)
                    if diagnose_search_pop_sec_element is not None:
                        print('inside the diagnose_search_pop_element')
                        logger.info('inside the diagnose_search_pop_element')
                        time.sleep(.5)
                        try:
                            diagnose_search_pop_element = self.is_element_exist(
                                diagnose_search_pop)
                            diagnose_search_pop_element.click()
                            time.sleep(.5)
                        except:
                            print('Ignoring selecting diagnose code')
                            logger.info('Switching to work')

                    diagnose_search_pop_sec_element_not_found = self.is_element_exist(
                        diagnose_search_pop_sec_not)

                    if diagnose_search_pop_sec_element_not_found is not None:
                        val = diagnose_search_pop_sec_element_not_found.text
                        if val == "No results matched the search text.":
                            request.Message = f"Invalid ICD: {item}"
                            request.Success = False
                            request_list.append(request)
                            forward = False
                            break

                    logger.info('Switching to work')
                    self.driver.switch_to.default_content()
                    self.driver.switch_to.frame("work")
                    print('Done: switching to work')
                    logger.info('Done: switching to work')

                if forward == False:
                    continue
                # add Services
                service_items = [
                    n for n in member['CPTs'] if n['type'] is not None and n['type'] != '']
                print('Adding services')
                logger.info('Adding services')
                service_value_count = 4
                for service in service_items:
                    serviceType = service['type']
                    serviceValue = service['value']
                    print(f"service: {serviceType} - {serviceValue}")
                    logger.info(f"service: {serviceType} - {serviceValue}")
                    service_data_element = self.get_element_by_path(
                        service_data)

                    service_data_element.send_keys(Keys.HOME)
                    service_data_element.clear()
                    service_data_element.send_keys(serviceType + Keys.ENTER)
                    time.sleep(.5)
                    self.waiting_until_loading()
                    controller = str(service_value_count)
                    if service_value_count < 10:
                        controller = f'0{str(service_value_count)}'

                    controller_id = service_value.replace(
                        '{count}', controller)
                    print(f'service controller id {controller_id}')
                    logger.info(f'service controller id {controller_id}')

                    controller_id_element = self.is_element_exist(
                        controller_id, 2)
                    if controller_id_element is None:
                        request.Message = f"Unable to find Service QTY for CPT: {serviceType}"
                        request.Success = False
                        logger.error(
                            f"Unable to find Service QTY for memberId: {memberId}")
                        # self.driver.close()
                        # self.driver.quit()
                        request_list.append(request)
                        forward = False
                        break
                        # return {"request_list": request_list}
                    controller_id_element.clear()
                    controller_id_element.send_keys(serviceValue)

                    service_value_count = service_value_count + 1

                if forward == False:
                    continue

                service_from_element = self.get_element_by_path(service_from)
                service_from_element.send_keys(member['StartDateFormatted'])
                service_to_element = self.get_element_by_path(service_to)
                service_to_element.send_keys(member['EndDateFormatted'])
                comment_element = self.get_element_by_path(comment)
                comment_element.send_keys(member['Message'])

                priority_arrow_element = self.get_element_by_path(
                    priority_arrow)
                priority_arrow_element.click()

                priority_id = 3
                if member['Urgent'].upper() == 'S':
                    priority_id = 2
                priority_controller = priority.replace(
                    '{priority}', str(priority_id))
                priority_controller_element = self.get_element_by_path(
                    priority_controller)
                priority_controller_element.click()                

                request_submit_element = self.get_element_by_path(
                    request_submit)
                request_submit_element.click()
                time.sleep(1)
                documents_attached_element_1 = self.is_element_exist(
                    documents_attached, 5)
                if documents_attached_element_1 is None:
                    message = 'Document upload screen is not loaded. Please submit the document manually'
                    request.Message = message
                    request.Success = True
                    request_list.append(request)
                    self.driver.close()
                    self.driver.quit()
                    return {"success": True, "request_list": request_list}

                documents_attached_arrow_element = self.get_element_by_path(
                    documents_attached_arrow)
                documents_attached_arrow_element.click()

                filesArray = member['FilePath'].split(",")
                files = [n for n in filesArray if n is not None]
                logger.info(f'Number of files to attached: {str(len(files))}')
                if len(files) > 0:
                    documents_attached_element = self.get_element_by_path(
                        documents_attached)
                    documents_attached_element.click()
                    time.sleep(1)

                    documents_type_arrow_element = self.get_element_by_path(
                        documents_type_arrow)
                    documents_type_arrow_element.click()
                    time.sleep(1)
                    documents_type_element = self.get_element_by_path(
                        documents_type)
                    documents_type_element.click()
                    time.sleep(1)

                    for file in files:
                        logger.info(
                            f"Adding file: {file} to member: {memberId}")
                        upload_text_element = self.is_element_exist(
                            upload_text)
                        if upload_text_element is None:
                            request.Message = request.Message + \
                                f'Unable to add the document: {file}'
                            logger.error(
                                f"Failed to add file: {file} to member: {memberId}")
                            continue
                        try:
                            upload_text_element.send_keys(file)
                            time.sleep(1)
                            upload_button_element = self.get_element_by_path(
                                upload_button)
                            upload_button_element.click()
                            time.sleep(1)
                        except:
                            request.Message = request.Message + \
                                f'Unable to add the document: {file}'
                            forward = False
                            request.Success = True
                            request_list.append(request)
                            break

                else:
                    logger.info(f"Zero files for member: {memberId}")
                    documents_attached_no_element = self.get_element_by_path(
                        documents_attached_no)
                    documents_attached_no_element.click()

                if forward == False:
                    continue

                time.sleep(1)
                upload_continue_button_element = self.get_element_by_path(
                    upload_continue_button)
                upload_continue_button_element.click()
                time.sleep(1)

                summary_auth_link_element = self.is_element_exist(
                    summary_auth_link, 1)
                if summary_auth_link_element is None:
                    message = 'Submission summary screen is not loaded'
                    request.Message = message
                    logger.error(
                        f"Submission summary screen is not loaded for member: {memberId}")
                    self.driver.close()
                    self.driver.quit()
                    request_list.append(request)
                    return {"success": True, "request_list": request_list}

                ref_num = summary_auth_link_element.text
                request.ReferenceNumber = ref_num
                member['ReferenceNumber'] = ref_num
                summary_auth_link_element.click()
                time.sleep(1)

                window_list = self.driver.window_handles
                parent_handler = self.driver.current_window_handle
                try:
                    for handler in window_list:
                        print(f'handler: {handler}')
                        try:
                            if handler != parent_handler:
                                self.driver.switch_to.window(handler)
                                member_ref_print_button_element = self.get_element_by_path(
                                    member_ref_print_button)
                                member_ref_print_button_element.click()
                                break
                                time.sleep(5)
                        except:
                            request.Message = 'Error when printing summary document'
                            logger.error(
                                f"Error when printing summary document for member: {memberId}")
                            self.driver.close()
                            self.driver.quit()
                            request_list.append(request)
                            return {"success": True, "request_list": request_list}

                    self.driver.switch_to.window(parent_handler)
                    time.sleep(1)

                    file_path = os.path.join(
                        self.download_directory, download_file_name)
                    try:
                        print(
                            f'Finding file name to rename {memberId}-{ref_num}')
                        logger.info(
                            f'Finding file name to rename {memberId}-{ref_num}')
                        if path.exists(file_path):
                            print(f'Found file to rename: {file_path}')
                            logger.info(f'Found file to rename: {file_path}')
                            os.rename(file_path, os.path.join(self.download_directory,
                                                              f'{memberId}_{ref_num}_Summary.pdf'))
                            print(
                                f'Rename success for: {memberId}_{ref_num}')
                            logger.info(
                                f'Rename success for: {memberId}_{ref_num}')
                        else:
                            message = f'Unable to find the summary pdf for member: {memberId}, Reference: {ref_num}'
                            request.message = message
                            request_list.append(request)
                            logger.error(
                                f'Unable to find the summary pdf for member: {memberId}, Reference: {ref_num}')
                            print(message)
                            self.driver.close()
                            self.driver.quit()
                            return {"success": True, "request_list": request_list}
                    except:
                        logger.error(
                            f'Error when renaming summary file for: {memberId}_{ref_num}')
                        message = f'Error when renaming summary file for: {memberId}_{ref_num}'
                        request.message = message
                        request_list.append(request)
                        self.driver.close()
                        self.driver.quit()
                        return {"success": True, "request_list": request_list}
                except:
                    message = f'Unable to download the summary for member: {memberId}, Reference: {ref_num}'
                    logger.error(
                        f'Unable to download the summary for member: {memberId}, Reference: {ref_num}')
                    request.Message = message
                    request_list.append(request)
                    continue

            except Exception as ex:
                logger.error(
                    f'ERROR. member: {memberId}, Exception: {ex}')
                print(f'ERROR {ex}')
                request.Message = f'ERROR. member: {memberId}, Exception: {ex}'
                request_list.append(request)
                continue
            i = i + 1
            request_list.append(request)
            # break
        time.sleep(5)
        self.driver.close()
        self.driver.quit()
        for lst in request_list:
            pprint(vars(lst))
        return {"success": True, "request_list": request_list}

    def waiting_until_loading(self):
        logger.debug('waiting_until_loading')
        loading_element = self.driver.find_element_by_xpath(loading)
        while True:
            attributes = self.driver.execute_script('var items = {}; for (index = 0; index < arguments['
                                                    '0].attributes.length; ++index) { items[arguments[0].attributes['
                                                    'index].name] = arguments[0].attributes[index].value }; return '
                                                    'items;', loading_element)
            print(f'attributes{attributes}')
            if attributes["style"] is not None and str(attributes["style"]) == 'display: none;':
                break
            time.sleep(1)
            print('waiting until close the loading popup')
            logger.debug('waiting until close the loading popup')

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
