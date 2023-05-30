import ctypes
import threading
import requests
import random
import re
import time
import json

from lxml import html
from lxml import etree
from requestData import requestProfileData, requestTaskData
from httpResponseHandler import HttpResponseHandler
from customLogging import Clogging
from MiscHandling import miscHandling
from webhookHandler import hook

class WeAreStrap():

    def __init__(self, data):
        self.task_data = data[0]
        self.profiles = data[1]
        self.proxy_list = data[2]
        self.session = data[3]
        self.settings = data[4]
        self.task_num = data[5]
        self.carts = data[6]
        self.checkouts = data[7]
        self.amount_tasks = data[8]
    
    def main(self):
        ctypes.windll.kernel32.SetConsoleTitleW(f"AlphaCLI 0.2.0 | Tasks {self.amount_tasks} | Carts {self.carts.value} | Checkouts {self.checkouts.value}")
        task_request = requestTaskData(self.task_data)
        log = Clogging(self.task_num)

        log.printYellow("Setting up session...")

        product_url = task_request.getProductUrl()
        size = task_request.getSize()
        profile_name = task_request.getProfile()

        # Get profile for task
        task_profile = ''
        for profile in self.profiles:
            if profile[0] == profile_name:
                task_profile = profile
                break # Stop looping through more profiles
        if task_profile == '':
            log.printRed(f"Profile '{profile_name}' not found, stopping task...")
            return False
        profile_request = requestProfileData(task_profile)

        # Load settings
        settings = self.settings
        username = settings['USERNAME']
        privatewebhook = settings['WEBHOOK']
        delay = int(settings['DELAY'])/1000
        monitor_delay = int(settings["MONITOR_DELAY"])/1000
        cartsound = settings['CART_SOUND']
        checkoutsound = settings['CHECKOUT_SOUND']

        # If cartsound is True make extra threadto play sound in
        if cartsound == 'true':
            play_cart = threading.Thread(target=miscHandling().playsoundCart)

        productfound = False
        carted = False
        checkout = False
        while(not checkout):
            # First scrape the product
            while(not productfound):
                try:
                    log.printYellow('Getting product page...')
                    product_info = self.findProduct(product_url)
                except Exception as e:
                    log.printRed(f'Failed to get productpage')
                else:
                    if type(product_info) is not list:
                        HttpResponseHandler().QueensResponse(product_info, log)
                        if product_info == 429 or product_info == 403:
                            self.session = requests.Session()
                            if len(self.proxy_list) > 0:
                                proxy = random.choice(self.proxy_list)
                                self.session.proxies.update({'http:': proxy})
                    else:
                        product_name = product_info[0]
                        product_image = product_info[1]
                        product_price = product_info[2]
                        id_product = product_info[3]
                        id_customization = product_info[4]
                        token = product_info[5]
                        variants = product_info[6]
                        sizes = product_info[7]

                        if sizes == False:
                            log.printGreen(f'Found {product_name} -- No sizes found')
                        else:
                            log.printGreen(f'Found {product_name} -- {sizes}')
                        productfound = True
                if not productfound:
                    time.sleep(monitor_delay)

            while(not carted):
                if sizes == False:
                    # Rescrape sizes
                    try:
                        size_scrape = self.parseSizes(product_url)
                    except Exception as e:
                        log.printRed(f'Failed to get productpage -- {e}')
                    else:
                        if type(size_scrape) is not list:
                            HttpResponseHandler().QueensResponse(size_scrape, log)
                            if size_scrape == 429 or size_scrape == 403:
                                if len(self.proxy_list) > 0:
                                    proxy = random.choice(self.proxy_list)
                                    self.session.proxies.update({'http:': proxy})
                        else:
                            if size_scrape[0] == False:
                                log.printYellow(f"{product_name} -- no sizes found, retrying...")
                            else:
                                variants = size_scrape[0]
                                sizes = size_scrape[1]
                                log.printGreen(f'{product_name} -- found sizes {sizes}')
                else:
                    selected_size = ''
                    if size.upper() == 'RANDOM':
                        # Grab a random size
                        r_index = int(random.randint(0, len(variants)-1)) # Get random index
                        variant = variants[r_index]
                        selected_size = sizes[r_index]
                    log.printYellow(f'Adding size {selected_size} to cart...')

                    try:
                        cart_data = [product_url, token, id_product, id_customization, variant]
                        cart_response = self.addToCart(cart_data)
                    except Exception as e:
                        log.printRed(f'Unexpected error when adding to cart -- {e}')
                    else:
                        # Check if return type is not a bool
                        if type(cart_response) is not list:
                            HttpResponseHandler().QueensResponse(cart_response, log)
                            if cart_response == 429 or cart_response == 403:
                                if len(self.proxy_list) > 0:
                                    proxy = random.choice(self.proxy_list)
                                    self.session.proxies.update({'http:': proxy})
                        else:
                            if cart_response[0]:
                                log.printGreen(f'Added size {selected_size} to cart!')
                                carted = True
                                attribute_id = cart_response[1]
                                # Change carts on top bar and play the cart sound
                                if cartsound == 'true':
                                    play_cart.start()
                                    self.carts.increment(1)
                                    ctypes.windll.kernel32.SetConsoleTitleW(f"AlphaCLI 0.2.0 | Tasks {self.amount_tasks} | Carts {self.carts.value} | Checkouts {self.checkouts.value}")
                                else:
                                    log.printYellow(f"Size {selected_size} is OOS, retrying...")
                if not carted:
                    time.sleep(monitor_delay)
            
            checkout = True

        email = task_request.getEmail()
        webhook_data = [self.session, product_name, product_image, username, profile_name, email, 'Paypal', selected_size, 'Wearestrap', settings['WEBHOOK'], product_price, 'Complete in browser', 3066993, '']
        try:
            hook().sendPublicWebhook(webhook_data)
        except Exception as e:
            log.printRed(f"Error sending public webhook -- {e}")
        try:
            hook().sendPrivateWebhook(webhook_data)
        except Exception as e:
            log.printRed(f"Error sending private webhook -- {e}")
        input()
                    
    def findProduct(self, product_url):
        get_header = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
        }
        response_productpage = self.session.get(product_url, headers=get_header)

        if response_productpage.status_code in range(200, 299):
            source = html.fromstring(response_productpage.content)
            product_name = source.xpath('//*[@id="main"]/div[1]/div[2]/div[1]/div[1]/h1/text()')
            product_image = source.xpath('//*[@id="main"]/div[1]/div[1]/div[2]/ul/li[1]/img/@src')
            product_price = source.xpath('//*[@id="main"]/div[1]/div[2]/div[1]/div[2]/div/span/@content')
            id_product = source.xpath('//*[@id="product_page_product_id"]/@value')
            id_customization = source.xpath('//*[@id="product_customization_id"]/@value')
            token = source.xpath('//*[@id="add-to-cart-or-refresh"]/input[1]/@value')

            try:
                size_table_path = source.xpath('//*[@id="EU"]')
                sizes_table = etree.tostring(size_table_path[0]).decode('utf-8')
                variants = re.findall('<span data-valor="(.+?)"', sizes_table)
                sizes = re.findall('data-referencia="(.+?)"', sizes_table)

                return [product_name[0], product_image[0], product_price[0], id_product[0], id_customization[0], token[0], variants, sizes]
            except:
                return [product_name[0], product_image[0], product_price[0], id_product[0], id_customization[0], token[0], False, False]

        else:
            return response_productpage.status_code
    
    def parseSizes(self, product_url):
        get_header = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
        }
        response_productpage = self.session.get(product_url, headers=get_header)

        if response_productpage.status_code in range(200, 299):
            source = html.fromstring(response_productpage.content)
            try:
                size_table_path = source.xpath('//*[@id="EU"]')
                sizes_table = etree.tostring(size_table_path[0]).decode('utf-8')
                variants = re.findall('<span data-valor="(.+?)"', sizes_table)
                sizes = re.findall('data-referencia="(.+?)"', sizes_table)
                return [variants, sizes]
            except:
                return [False, False]
        else:
            return response_productpage.content
    
    def addToCart(self, data):
        product_url = data[0]
        token = data[1]
        id_product = data[2]
        id_customization = data[3]
        variant = data[4]
        
        cart_headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache',
            'content-length': '200',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://wearestrap.com',
            'pragma': 'no-cache',
            'referer': product_url,
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }
        cart_form_data = {
            'token': token,
            'id_product': id_product,
            'id_customization': id_customization,
            'group[1]': variant,
            'qty': '1',
            'add': '1',
            'action': 'update'
        }
        cart_response = self.session.post('https://wearestrap.com/en/cart', data=cart_form_data, headers=cart_headers)

        if cart_response.status_code in range(200, 299):
            cart_json = json.loads(cart_response.content)
            return [cart_json['success'], cart_json['id_product_attribute']]
        else:
            return cart_response.status_code