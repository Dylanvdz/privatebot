import csv
import json

from csv import writer

class load():
    """
    Get loads info for example:
        - settings.json
        - tasks.csv
        - proxy.txt
        - profiles.csv
    """
    
    def loadSettings(self):
        try:
            with open('Settings.json') as config:
                data = json.loads(config.read())
        except:
            # If it fails to open the file then return false
            return False
        else:
            # If it can open the file then return the data from inside the file
            return data
    
    def writeToSettings(self, data):
        with open('Settings.json', 'w', encoding='utf-8') as write:
            json.dump(data, write, indent=4)
    
    def loadTasks(self, site):
        tasks = []
        with open(f'{site}/tasks.csv') as csvFile:
            tasksReader = csv.reader(csvFile)
            for row in tasksReader:
                tasks.append(row)
        # Remove the first row
        # When soft coding this the first row needs to be added again
        tasks.pop(0)
        return tasks
    
    def loadProfiles(self):
        profiles = []
        with open("Profiles.csv") as csvFile:
            csvReader = csv.reader(csvFile)
            for row in csvReader:
                profiles.append(row)
        # Remove the first row
        profiles.pop(0)
        return profiles
    
    def loadProxies(self, site):
        proxies = []
        with open(f"{site}/proxies.txt") as f:
            try:
                for line in f:
                    proxy = line.strip().split(':') # Proxy non formatted
                    # Proxy format http://user:pass@ip:port to use in requests
                    http = f"http://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}"
                    proxies.append(http)
            except:
                for line in f:
                    proxy = line.strip().split(':') # Proxy non formatted
                    # Proxy format http://user:pass@ip:port to use in requests
                    http = f"http://{proxy[0]}:{proxy[1]}"
                    proxies.append(http)
        return proxies
    
    def saveCheckout(self, data):
        #data = ['27-08-2020-15:00:32', 'Dylan', 'Queens', 'https://www.queens.cz/wear/107152/2/nike-air-force-1-07-craft/', '45', 'paypal', '2304', 'test@gmail.com', 'Success', 'None', 'None']
        with open('Checkouts.csv', 'a', newline='') as f:
            csv_writer = writer(f)
            csv_writer.writerow(data)
    
    def readCaptchaStorage(self):
        try:
            with open('misc/captchaHarvester.json') as storage:
                data = json.loads(storage.read())
        except:
            return False
        else:
            return data
    
    def writeCaptchaStorage(self, data):
        with open('misc/captchaHarvester.json', 'w', encoding='utf-8') as storage:
            json.dump(data, storage, indent=4)