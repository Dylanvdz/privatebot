import time
import os
import logging
import threading

from webhookHandler import hook
from loadCredentials import load
from keywordMonitors import kwMonitor
from datetime import datetime
from colorama import Fore, Back, Style, init
from captchaHarvester import Harvester

class toolsModules():

    # Test webhook
    def testhook(self):
        settings = load().loadSettings()
        username = settings['USERNAME']
        privatewebhook = settings['WEBHOOK']
        time_ = datetime.now().strftime("%H:%M:%S")

        try:
            response = hook().sendTestWebhook(username, privatewebhook, time_)
            print(f" {time_} | {Fore.GREEN}Webhook test successfull!{Style.RESET_ALL}")
        except Exception as e:
            print(f" {time_} | Webhook | {Fore.RED}Error sending webhook ({e}){Style.RESET_ALL}")
        if type(response) is not bool:
            print(f" {time_} | Webhook | {Fore.RED}Error sending webhook, response: {response.status_code}{Style.RESET_ALL}")
        time.sleep(2)
        # Clear the screen from previous prints
        os.system('cls')
    
    def keywordCheckMenu(self):
        # Clear the screen from previous prints
       # os.system('cls')

        # Objects / variables
        time_ = datetime.now().strftime("%H:%M:%S")

        print(f" {time_} | {Fore.CYAN}Starting keyword check...\n{Style.RESET_ALL}")
        sitelist = ['Queens']
        # Print the sitelist
        for i in range(len(sitelist)):
            print(f" {time_} | {Fore.YELLOW}[{i}]{Style.RESET_ALL} {sitelist[i]}")

        print(f"\n {time_} | {Fore.YELLOW}Enter site: {Style.RESET_ALL}", end='')
        site = input()

        if site == '0' or site.lower() == 'queens':
            print(f" {time_} | {Fore.YELLOW}Enter keyword(s): {Style.RESET_ALL}", end='')
            keywords = input()
            kwMonitor().queensKWCheck(keywords)
        else:
            print(f" {time_} | {Fore.RED}{site} is not an option{Style.RESET_ALL}")
            time.sleep(2)
        # Clear the screen from previous prints
        os.system('cls')
        return
    
    def harvesterQueens(self):
        # Clear the screen from previous prints
        os.system('cls')
        time_ = datetime.now().strftime("%H:%M:%S")

        logging.basicConfig(format=' %(asctime)s | Harvester | %(message)s', level=logging.INFO, datefmt='%H:%M:%S')
        logging.getLogger("requests").setLevel(logging.WARNING)

        print(f" {time_} | {Fore.CYAN}Starting harvester...\n{Style.RESET_ALL}")

        # Load captcha token
        settings = load().loadSettings()
        service = settings['CAPTCHA_SERVICE']

        if service.lower() == '2captcha':
            api_token = settings['2CAPTCHA_TOKEN']
        if service.lower() == 'capmonster':
            api_token = settings['CAPMONSTER_TOKEN']
        elif service.lower() != '2captcha' and service.lower() != 'capmonster':
            print(f" {time_} {Fore.RED}| Harvester | Please enter correct captcha service in settings..{Style.RESET_ALL}")
            time.sleep(2)
            return
        
        tasks = load().loadTasks('Queens')
        # Reset all previous data
        data = []
        for i in range(len(tasks)):
            temp = {"harvester_id": str(i+1), "data": {"captcha_token": ""}}
            data.append(temp)
        load().writeCaptchaStorage(data)

        lock = threading.Lock()
        threads = []
        for i in range(len(tasks)):
            threads.append(threading.Thread(target=Harvester().queensHarvester, args=(int(i+1), api_token, service, lock)))
            
        for i in threads:
            i.start()
        for i in threads:
            i.join()