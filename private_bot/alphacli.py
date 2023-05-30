import curses
import Colorer
import time as time_
import os
import ctypes

from curses import textpad
from colorama import Fore, Back, Style, init
from authenticate import auth
from loadCredentials import load
from datetime import datetime
from sitesMenu import site_menu
from toolsMenu import Tools
from MiscHandling import miscHandling

banner = r"""
    ___    __    ____  __  _____       ________    ____
   /   |  / /   / __ \/ / / /   |     / ____/ /   /  _/
  / /| | / /   / /_/ / /_/ / /| |    / /   / /    / /  
 / ___ |/ /___/ ____/ __  / ___ |   / /___/ /____/ /   
/_/  |_/_____/_/   /_/ /_/_/  |_|   \____/_____/___/                      

               --- Private CLI bot ---

"""

sitelist = ['Queens', 'LDLC', 'Tools']
username = ''
init()

class main():

    def loadMenu(self, stdscr):
        """
        Important :
            - Version need to be scraped from the google sheets api when new auth system gets implemented
            for now its hardcoded
        """
        version = "v0.1.9.5"
        # Set title bar
        ctypes.windll.kernel32.SetConsoleTitleW(f"AlphaCLI {version} | Main menu")

        curses.initscr()
        # Capture the current time
        time = datetime.now().strftime("%H:%M:%S")

        # Define the colors used
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK) # White color
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK) # Red color
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Color yellow

        # Load the navigation bar
        attributes = {}
        attributes['selected'] = curses.color_pair(5)
        attributes['not-selected'] = curses.color_pair(2)

        c = 0
        option = 0
        while(c != 10):
            stdscr.erase()
            stdscr.addstr(banner, curses.color_pair(4))
            #stdscr.addstr("------------ | ", curses.color_pair(1))
            stdscr.addstr(f" {time} |", curses.color_pair(2))
            stdscr.addstr(" Welcome ", curses.color_pair(5))
            stdscr.addstr(f"{username}\n\n", curses.color_pair(4))

            for i in range(len(sitelist)):
                if i == option:
                    attr = attributes['selected']
                else:
                    attr = attributes['not-selected']
                    #--------
                #stdscr.addstr("------------ | ", curses.color_pair(1))
                stdscr.addstr(f" {time} |", curses.color_pair(2))
                stdscr.addstr(" [{0}] ".format(i+1), curses.color_pair(5))
                stdscr.addstr(f"{sitelist[i]}\n", attr)
            c = stdscr.getch()
            if c == curses.KEY_UP and option > 0:
                option -= 1
            elif c == curses.KEY_DOWN and option < len(sitelist)-1:
                option += 1
            
        site = sitelist[option]
        curses.endwin()

        if site == 'Queens':
            # Queens module
            site_menu().main('Queens')
        #if site == 'Wearestrap':
            #site_menu().main('Wearestrap')
        if site == 'LDLC':
            site_menu().main('LDLC')
        if site == 'Tools':
            Tools().main()
        
    def lockBot(self, key):
        if auth().user(key) == True:
            print(f"{Fore.GREEN} [AUTH]: Key authenticated!{Style.RESET_ALL}")
            time_.sleep(0.5)
            os.system('cls')

        if auth().user(key) == False:
            print(f"{Fore.RED} [AUTH]: Key is not valid!{Style.RESET_ALL}")
            print("Press enter to exit...", end='')
            input()
            exit()
        return
    
    def checkSettings(self, settings):
        # This function ensures everything is filled into settings and ask for certain data if its empty
        # If settings is false then it failed to read the settings file and it exits the bot
        if settings == False:
            print(F"{Fore.RED} Error loading settings...{Style.RESET_ALL}")
            print("Press enter to exit...", end='')
            input()
            exit()
        change = False
        # Checks if certain settings are filled in
        # Access token cant be empty
        if settings['ACCESS_TOKEN'] == '':
            print(F"{Fore.RED} [SETTINGS] No key found in settings...{Style.RESET_ALL}")
            print(F"{Fore.YELLOW} [SETTINGS] Please enter your key: {Style.RESET_ALL}", end='')
            key = input()
            while(key == ''):
                print(F"{Fore.YELLOW} [SETTINGS] Please enter your key: {Style.RESET_ALL}", end='')
                key = input()
            # Update json and write to settings
            settings['ACCESS_TOKEN'] = key
            change = True
        # Username cant be empty
        if settings['USERNAME'] == '':
            print(F"{Fore.RED } [SETTINGS] No username found in settings...{Style.RESET_ALL}")
            print(F"{Fore.YELLOW} [SETTINGS] Please enter your username: {Style.RESET_ALL}", end='')
            username = input()
            while(username == ''):
                print(F"{Fore.YELLOW} [SETTINGS] Please enter your username: {Style.RESET_ALL}", end='')
                username = input()
            # Update json and write to settings
            settings['USERNAME'] = username
            change = True
        # Captcha token cant be empty
        if settings['2CAPTCHA_TOKEN'] == '':
            print(F"{Fore.RED} [SETTINGS] No 2Captcha token found in settings...{Style.RESET_ALL}")
            print(F"{Fore.YELLOW} [SETTINGS] Please enter your 2Captcha token (Type a space if not used): {Style.RESET_ALL}", end='')
            token = input()
            while(token == ''):
                print(F"{Fore.YELLOW} [SETTINGS] Please enter your 2Captcha token (Type a space if not used): {Style.RESET_ALL}", end='')
                token = input()
            # Update json and write to settings
            settings['2CAPTCHA_TOKEN'] = token
            change = True
        if settings['CAPMONSTER_TOKEN'] == '':
            print(F"{Fore.RED} [SETTINGS] No capmonster token found in settings...{Style.RESET_ALL}")
            print(F"{Fore.YELLOW} [SETTINGS] Please enter your capmonster token (Type a space if not used): {Style.RESET_ALL}", end='')
            token = input()
            while(token == ''):
                print(F"{Fore.YELLOW} [SETTINGS] Please enter your capmonster token (Type a space if not used): {Style.RESET_ALL}", end='')
                token = input()
            # Update json and write to settings
            settings['CAPMONSTER_TOKEN'] = token
            change = True
        # Captcha service cant be empty
        if settings['CAPTCHA_SERVICE'] == '':
            print(F"{Fore.RED} [SETTINGS] No captcha service specified in settings...{Style.RESET_ALL}")
            print(F"{Fore.YELLOW} [SETTINGS] Please enter which captcha service you want to use (2captcha, capmonster): {Style.RESET_ALL}", end='')
            captcha_service = input()
            while(captcha_service  == ''):
                print(F"{Fore.YELLOW} [SETTINGS] Please enter which captcha service you want to use (2captcha, capmonster): {Style.RESET_ALL}", end='')
                token = input()
            # Update json and write to settings
            settings['CAPTCHA_SERVICE'] = captcha_service
            change = True
        # Webhook cant be empty
        if settings['WEBHOOK'] == '':
            print(f"{Fore.RED} [SETTINGS] No webhook url found in settings...{Style.RESET_ALL}")
            print(f"{Fore.YELLOW} [SETTINGS] Please enter your webhook url: {Style.RESET_ALL}", end='')
            webhook_url = input()
            while(webhook_url == ''):
                print(f"{Fore.YELLOW} [SETTINGS] Please enter your webhook url: {Style.RESET_ALL}", end='')
                webhook_url = input()
            # Update json and write to settings
            settings['WEBHOOK'] = webhook_url
            change = True
        
        # Set default values for empty settings
        if settings['DELAY'] == '': # Default delay
            print(f"{Fore.YELLOW} [SETTINGS] Delay is empty, using default delay of '1000'{Style.RESET_ALL}")
            # Update json and write to settings
            settings['DELAY'] = '1000'
            change = True
        if settings['MONITOR_DELAY'] == '': # Default monitor delay
            print(f"{Fore.YELLOW} [SETTINGS] Monitor delay is empty, using default delay of '1000'{Style.RESET_ALL}")
            # Update json and write to settings
            settings['MONITOR_DELAY'] = '1000'
            change = True
        if settings['DISPLAY_ACTIVITY'] == '': # Default activity preference
            print(f"{Fore.YELLOW} [SETTINGS] Activity preference is empty, using default value of 'false'{Style.RESET_ALL}")
            # Update json and write to settings
            settings['DISPLAY_ACTIVITY'] = 'false'
            change = True
        if settings['CART_SOUND'] == '': # Default for cart sound
            print(f"{Fore.YELLOW} [SETTINGS] Cart sound is empty, using default of true{Style.RESET_ALL}")
            # Update json and write to settings
            settings['CART_SOUND'] = 'true'
            change = True
        if settings['CHECKOUT_SOUND'] == '': # Default for checkout sound
            print(f"{Fore.YELLOW} [SETTINGS] Checkout sound is empty, using default of true{Style.RESET_ALL}")
            # Update json and write to settings
            settings['CHECKOUT_SOUND'] = 'true'
            change = True
        
        # Check if settings has changed so it needs to save the new settings
        if change:
            try:
                # Write settings to settings.json
                load().writeToSettings(settings)
                print(f"{Fore.GREEN} [SETTINGS] Saved settings!{Style.RESET_ALL}")
            except:
                print(f"{Fore.RED} [SETTINGS] Error writing settings to file, not saved!{Style.RESET_ALL}")
        return settings

if __name__ == "__main__":
    time = datetime.now().strftime("%H:%M:%S")

    print(f"{Fore.CYAN} {banner}{Style.RESET_ALL}")

    loadSettings = load().loadSettings()
    settings = main().checkSettings(loadSettings)
    
    # Bot lock, check if key is valid. User authentication
    main().lockBot(settings['ACCESS_TOKEN'])
    username = settings['USERNAME']

    # Boot settings
    if settings['DISPLAY_ACTIVITY'] == 'true':
        try:
            miscHandling().displayRPC("v0.1.9") # Display game activity
        except Exception as e:
            print(e)
    
    # Clear the screen from previous prints
    os.system('cls')
    while(True):
        curses.wrapper(main().loadMenu)