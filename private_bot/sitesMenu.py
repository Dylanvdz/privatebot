import curses
import os
import ctypes

from datetime import datetime
from runMode import modules

banner = r"""
    ___    __    ____  __  _____       ________    ____
   /   |  / /   / __ \/ / / /   |     / ____/ /   /  _/
  / /| | / /   / /_/ / /_/ / /| |    / /   / /    / /  
 / ___ |/ /___/ ____/ __  / ___ |   / /___/ /____/ /   
/_/  |_/_____/_/   /_/ /_/_/  |_|   \____/_____/___/                      

               --- Private CLI bot ---

"""
#modes = ['Start tasks', 'Shock mode [lOCKED', 'Exit']
modes = []
site = ''
tasks = ''
proxies = ''

class site_menu():

    def main(self, nsite):
        global site, tasks, proxies, modes
        site = nsite

        """
        Important :
            - Version need to be scraped from the google sheets api when new auth system gets implemented
            for now its hardcoded
        """
        version = "v0.1.9.5"
        # Set title bar
        ctypes.windll.kernel32.SetConsoleTitleW(f"AlphaCLI {version} | {site} menu")

        if site == 'Queens' or site == 'Wearestrap' or site == 'LDLC':
            modes = ['Start tasks', 'Shock mode', 'Exit']
        
        # Load tasks and proxies to show on the menu
        task_data = modules().loadData(site)
        if task_data == False:
            input()
            os.system('cls')
            return
        else:
            tasks = len(task_data[0])
            proxies = len(task_data[1])
        os.system('cls')
        curses.initscr()
        curses.wrapper(site_menu().menu)
    
    def menu(self, stdscr):
        # Capture the current time
        time = datetime.now().strftime("%H:%M:%S")
        mode = ''

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
            stdscr.addstr(f" {time} | ", curses.color_pair(2))
            stdscr.addstr(f"{site} menu ", curses.color_pair(4))
            stdscr.addstr(f"| Tasks {tasks} | Proxies {proxies}\n\n", curses.color_pair(2))

            for i in range(len(modes)):
                if i == option:
                    attr = attributes['selected']
                else:
                    attr = attributes['not-selected']
                    #--------
                #stdscr.addstr("------------ | ", curses.color_pair(1))
                stdscr.addstr(f" {time} |", curses.color_pair(2))
                stdscr.addstr(" [{0}] ".format(i+1), curses.color_pair(5))
                stdscr.addstr(f"{modes[i]}\n", attr)
            c = stdscr.getch()
            if c == curses.KEY_UP and option > 0:
                option -= 1
            elif c == curses.KEY_DOWN and option < len(modes)-1:
                option += 1
            
        mode = modes[option]
        curses.endwin()

        if mode == 'Start tasks':
            # Run all tasks
            modules().startAllTasks(site)
            return
        if mode == 'Shock mode':
            # Run shock mode
            modules().shockMode(site)
            return
        if mode == 'Exit':
            return