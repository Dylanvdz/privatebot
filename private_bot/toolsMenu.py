import curses
import time
import os 
import ctypes

from tools import toolsModules
from datetime import datetime

banner = r"""
  ______            __        __  ___                
 /_  __/___  ____  / /____   /  |/  /__  ____  __  __
  / / / __ \/ __ \/ / ___/  / /|_/ / _ \/ __ \/ / / /
 / / / /_/ / /_/ / (__  )  / /  / /  __/ / / / /_/ / 
/_/  \____/\____/_/____/  /_/  /_/\___/_/ /_/\__,_/ 

               --- Private CLI bot ---

"""

tools = ['Webhook test', 'Queens harvester', 'Exit']

class Tools():

    def main(self):
        curses.initscr()
        curses.wrapper(Tools().loadMenu)
    
    def loadMenu(self, stdscr):
        """
        Important :
            - Version need to be scraped from the google sheets api when new auth system gets implemented
            for now its hardcoded
        """
        version = "v0.1.9.5"
        # Set title bar
        ctypes.windll.kernel32.SetConsoleTitleW(f"AlphaCLI {version} | Tools menu")

        # Capture the current time
        time = datetime.now().strftime("%H:%M:%S")

        # Define the colors used
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK) # White color
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Color yellow
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK) # Red color

        # Load the navigation bar
        attributes = {}
        attributes['selected'] = curses.color_pair(2)
        attributes['not-selected'] = curses.color_pair(1)

        c = 0
        option = 0
        while(c != 10):
            stdscr.erase()
            stdscr.addstr(banner, curses.color_pair(3))
            stdscr.addstr(f" {time} | ", curses.color_pair(1))
            stdscr.addstr("Tools menu\n\n", curses.color_pair(3))

            for i in range(len(tools)):
                if i == option:
                    attr = attributes['selected']
                else:
                    attr = attributes['not-selected']
                    #--------
                #stdscr.addstr("------------ | ", curses.color_pair(1))
                stdscr.addstr(f" {time} |", curses.color_pair(1))
                stdscr.addstr(" [{0}] ".format(i+1), curses.color_pair(2))
                stdscr.addstr(f"{tools[i]}\n", attr)
            c = stdscr.getch()
            if c == curses.KEY_UP and option > 0:
                option -= 1
            elif c == curses.KEY_DOWN and option < len(tools)-1:
                option += 1

        tool = tools[option]
        curses.endwin()

        if tool == 'Webhook test':
            toolsModules().testhook()
        #if tool == 'Keyword check':
            #toolsModules().keywordCheckMenu()
        if tool == 'Queens harvester':
            toolsModules().harvesterQueens()