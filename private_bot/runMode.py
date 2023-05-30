import time as time_delay
import logging
import os
import concurrent.futures
import requests
import math
import threading

import ctypes

from datetime import datetime
from loadCredentials import load
from colorama import Fore, Back, Style, init
from concurrent.futures import ThreadPoolExecutor, wait, as_completed

from queens import Queens
from wearestrap import WeAreStrap
from ldlc import Ldlc

class AtomicCounter:
    def __init__(self, initial=0):
        """Initialize a new atomic counter to given initial value (default 0)."""
        self.value = initial
        self._lock = threading.Lock()

    def increment(self, num=1):
        """Atomically increment the counter by num (default 1) and return the
        new value.
        """
        with self._lock:
            self.value += num
            return self.value

class modules():
    
    def loadData(self, site):
        time = datetime.now().strftime("%H:%M:%S")

        logging.basicConfig(format=' %(asctime)s | '+site+' | %(message)s', level=logging.INFO, datefmt='%H:%M:%S')
        logging.getLogger("requests").setLevel(logging.WARNING)

        # Load tasks
        try:
            tasks = load().loadTasks(site)
        except Exception as e:
            print(f" {time} | {Fore.RED} Error loading tasks ({e}){Style.RESET_ALL}")
            return False
        # Load proxies
        try:
            proxies = load().loadProxies(site)
        except Exception as e:
            print(f" {time} | {Fore.RED} Error loading proxies ({e}){Style.RESET_ALL}")
            return False
        # Load profiles
        try:
            profiles = load().loadProfiles()
        except Exception as e:
            print(f" {time} | {Fore.RED} Error loading profiles ({e}){Style.RESET_ALL}")
            return False
        
        os.system('cls')
        return [tasks, proxies, profiles]
    
    def startAllTasks(self, site):
        time = datetime.now().strftime("%H:%M:%S")

        # Load tasks, proxies and profiles
        run_data = modules().loadData(site)
        if run_data == False:
            input()
            return
        
        tasks = run_data[0]
        proxies = run_data[1]
        profiles = run_data[2]

        # Check if tasks, profiles and proxies file is empty an
        if len(tasks) < 1:
            print(f" {time} | {Fore.RED} Your tasks file is empty! {Style.RESET_ALL}")
            time_delay.sleep(2)
            os.system('cls')
            return
        if len(profiles) < 1:
            print(f" {time} | {Fore.RED} Your profiles file is empty! {Style.RESET_ALL}")
            time_delay.sleep(2)
            os.system('cls')
            return
        # Check if proxy file is empty
        if len(proxies) == 0:
            print(f" {time} | {Fore.RED}No proxies loaded, running on local host. Are you sure you want to continue? [Y or N]: {Style.RESET_ALL}", end='')
            run_no_prox = input().lower()
            if str(run_no_prox) != 'y':
                print(f" {time} | Terminated process...")
                time_delay.sleep(2)
                os.system('cls')
                return

        print(f" {time} | {Fore.CYAN}Starting all tasks...{Style.RESET_ALL}")
        modules().startThreads(run_data, site)
        os.system('cls')
        return
    
    def shockMode(self, site):
        time = datetime.now().strftime("%H:%M:%S")
        # Load tasks, proxies and profiles
        run_data = modules().loadData(site)
        if run_data == False:
            input()
            return
            
        tasks = run_data[0]
        proxies = run_data[1]
        profiles = run_data[2]
        
        if len(tasks) < 1:
            print(f" {time} | {Fore.RED} Your tasks file is empty! {Style.RESET_ALL}")
            time_delay.sleep(2)
            os.system('cls')
            return
        if len(profiles) < 1:
            print(f" {time} | {Fore.RED} Your profiles file is empty! {Style.RESET_ALL}")
            time_delay.sleep(2)
            os.system('cls')
            return
        if len(proxies) == 0:
            print(f" {time} | {Fore.RED}No proxies loaded, running on local host. Are you sure you want to continue? [Y or N]: {Style.RESET_ALL}", end='')
            run_no_prox = input().lower()
            if str(run_no_prox) != 'y':
                print(f" {time} | Terminated process...")
                time_delay.sleep(2)
                os.system('cls')
                return
        print(f" {time} | {Fore.CYAN}Starting shock mode...{Style.RESET_ALL}")

        shock_input = ''
        while(shock_input == ''):
            print(f" {time} | Shock Mode | {Fore.YELLOW}Enter product url: {Style.RESET_ALL}", end='')
            shock_input = input()
        
        for task in tasks:
            task[3] = shock_input
        modules().startThreads(run_data, site)
        os.system('cls')
        return
    
    def startThreads(self, data, site):
        time = datetime.now().strftime("%H:%M:%S")

        # Load the settings file
        settings = load().loadSettings()

        tasks = data[0]
        proxies = data[1]
        profiles = data[2]

        """
        Important :
            - Version need to be scraped from the google sheets api when new auth system gets implemented
            for now its hardcoded
        """

        proxies_amount = math.floor(len(proxies)/len(tasks))
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=500)
        run_tasks = []
        proxy_list = []

        cartcounter = AtomicCounter()
        checkoutcounter = AtomicCounter()
        
        version = "v0.1.9"
        # Set title bar
        ctypes.windll.kernel32.SetConsoleTitleW(f"AlphaCLI {version} | Tasks {len(tasks)} | Carts {checkoutcounter.value} | Checkouts {cartcounter.value}")
        for i in range(len(tasks)):
            task = tasks[i]
            session = requests.Session()

            if len(proxies) > 0:
                # Calculate amount_proxies / amount_tasks and round down to full integer to get how many proxies per task for rotation
                if proxies_amount == 0:
                    print(f" {time} | {Fore.RED}More tasks then proxies loaded, please add more proxies{Style.RESET_ALL}")
                    time_delay.sleep(3)
                    return
                proxy_list = []
                for _ in range(proxies_amount):
                    proxy_list.append(proxies[0])
                    proxies.pop(0)
            #threading.session = session
            task_data = [task, profiles, proxy_list, session, settings, int(i+1), cartcounter, checkoutcounter, len(tasks)]
            
            if site == 'Queens':
                queens = Queens(task_data)
                run_tasks.append(pool.submit(queens.main))
            if site == 'Wearestrap':
                wearestrap = WeAreStrap(task_data)
                run_tasks.append(pool.submit(wearestrap.main))
            if site == 'LDLC':
                ldlc = Ldlc(task_data)
                run_tasks.append(pool.submit(ldlc.main))
        
        for future in concurrent.futures.as_completed(run_tasks):
            task_result = future.result()
            try:
                load().saveCheckout(task_result)
            except:
                pass
        
        pool.shutdown(wait=True)
        input('All tasks are finished, press enter to return...')