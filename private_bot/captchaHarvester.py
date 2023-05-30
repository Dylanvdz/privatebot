import requests
import time
import json
from loadCredentials import load
from customLogging import Clogging
from twocaptcha import TwoCaptcha

class Harvester():

    def queensHarvester(self, task, api_token, service, lock):
        log = Clogging(task)

        while(True):
            log.printYellow('Solving captcha...')

            result = ''
            # Solve the captcha, then lock thread and write to json
            if service.lower() == '2captcha':
                try:
                    solver = TwoCaptcha(api_token)
                    result = solver.recaptcha(
                        sitekey='6LeY38UUAAAAALoU0_zoe6vTARi9S8SDLah9a94M',
                        url='https://www.queens.cz/kosik/udaje',
                        data={'action': 'cart'},
                        version='v3'
                    )
                except Exception as e:
                    log.printRed(f'Error solving captcha -- {e}')

            if service.lower() == 'capmonster':
                createTaskData = {
                    "clientKey": api_token,
                    "task": {
                        "type":"RecaptchaV3TaskProxyless",
                        "websiteURL":"https://www.queens.cz/kosik/udaje",
                        "websiteKey":"6LeY38UUAAAAALoU0_zoe6vTARi9S8SDLah9a94M",
                        "pageAction": "cart"
                    }
                }
                try:
                    responseTask = requests.post('https://api.capmonster.cloud/createTask', json=createTaskData)
                except Exception as e:
                    log.printRed(f'Error initializing capmonster task -- {e}')
                else:
                    json_response1 = json.loads(responseTask.content)
                    
                    solution = None
                    while(solution == None):
                        getResultData = {
                            'clientKey': api_token,
                            'taskId': json_response1['taskId']
                        }
                        try:
                            responseResult = requests.post('https://api.capmonster.cloud/getTaskResult', json=getResultData)
                        except Exception as e:
                            log.printRed(f'Error requesting captcha -- {e}')
                        else:
                            json_reponse2 = json.loads(responseResult.content)
                            
                            # Check for errors
                            if json_reponse2['errorId'] == 1:
                                error = json_reponse2['errorCode']
                                if error == 'ERROR_NO_SUCH_CAPCHA_ID' or error == 'WRONG_CAPTCHA_ID':
                                    try:
                                        responseTask = requests.post('https://api.capmonster.cloud/createTask', json=createTaskData)
                                    except Exception as e:
                                        log.printRed(f'Error initializing capmonster task -- {e}')
                                    else:
                                        json_response1 = json.loads(responseTask.content)
                                else:
                                    log.printRed(f'Error solving captcha -- {error}')
                            else:
                                temp = json_reponse2['solution']
                                solution = temp
                    result = temp['gRecaptchaResponse']
            if result != '':
                with lock:
                    data = load().readCaptchaStorage()
                    if data == False:
                        log.printRed('Error reading captcha storage...')
                    else:
                        for i in range(len(data)):
                            if data[i]['harvester_id'] == str(task):
                                data[i]['data']['captcha_token'] = result
                                break
                        try:
                            load().writeCaptchaStorage(data)
                        except:
                            log.printRed('Error storing captcha...')
                        else:
                            log.printGreen('Captcha stored!')
            time.sleep(2)