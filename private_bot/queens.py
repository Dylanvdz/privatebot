import ctypes
import requests
import re
import random
import time
import threading
import json
from datetime import datetime
from lxml import html, etree
from requestData import requestProfileData, requestTaskData
from customLogging import Clogging
from httpResponseHandler import HttpResponseHandler
from MiscHandling import miscHandling
from loadCredentials import load
from webhookHandler import hook
from twocaptcha import TwoCaptcha

class Queens():

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
        
        # Add a proxy to session
        if len(self.proxy_list) > 0:
            proxy = self.proxy_list[0]
            self.session.proxies = {'http': proxy, 'https': proxy}
        else:
            proxy = 'Localhost'
        
        # Load settings
        settings = self.settings
        username = settings['USERNAME']
        privatewebhook = settings['WEBHOOK']
        delay = int(settings['DELAY'])/1000
        monitor_delay = int(settings["MONITOR_DELAY"])/1000
        service = settings['CAPTCHA_SERVICE']
        cartsound = settings['CART_SOUND']
        checkoutsound = settings['CHECKOUT_SOUND']

        # If cartsound is True make extra threadto play sound in
        if cartsound == 'true':
            play_cart = threading.Thread(target=miscHandling().playsoundCart)

        # Grab captcha key
        try:
            captcha_api_key = settings[f'{service.upper()}_TOKEN']
        except:
            log.printRed('Error getting captcha token, please check settings.json...')
            return
        
        # Check the mode
        mode = task_request.getMode()
        if mode.upper() == 'KEYWORD':
            log.printYellow('Starting keyword monitor...')
            # Do keyword monitor here

        if product_url.lower() == 'new':
            old_found = False
            new_found = False
            
            while(not old_found):
                log.printYellow('Monitoring new items (1)...')
                try:
                    old_link_list = self.monitorItem()
                    old_found = True
                except Exception as e:
                    log.printRed(f'Unexpected error monitoring for items -- {e}')
                else:
                    if type(old_link_list) is not list:
                        if old_link_list == False:
                            log.printRed('Failed to scrape new items, retrying...')
                        else:
                            HttpResponseHandler().QueensResponse(old_link_list, log)
                            if old_link_list == 429 or old_link_list == 403:
                                self.session = requests.Session()
                                if len(self.proxy_list) > 0:
                                    proxy = random.choice(self.proxy_list)
                                    self.session.proxies.update({'http:': proxy})
                if not old_found:
                    time.sleep(monitor_delay)
            
            while(not new_found):
                log.printYellow('Monitoring new items (2)...')
                try:
                    link_list = self.monitorItem()
                except Exception as e:
                    log.printRed(f'Unexpected error monitoring for items -- {e}')
                else:
                    if type(link_list) is not list:
                        if link_list == False:
                            log.printRed('Failed to scrape new items, retrying...')
                        else:
                            HttpResponseHandler().QueensResponse(link_list, log)
                            if link_list == 429 or link_list == 403:
                                self.session = requests.Session()
                                if len(self.proxy_list) > 0:
                                    proxy = random.choice(self.proxy_list)
                                    self.session.proxies.update({'http:': proxy})
                    else:
                        list_diff = list(set(link_list)-set(old_link_list))

                        if list_diff != []:
                            log.printGreen(f'Found new item -- {list_diff[0]}')
                            product_url = list_diff[0]
                            new_found = True
                if not new_found:
                    time.sleep(monitor_delay)
        productfound = False
        carted = False
        checkout = False
        item_id = []
        while(not checkout):
            # First scrape the product
            while(not productfound):
                try:
                    log.printYellow('Getting product page...')
                    product = self.findProduct(product_url)
                except Exception as e:
                    log.printRed(f'Failed to get productpage -- {e}')
                else:
                    # Handle response codes
                    if type(product) is not list:
                        HttpResponseHandler().QueensResponse(product, log)
                        if product == 429 or product == 403:
                            self.session = requests.Session()
                            if len(self.proxy_list) > 0:
                                proxy = random.choice(self.proxy_list)
                                self.session.proxies.update({'http:': proxy})
                    else:
                        product_name_split = product[0][0].split(" – ")
                        product_name = product_name_split[0]
                        item_id = product[4]

                        if not item_id:
                            log.printGreen(f"Found {product_name} -- No sizes found")
                        else:
                            variants = product[5]
                            sizes = product[6]

                            if sizes == []:
                                log.printYellow(f"{product_name} is sold out, retrying...")
                            else:
                                log.printGreen(f"Found {product_name} -- {sizes}")
                        productfound = True
                if not productfound:
                    time.sleep(monitor_delay)
            
            while(not carted):
                if not item_id:
                    # Rescrape product page untill sizes are available
                    try:
                        size_scrape = self.parseSizes(product_url)
                    except Exception as e:
                        log.printRed(f'Failed to get productpage -- {e}')
                    else:
                        # Handle response codes
                        if type(size_scrape) is not list:
                            if size_scrape == False:
                                log.printYellow(f"{product_name} -- no sizes found, retrying...")
                            else:
                                HttpResponseHandler().QueensResponse(size_scrape, log)
                                if size_scrape == 429 or size_scrape == 403:
                                    if len(self.proxy_list) > 0:
                                        proxy = random.choice(self.proxy_list)
                                        self.session.proxies.update({'http:': proxy})
                        else:
                            # Add variants and sizes to product array
                            item_id = size_scrape[0]
                            variants = size_scrape[1]
                            sizes = size_scrape[2]

                            if sizes == []:
                                log.printYellow(f"{product_name} is sold out, retrying...")
                            else:
                                log.printGreen(f"{product_name} -- found sizes {sizes}")
                else:
                    selected_size = ''
                    if size.upper() == 'RANDOM':
                        # Grab a random size
                        r_index = int(random.randint(0, len(variants)-1)) # Get random index
                        variant = variants[r_index]
                        selected_size = sizes[r_index]
                    
                    log.printYellow(f'Adding size {selected_size} to cart...')
                    try:
                        atc_data = [product[3], item_id, variant, product_url] # Product[3] = crsf_token
                        cart_response = self.addToCart(atc_data)
                    except Exception as e:
                        log.printRed(f'Unexpected error when adding to cart -- {e}')
                    else:
                        # Check if return type is not a bool
                        if type(cart_response) is not bool:
                            try:
                                HttpResponseHandler().QueensResponse(cart_response, log)
                                if product == 429 or product == 403:
                                    if len(self.proxy_list) > 0:
                                        proxy = random.choice(self.proxy_list)
                                        self.session.proxies.update({'http:': proxy})
                            except:
                                pass
                        else:
                            carted = cart_response
                            
                            if carted:
                                log.printGreen(f'Added size {selected_size} to cart!')
                                # Change carts on top bar and play the cart sound
                                if cartsound == 'true':
                                    play_cart.start()
                                    self.carts.increment(1)
                                    ctypes.windll.kernel32.SetConsoleTitleW(f"AlphaCLI 0.2.0 | Tasks {self.amount_tasks} | Carts {self.carts.value} | Checkouts {self.checkouts.value}")
                            else:
                                log.printYellow(f"Size {selected_size} is OOS, retrying...")
                if not carted:
                    time.sleep(monitor_delay)
            
            country = profile_request.getCountry()
            while(True):
                shipping_country = self.getCountryCode(country)
                if shipping_country == '':
                    log.printRed(f'Shipping to {country} not supported!')
                    time.sleep(monitor_delay)
                else:
                    break
            custom_ship = task_request.getCustomShipping()
            payment_method = task_request.getPayment()
            
            quantity_code = ''
            submit_checkout = False
            submit_shipping = False
            while(not submit_shipping):
                log.printYellow('Submitting shipping...')
                try:
                    shipping_data = [product[3], shipping_country, custom_ship, payment_method, quantity_code]
                    shipping_response = self.submitShipping(shipping_data)
                except Exception as e:
                    log.printRed(f"Unexpected error when submitting shipping -- {e}")
                else:
                    if type(shipping_response) is not list:
                        HttpResponseHandler().QueensResponse(shipping_response, log)
                        if product == 429 or product == 403:
                            if len(self.proxy_list) > 0:
                                proxy = random.choice(self.proxy_list)
                                self.session.proxies.update({'http:': proxy})
                    else:
                        submit_shipping = True
                if not submit_shipping:
                    time.sleep(monitor_delay)
            
            # Handle captcha
            captcha_token = ''
            while(captcha_token == ''):
                harvester = task_request.getHarvester()
                if harvester.lower() == 'true':
                    log.printYellow('Requesting captcha from harvester...')
                    try:
                        captcha_storage = load().readCaptchaStorage()
                    except Exception as e:
                        log.printRed('Error while requesting captcha, retrying...')
                    else:
                        if captcha_storage == False:
                            log.printRed('Error when reading captcha storage, retrying...')
                        else:
                            for i in captcha_storage:
                                if i['harvester_id'] == str(self.task_num):
                                    captcha_token = i['data']['captcha_token']['code']

                                    if captcha_token == '':
                                        log.printYellow('No captcha token found, retrying...')
                                    else:
                                        log.printGreen(f'Successfully retreived captcha token')
                                        break
                else:
                    if service.lower() == '2captcha':
                        log.printYellow('Solving captcha via 2captcha...')
                    if service.lower() == 'capmonster':
                        log.printYellow('Solving captcha via capmonster...')
                    try:
                        captcha_token = self.solveCaptcha(captcha_api_key, service, log)
                        if type(captcha_token) is list:
                            log.printRed(f'Error solving captcha [{captcha_token}]')
                            captcha_token = ''
                    except Exception as e:
                        log.printRed(f'General error solving captcha [{e}]')
                        time.sleep(monitor_delay)
                    else:
                        log.printGreen('Solved captcha!')
                    # Capmonster or 2captcha
                time.sleep(monitor_delay)
            
            while(not submit_checkout):
                log.printYellow('Submitting billing...')
                try:
                    checkout_data = [shipping_response[0], captcha_token, profile_request, task_request]
                    checkout_response = self.submitBilling(checkout_data)
                except Exception as e:
                    log.printRed(f'Error when submitting billing -- {e}')
                else:
                    if type(checkout_response) is not list:
                        HttpResponseHandler().QueensResponse(checkout_response, log)
                        if product == 429 or product == 403:
                            if len(self.proxy_list) > 0:
                                proxy = random.choice(self.proxy_list)
                                self.session.proxies.update({'http:': proxy})
                    else:
                        if payment_method.lower() == 'cc' or payment_method.lower() == 'creditcard':
                            payment = 'Creditcard'
                        if payment_method.lower() == 'pp' or payment_method.lower() == 'paypal':
                            payment = 'Paypal'
                        try:
                            checkout_response_content = checkout_response[0]
                            checkout_success = re.findall("Order has been accepted", str(checkout_response_content))
                            log.printGreen(f"{checkout_success[0]} -- Check your email!")
                            checkout_success = True
                            """
                            if payment_method.lower() == 'cc' or payment_method.lower() == 'creditcard':
                                try:
                                    # Grab checkoout url
                                    checkout_token = re.findall("<a href=\"https://api.platebnibrana.csob.cz/api/v1.6/payment/process/M1MIPS1767/(.+?)\"", checkout_response_content)
                                    checkout_url = f"https://api.platebnibrana.csob.cz/api/v1.6/payment/process/M1MIPS1767/{checkout_token[0]}"
                                except:
                                    checkout_url = False
                            
                            if payment_method.lower() == 'pp' or payment_method.lower() == 'paypal':
                                # Handle paypal here
                                checkout_url = 'https://www.monthlybrands.com.pk/wp-content/uploads/2018/08/Check-Email.jpg'
                            """
                            submit_checkout = True
                        except:
                            log.printRed('Order failed')
                            checkout_success = False
                            product_image = product[1]
                            email = task_request.getEmail()
                            price = product[2]

                            webhook_data = [self.session, product_name, product_image[0], username, profile_name, email, payment, selected_size, 'Queens', settings['WEBHOOK'], price[0], 'Failed to complete order', 14177041, '']
                            submit_checkout = True
                        else:
                            product_image = product[1]
                            email = task_request.getEmail()
                            price = product[2]

                            webhook_data = [self.session, product_name, product_image[0], username, profile_name, email, payment, selected_size, 'Queens', settings['WEBHOOK'], price[0], 'Complete order in email!', 3066993, '']
                            if checkoutsound == 'true':
                                miscHandling().playsoundCheckout()
                            self.checkouts.increment(1)
                            ctypes.windll.kernel32.SetConsoleTitleW(f"AlphaCLI 0.2.0 | Tasks {self.amount_tasks} | Carts {self.carts.value} | Checkouts {self.checkouts.value}")
                if not submit_checkout:
                    time.sleep(monitor_delay)
                else:
                    checkout = True
        try:
            hook().sendPublicWebhook(webhook_data)
        except Exception as e:
            log.printRed(f"Error sending public webhook -- {e}")
        try:
            hook().sendPrivateWebhook(webhook_data)
        except Exception as e:
            log.printRed(f"Error sending private webhook -- {e}")
        #============== end of the module====================
        if cartsound == 'true':
            play_cart.join()

        date_time = datetime.now()
        checkout_time = date_time.strftime("%d-%m-%Y-%H:%M:%S")

        try:
            price = price[0].replace('Kč', '')
        except:
            price = 'N/A'

        return [str(checkout_time), profile_name, 'Queens', product_url, selected_size, payment, price, email, str(checkout_success), 'None', str(proxy)]
    
    def monitorItem(self):
        endpoint = 'https://www.queens.cz/air-jordan-1/'
        # Scrape all products and check for certain keywords

        # Headers
        get_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'nl-NL,nl;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
        }
        response = self.session.get(endpoint, headers=get_headers)

        if response.status_code not in range(200, 299):
            return response.status_code
        else:
            try:
                link_list = []
                source = html.fromstring(response.content)
                for item in source.xpath('//*[@id="categoryItems"]//div//a'):
                    link_list.append(item.attrib['href'])
                return link_list
            except:
                return False

    def getCountryCode(self, country):
        countries = ['cz', 'de', 'fr', 'it', 'nl', 'dk', 'ie']
        codes = ['1', '10', '16', '13', '8', '73', '36']
        
        country_code = ''
        for i in range(len(countries)):
            if country.lower() == countries[i]:
                country_code = codes[i]
        return country_code

    def findProduct(self, product_url):
        get_product_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'cache-control': 'max-age=0',
            'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'            
        }
        product_page = self.session.get(product_url, headers=get_product_headers)

        if product_page.status_code in range(200, 299):
            source = html.fromstring(product_page.content)
            product_name = source.xpath('/html/head/meta[5]/@content')
            image_url = source.xpath('//*[@id="thumb_1"]/@src')
            price = source.xpath('/html/head/meta[16]/@content')
            csrf_token = source.xpath('//*[@id="navbar-menu-links"]/div/ul/li[4]/div/form/input/@value')
            item_id = source.xpath('//*[@id="itemForm"]/input[2]/@value')
            
            # If there is no item_id then the product is not instock
            if item_id:
                # Scrape sizes
                variants = []
                sizes = []
                for z_v in source.xpath('//*[@id="variant"]//option'):
                    variants.append(z_v.attrib['value'])
                    sizes.append(z_v.text_content())
                
                return [product_name, image_url, price, csrf_token, item_id, variants, sizes]
            return [product_name, image_url, price, csrf_token, item_id]
        else:
            return product_page.status_code
    
    def parseSizes(self, product_url):
        # Only scrape the sizes
        get_product_headers = {
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
        product_page = self.session.get(product_url, headers=get_product_headers)
        
        if product_page.status_code in range(200, 299):
            source = html.fromstring(product_page.content)
            try:
                # Scraoe variant and sizes
                item_id = source.xpath('//*[@id="itemForm"]/input[2]/@value')
                variants = []
                sizes = []
                for z_v in source.xpath('//*[@id="variant"]//option'):
                    variants.append(z_v.attrib['value'])
                    sizes.append(z_v.text_content())

                return [item_id, variants, sizes]
            except:
                return False
        else:
            return product_page.status_code
    
    def addToCart(self, data):
        csrf_token = data[0]
        item_id = data[1]
        variant = data[2]
        product_url = data[3]

        # Headers 
        atc_headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-length': '500',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://www.queens.cz',
            'referer': product_url,
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }
        # Cart form data
        cart_form_data ={
            'ci_csrf_token': csrf_token,
            'variant': variant,
            'item_id': item_id,
            'quantity': '1'
        }
        atc_response = self.session.post('https://www.queens.cz/cart/add_ajax', data=cart_form_data, headers=atc_headers)

        if atc_response.status_code in range(200, 299):
            check_cart_headers = {
                'accept': '*/*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
                'referer': product_url,
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest'
            }
            # Check if the item is added to cart
            cart_response = self.session.get('https://www.queens.cz/cart/update_cart_status', headers=check_cart_headers)
            if cart_response.status_code in range(200, 299):
                source = html.fromstring(cart_response.content)
                items_cart = source.xpath('/html/body/a/span[2]/text()')
                if int(items_cart[0]) > 0:
                    return True
                else:
                    return False
            else:
                return cart_response.status_code
    
    def submitShipping(self, data):
        csrf_token = data[0]
        shipping_country = data[1]
        custom_shipping = data[2]
        payment_method = data[3]
        quantity_code = data[4]

        # Post the cart
        post_cart_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'content-length': '433',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.queens.cz',
            'referer': 'https://www.queens.cz/kosik/',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
        }
        form_data = {
            'ci_csrf_token': csrf_token,
            quantity_code: '1'
        }
        submit_cart_response = self.session.post('https://www.queens.cz/kosik/stat', data=form_data, headers=post_cart_headers)
        if submit_cart_response.status_code in range(200, 299):
            source = html.fromstring(submit_cart_response.content)
            csrf_token_shipping = source.xpath('//*[@id="navbar-menu-links"]/div/ul/li[4]/div/form/input/@value')
        else:
            return submit_cart_response.status_code
        
        # Post the shipping country
        post_country_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'content-length': '433',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.queens.cz',
            'referer': 'https://www.queens.cz/kosik/stat',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
        }
        submitcountry_data = {
            'ci_csrf_token': csrf_token_shipping[0],
            'state': shipping_country,
            'state-id': 'Jiný stát ...'
        }
        submit_country_response = self.session.post('https://www.queens.cz/kosik/doprava', data=submitcountry_data, headers=post_country_headers)
        if submit_country_response.status_code in range(200, 299):
            source = html.fromstring(submit_country_response.content)
            csrf_token_ship_method = source.xpath('//*[@id="navbar-menu-links"]/div/ul/li[4]/div/form/input/@value')

            if custom_shipping == '':
                if shipping_country == '1':
                    shipping_method = 'ppl'
                else:
                    #Scrape the shipping method
                    #shipping_method_temp = source.xpath('//*[@id="ups"]/@id')
                    #shipping_method = shipping_method_temp[0]
                    shipping_method = 'ups'
            else:
                shipping_method = custom_shipping
            
            if payment_method.lower() == 'pp' or payment_method.lower() == 'paypal':
                payment_id = 'paypal'
            if payment_method.lower() == 'cc' or payment_method.lower() == 'creditcard':
                payment_id = 'card'
        else:
            return submit_country_response.status_code
        
        # Submit shipping method and scrape the billing site
        post_submit_ship_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'content-length': '433',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.queens.cz',
            'referer': 'https://www.queens.cz/kosik/doprava',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-users': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
        }
        submit_shipping_data = {
            'ci_csrf_token': csrf_token_ship_method[0],
            'shipping': shipping_method,
            'payment': payment_id,
            'state_id': shipping_country
        }
        submit_shipping_response = self.session.post('https://www.queens.cz/kosik/udaje', data=submit_shipping_data, headers=post_submit_ship_headers)
        if submit_shipping_response.status_code in range(200, 299):
            source = html.fromstring(submit_shipping_response.content)
            csrf_token_billing = source.xpath('//*[@id="navbar-menu-links"]/div/ul/li[4]/div/form/input/@value')
            return [csrf_token_billing]
        else:
            return submit_shipping_response.status_code
    
    def submitBilling(self, data):
        csrf_token = data[0]
        recaptcha_token = data[1]
        profile_obj = data[2]
        task_obj = data[3]

        post_billing_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'content-length': '800',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.queens.cz',
            'referer': 'https://www.queens.cz/kosik/udaje',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
        }
        submitbilling_data = {
            'ci_csrf_token': csrf_token,
            'first_name': '',
            'jakobykrestnijmeno': profile_obj.getFirstName(),
            'sur_name': profile_obj.getLastName(),
            'company_name': task_obj.getCompanyName(),
            'email': task_obj.getEmail(),
            'phone': profile_obj.getPhoneNumber(),
            'street': profile_obj.getAddress1(),
            'street_number': profile_obj.getHouseNumber(),
            'city': profile_obj.getCity(),
            'zip': profile_obj.getZipcode(),
            'note': '',
            'is_terms': 'on',
            'is_paper': 'false',
            'is_newsletter': 'true',
            'recaptcha': recaptcha_token
        }
        checkout_response = self.session.post('https://www.queens.cz/kosik/dokonceni-objednavky', data=submitbilling_data, headers=post_billing_headers)
        if checkout_response.status_code in range(200, 299):
            return [checkout_response.content]
        else:
            return checkout_response.status_code
    
    def solveCaptcha(self, key, service, log):
        if service.lower() == '2captcha':
            solver = TwoCaptcha(key)
            result = solver.recaptcha(
                sitekey='6LeY38UUAAAAALoU0_zoe6vTARi9S8SDLah9a94M',
                url='https://www.queens.cz/kosik/udaje',
                data={'action': 'cart'},
                version='v3'
            )
            return result['code']
        
        if service.lower() == 'capmonster':
            createTaskData = {
                "clientKey": key,
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
                    try:
                        getResultData = {
                            'clientKey': key,
                            'taskId': json_response1['taskId']
                        }
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
                            solution = json_reponse2['solution']
            return solution['gRecaptchaResponse']