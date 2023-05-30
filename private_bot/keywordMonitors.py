import os 
import requests
import re

from datetime import datetime
from lxml import html
from lxml import etree
from colorama import Fore, Back, Style, init

class kwMonitor():

    def queensKWCheck(self, keywords):
        # Headers
        get_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'cache-control': 'max-age=0',
            'accept-language': 'nl-NL,nl;q=0.9',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
        }

        current_time = datetime.now().strftime("%H:%M:%S")
        # Split keywords
        keywordlist = keywords.split(';')
        endpoints = ['https://www.queens.cz/novinky/', 'https://www.queens.cz/kat/2/boty-tenisky-panske/?filtr[]=1', 'https://www.queens.cz/kat/106/boty-tenisky-damske/?filtr[]=1']

        # Create new session
        session = requests.Session()
        scraped_urls = []
        scraped_keywords = []
        for i in range(len(endpoints)):
            response = session.get(endpoints[i], headers=get_headers)
            source = html.fromstring(response.content)
            products = source.xpath('//*[@id="categoryItems"]')
            all_product = etree.tostring(products[0]).decode('utf-8')

            product_urls = re.findall("<a href=\"(.+?)\">", all_product)
            product_keywords = re.findall("alt=\"(.+?)\"", all_product)
            list(map(lambda url: scraped_urls.append(url), product_urls))
            list(map(lambda keyword: scraped_keywords.append(keyword), product_keywords))
        
        # Check for keywords
        detected_products = []
        for product in scraped_keywords:
            for keyword in keywordlist:
                if keyword.lower() in product.lower():
                    detected_products.append(product)
        print('\n')
        if detected_products != []:
            print(f" {current_time} | {Fore.RED}Monitor | Products found matching your keywords ({len(detected_products)}): {Style.RESET_ALL}")
            list(filter(lambda product: print(f" {current_time} | {Fore.YELLOW}Monitor | {product}{Style.RESET_ALL}"), detected_products))
        else:
            print(f" {current_time} | {Fore.GREEN}Monitor | No products found that match your keywords!{Style.RESET_ALL}")
        input("press enter to exit...")

    def queensMonitor(self, data):
        print('Hello there')
        input()
        return