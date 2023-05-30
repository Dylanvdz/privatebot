import logging
import threading
"""
Makes sure correct format is printed

from customLogging import Clogging

Clogging().printNormal("text")
Clogging().printGreen("text")
Clogging().printRed("text)
"""

class Clogging():
    
    def __init__(self, num):
        task = "{:0>3d}".format(num)
        self.task = task

    def printYellow(self, msg):
        logging.warning(f"Task {self.task} |  {msg}")
    
    def printGreen(self, msg):
        logging.info(f"Task {self.task} |  {msg}")

    def printRed(self, msg):
        logging.error(f"Task {self.task} |  {msg}")