import ctypes
import requests
import time
import threading
import time
import threading
import json
import random
import re

from datetime import datetime
from lxml import html, etree
from requestData import requestProfileData, requestTaskData
from customLogging import Clogging
from httpResponseHandler import HttpResponseHandler
from MiscHandling import miscHandling
from loadCredentials import load
from webhookHandler import hook
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class Ldlc():

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

        productid = task_request.getProductUrl()

        if "https://www.ldlc.com" in productid:
            product_url = productid
            product_id_temp = re.search("https://www.ldlc.com/fiche/(.*).html", productid)
            productid = product_id_temp.group(1)
        else:
            product_url = f'https://www.ldlc.com/fiche/{productid}.html'

        account_email = task_request.getEmail()
        account_password = task_request.getPassword()

        payment_method = task_request.getPayment()
        shipping_method = task_request.getCustomShipping()
        profile_name = task_request.getProfile()

        if account_email == '' or account_password == '':
            log.printRed('Account details empty!')

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
            #self.session.proxies.update({'http': proxy, 'https': proxy})
            self.session.proxies = {'http': proxy, 'https': proxy}

        # Load settings
        settings = self.settings
        username = settings['USERNAME']
        delay = int(settings['DELAY'])/1000
        monitor_delay = int(settings["MONITOR_DELAY"])/1000
        service = settings['CAPTCHA_SERVICE']
        cartsound = settings['CART_SOUND']
        checkoutsound = settings['CHECKOUT_SOUND']

        # If cartsound is True make extra threadto play sound in
        if cartsound == 'true':
            play_cart = threading.Thread(target=miscHandling().playsoundCart)
            play_checkout = threading.Thread(target=miscHandling().playsoundCheckout)
        
        productfound = False
        logged_in = False
        carted = False
        checkout = False
        while(not checkout):
            # Log in to account
            while(not logged_in):
                try:
                    req_token = self.scrapeLogin()
                except Exception as e:
                    log.printRed(f'Unexpected error opening login page -- {e}')
                    log.printYellow('Setting up new session...')
                    self.session = requests.Session()
                    if len(self.proxy_list) > 0:
                        proxy = self.proxy_list[0]
                        #self.session.proxies.update({'http': proxy, 'https': proxy})
                        self.session.proxies = {'http': proxy, 'https': proxy}
                except ConnectionError:
                    log.printRed('Connection error!')
                else:
                    if type(req_token) is not list:
                        HttpResponseHandler().QueensResponse(req_token, log)
                        if req_token == 429 or req_token == 403:
                            self.session = requests.Session()
                            if len(self.proxy_list) > 0:
                                proxy = random.choice(self.proxy_list)
                                self.session.proxies.update({'http:': proxy})
                    else:
                        log.printYellow('Logging in...')
                        # Login to account
                        try:
                            login_success = self.loginAccount(req_token[0], account_email, account_password, product_url)
                        except ConnectionError:
                            log.printRed(f'Connection error!')
                        except Exception as e:
                            log.printRed(f'Unexpected error logging in!')
                        else:
                            if type(login_success) is not bool:
                                if login_success == 400 or login_success == 403:
                                    log.printRed('Wrong login credentials!')
                                else:
                                    HttpResponseHandler().QueensResponse(login_success, log)
                            else:
                                if login_success == False:
                                    log.printRed('Wrong login credentials!')
                                logged_in = login_success
                if not logged_in:
                    time.sleep(monitor_delay)
            log.printGreen('Logged in!')

            log.printYellow('Parsing product page...')
            while(not carted):
                while(not productfound):
                    # Parse product
                    try:
                        product_info = self.parseProduct(product_url)
                    except Exception as e:
                        log.printRed(f'Unexpected error parsing product -- {e}')
                    except ConnectionError:
                        log.printRed('Connection error!')
                    else:
                        if type(product_info) is not list:
                            HttpResponseHandler().QueensResponse(product_info, log)
                            if req_token == 429 or req_token == 403:
                                log.printYellow('Rotating proxy...')
                                if len(self.proxy_list) > 0:
                                    proxy = random.choice(self.proxy_list)
                                    self.session.proxies.update({'http:': proxy})
                        else:
                            product_id = product_info[0]
                            title = product_info[1]
                            product_image = product_info[2]
                            price = product_info[3]
                            log.printGreen(f'Found product -- {title}')
                            productfound = True
                    if not productfound:
                        time.sleep(monitor_delay)

                log.printYellow(f'Adding {title} to cart...')
                try:
                    cart_success = self.addProductToCart(product_id, product_url)
                except Exception as e:
                    log.printRed(f'Unexpected error adding to cart -- {e}')
                except ConnectionError:
                    log.printRed('Connection error!')
                else:
                    if type(cart_success) is not bool:
                        HttpResponseHandler().QueensResponse(cart_success, log)
                        if req_token == 429 or req_token == 403:
                            log.printYellow('Rotating proxy...')
                            if len(self.proxy_list) > 0:
                                proxy = random.choice(self.proxy_list)
                                self.session.proxies.update({'http:': proxy})
                    else:
                        if not cart_success:
                            log.printRed('Add to cart failed, retrying...')
                        carted = cart_success
                if not carted:
                    time.sleep(monitor_delay)
            
            # Handle cart sound etc
            log.printGreen('Added to cart!')
            if cartsound == 'true':
                play_cart.start()
            self.carts.increment(1)
            ctypes.windll.kernel32.SetConsoleTitleW(f"AlphaCLI 0.2.0 | Tasks {self.amount_tasks} | Carts {self.carts.value} | Checkouts {self.checkouts.value}")
            
            submit_delivery = False
            while(not submit_delivery):
                log.printYellow('Submitting delivery...')
                try:
                    response_delivery = self.goToDelivery()
                except Exception as e:
                    log.printRed(f'Unexpected error submitting delivery (1) -- {e}')
                except ConnectionError:
                    log.printRed('Connection error!')
                else:
                    if type(response_delivery) is not bool:
                        HttpResponseHandler().QueensResponse(response_delivery, log)
                        if response_delivery == 429 or response_delivery == 403:
                            log.printYellow('Rotating proxy...')
                            if len(self.proxy_list) > 0:
                                proxy = random.choice(self.proxy_list)
                                self.session.proxies.update({'http:': proxy})
                    else:
                        if response_delivery:
                            try:
                                response_submit_delivery = self.submitDelivery(shipping_method)
                            except Exception as e:
                                log.printRed(f'Unexpected error submitting delivery (2) -- {e}')
                            except ConnectionError:
                                log.printRed('Connection error!')
                            else:
                                if type(response_submit_delivery) is not bool:
                                    HttpResponseHandler().QueensResponse(response_delivery, log)
                                    if response_delivery == 429 or response_delivery == 403:
                                        log.printYellow('Rotating proxy...')
                                        if len(self.proxy_list) > 0:
                                            proxy = random.choice(self.proxy_list)
                                            self.session.proxies.update({'http:': proxy})
                                else:
                                    if not response_submit_delivery:
                                        log.printRed('Failed to submit delivery, retrying...')
                                    submit_delivery = response_submit_delivery
                if not submit_delivery:
                    time.sleep(monitor_delay)
            
            # Handle payment types
            if payment_method.lower() == 'bank':
                payment_id = '260008'
            if payment_method.lower() == 'paypal' or payment_method.lower() == 'pp':
                payment_id = '260062'
            if payment_method.lower() == 'creditcard' or payment_method.lower() == 'cc':
                payment_id = '260014'
            # Default paypal if there is no payment type defined
            if payment_method == '':
                payment_id = '260062'

            submit_payment = False
            while(not submit_payment):
                log.printYellow('Submitting payment...')
                try:
                    submit_payment_response = self.submitPayment(payment_id)
                except Exception as e:
                    log.printRed(f'Unexpected error submitting payment -- {e}')
                except ConnectionError:
                    log.printRed('Connection error!')
                else:
                    if type(submit_payment_response) is not bool:
                        HttpResponseHandler().QueensResponse(submit_payment_response, log)
                        if submit_payment_response == 429 or submit_payment_response == 403:
                            log.printYellow('Rotating proxy...')
                            if len(self.proxy_list) > 0:
                                proxy = random.choice(self.proxy_list)
                                self.session.proxies.update({'http:': proxy})
                    else:
                        if not submit_payment_response:
                            log.printRed('Failed to submit payment, retrying...')
                        submit_payment = submit_payment_response
                if not submit_payment:
                    time.sleep(monitor_delay)
            
            submit_order = False
            while(not submit_order):
                log.printYellow('Submitting order...')
                try:
                    submit_order_response = self.submitOrder(payment_id, profile_request)
                except Exception as e:
                    log.printRed(f'Unexpected error submitting order -- {e}')
                except ConnectionError:
                    log.printRed('Connection error!')
                else:
                    if type(submit_order_response) is not list:
                        HttpResponseHandler().QueensResponse(submit_order_response, log)
                        if submit_order_response == 429 or submit_order_response == 403:
                            log.printYellow('Rotating proxy...')
                            if len(self.proxy_list) > 0:
                                proxy = random.choice(self.proxy_list)
                                self.session.proxies.update({'http:': proxy})
                    else:
                        if not submit_order_response[0]:
                            log.printRed('Failed to submit order, retrying...')
                        submit_order = submit_order_response[0]
                if not submit_order:
                    time.sleep(monitor_delay)
            checkout = True
        
        if payment_method.lower() == 'creditcard' or payment_method.lower() == 'cc':
            log.printGreen('Successfully submitted creditcard order!')
        else:
            log.printGreen('Successfully submitted order!')
        if checkoutsound == 'true':
            play_checkout.start()
            self.checkouts.increment(1)
        ctypes.windll.kernel32.SetConsoleTitleW(f"AlphaCLI 0.2.0 | Tasks {self.amount_tasks} | Carts {self.carts.value} | Checkouts {self.checkouts.value}")
        
        try:
            confirmation_url = f'https://secure2.ldlc.com{submit_order_response[1]}'
        except:
            confirmation_url = 'https://secure2.ldlc.com'
        
        if payment_method.lower() == 'paypal' or payment_method.lower() == 'pp' or payment_method == '':
            payment_method = 'Paypal'
            confirmation_url = submit_order_response[1]
        if payment_method.lower() == 'bank':
            payment_method = 'Bank'
            try:
                confirmation_url = f'https://secure2.ldlc.com{submit_order_response[1]}'
            except:
                confirmation_url = 'https://secure2.ldlc.com'
        if payment_method.lower() == 'creditcard' or payment_method.lower() == 'cc':
            payment_method = 'Creditcard'
            if len(submit_order_response) > 1:
                log.printGreen('Confirm 3ds payment...')
                confirmation_url = submit_order_response[1]

                options = webdriver.ChromeOptions()
                options.add_experimental_option('excludeSwitches', ['enable-logging'])

                #chrome_options = Options()
                #chrome_options.add_argument("--log-level=3")
                driver = webdriver.Chrome('D:/Code/alphacli_v0.2.2/misc/chromedriver', chrome_options=options)
                driver.get(confirmation_url)
            else:
                confirmation_url = False
            
        try:
            private_webhook = [title, product_image, payment_method, price, productid, confirmation_url, account_email]
            self.privateWebhook(private_webhook)

            public_webhook = [title, product_image, payment_method, price, productid, product_url, username, confirmation_url]
            self.public_webhook(public_webhook)
        except Exception as e:
            print(e)

        if cartsound == 'true':
            play_cart.join()
            play_checkout.join()
        
        date_time = datetime.now()
        checkout_time = date_time.strftime("%d-%m-%Y-%H:%M:%S")

        if len(self.proxy_list) == 0:
            proxy = 'Localhost'
        
        return[str(checkout_time), account_email, 'LDLC', product_url, '', payment_method, price, account_email, 'True', confirmation_url, str(proxy)]

    def scrapeLogin(self):
        # This function scrapes the login page for the request token
        get_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'en-US,en;q=0.9',
            'connection': 'keep-alive',
            'host': 'secure2.ldlc.com',
            'referer': 'https://www.ldlc.com/',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-site',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'
        }
        response_login_page = self.session.get('https://secure2.ldlc.com/fr-fr/Login/Login?returnUrl=/fr-fr/Account', headers=get_headers)

        if response_login_page.status_code in range(200, 299):
            req_verf_token = re.findall('input name="__RequestVerificationToken" type="hidden" value="(.+?)" /><input id', response_login_page.text)[0]
            return [req_verf_token]
        else:
            return response_login_page.status_code
    
    def loginAccount(self, req_token, account_email, account_password, product_link):
        # This function posts the login 
        post_login_header = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://secure2.ldlc.com',
            'pragma': 'no-cache',
            'referer': 'https://secure2.ldlc.com/fr-fr/Login/Login?returnUrl=/fr-fr/Account',
            'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'
        }
        login_data = {
            '__RequestVerificationToken': req_token,
            'VerificationToken': '0178eb995dd0-7a5a8abb67e13749d3a16be03548dba965e02d5a89bb67e02d5a88bb67e12d5a8fbb67e52d5a8ebb67e1394a96',
            'Email': account_email,
            'Password': account_password,
            'LongAuthenticationDuration': 'false'
        }
        response_login = self.session.post('https://secure2.ldlc.com/fr-fr/Login/Login?returnUrl=/fr-fr/Account', data=login_data, headers=post_login_header)

        if response_login.status_code in range(200, 299):
            get_account_header = {
                'accept': '*/*',
                'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
                'cache-control': 'no-cache',
                'pragma': 'no-cache',
                'referer': product_link,
                'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest'
            }
            account_info = self.session.get('https://www.ldlc.com/v4/fr-fr/header/user', headers=get_account_header)

            if account_info.status_code in range(200, 299):
                login_json = json.loads(account_info.content)
                return login_json['login']
            else:
                return account_info.status_code
        else:
            return response_login.status_code
    
    def parseProduct(self, product_link):
        get_product_page = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://secure2.ldlc.com',
            'pragma': 'no-cache',
            'referer': 'https://secure2.ldlc.com/fr-fr/Login/Login?returnUrl=/fr-fr/Account',
            'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'
        }
        response_product = self.session.get(product_link, headers=get_product_page)

        if response_product.status_code in range(200, 299):
            source = html.fromstring(response_product.content)
            product_id = source.xpath('//*[@id="product-page-price"]/div[2]/a[1]/@data-product-id')[0]
    
            try:
                title_temp = source.xpath('/html/head/title/text()')[0]
                title = title_temp.split('-')[0]
            except:
                title = 'Product name'
            
            try:
                product_image = source.xpath('//*[@id="activeOffer"]/div[2]/div[1]/div[2]/div/div[1]/div[1]/a/img/@src')[0]
            except:
                product_image = 'https://st4.depositphotos.com/14953852/24787/v/600/depositphotos_247872612-stock-illustration-no-image-available-icon-vector.jpg'

            try:
                price = source.xpath('//*[@id="activeOffer"]/div[2]/div[3]/aside/div[1]/div/text()')[0]
            except:
                price = 'N/A'

            return [product_id, title, product_image, price]
        else:
            return response_product.status_code
    
    def addProductToCart(self, product_id, product_link):
        get_header = {
            'accept': '*/*',
            'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'referer': product_link,
            'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }
        atc_link = f'https://www.ldlc.com/v4/fr-fr/cart/add/offer/{product_id}/1/0'
        response_cart = self.session.get(atc_link, headers=get_header)

        if response_cart.status_code in range(200, 299):
            account_info = self.session.get('https://www.ldlc.com/v4/fr-fr/header/user', headers=get_header)
            if account_info.status_code in range(200, 299):
                login_json = json.loads(account_info.content)
                if login_json['cartItemCount'] == 1:
                    return True
                else:
                    return False
            else:
                return account_info.status_code
        else:
            return response_cart.status_code
    
    def goToDelivery(self):
        # Submit delivery, which is presaved in the account
        post_delivery_headers = {
            'accept': '*/*',
            'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://secure2.ldlc.com',
            'pragma': 'no-cache',
            'referer': 'https://secure2.ldlc.com/fr-fr/Cart',
            'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }
        form_data = {
            'X-Requested-With': 'XMLHttpRequest'
        }
        response_delivery = self.session.post('https://secure2.ldlc.com/fr-fr/Cart/GoNextStep?url=/fr-fr/DeliveryPayment', data=form_data, headers=post_delivery_headers)

        if response_delivery.status_code in range(200, 299):
            # Check if the cart has a pack, if that is the case delete it from the cart
            pack_response_json = json.loads(response_delivery.content)
            try:
                if pack_response_json['AlertType'] == 'PackService':
                    # Remove pack from cart
                    self.session.post('https://secure2.ldlc.com/fr-fr/Cart/RemovePackService')
                response_delivery = self.session.post('https://secure2.ldlc.com/fr-fr/Cart/GoNextStep?url=/fr-fr/DeliveryPayment', data=form_data, headers=post_delivery_headers)
                if response_delivery.status_code not in range(200, 299):
                    return response_delivery.status_code
                else:
                    return True
            except:
                return True
        else:
            return response_delivery.status_code
    
    def submitDelivery(self, shipping_method):
        # Get payment page
        get_delivery_page_header = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://secure2.ldlc.com',
            'pragma': 'no-cache',
            'referer': 'https://secure2.ldlc.com/fr-fr/Cart',
            'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'
        }
        deliveryPayment_page = self.session.get('https://secure2.ldlc.com/fr-fr/DeliveryPayment', headers=get_delivery_page_header)
        if deliveryPayment_page.status_code in range(200, 299):
            try:
                source_payment_page = html.fromstring(deliveryPayment_page.content)
                
                address_token = source_payment_page.xpath('//*[@id="deliveryModeClassicSelectionForm"]/input[1]/@value')[0]

                if shipping_method.lower() == 'chronopost':
                    delivery_id = '370008'
                if shipping_method.lower() == 'standard':
                    delivery_id = '370001'
                if shipping_method.lower() == 'delivery europe':
                    delivery_id = '370002'
                if shipping_method.lower() == '':
                    for dm in source_payment_page.xpath('//*[@id="deliveryModeClassicSelectionForm"]//div//input'):
                        delivery_id = dm.attrib['data-mode-id']
                        break
            except:
                return False
            else:
                # Post the delivery opetion
                post_delivery_headers = {
                    'accept': '*/*',
                    'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
                    'cache-control': 'no-cache',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'origin': 'https://secure2.ldlc.com',
                    'pragma': 'no-cache',
                    'referer': 'https://secure2.ldlc.com/fr-fr/DeliveryPayment',
                    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }
                delivery_data = {
                    '__RequestVerificationToken': address_token,
                    'SelectedDeliverySlotId': '', 
                    'SelectedDeliveryModeId': delivery_id,
                    'X-Requested-With': 'XMLHttpRequest'
                }
                post_delivery_response = self.session.post('https://secure2.ldlc.com/fr-fr/DeliveryPayment/SetDeliveryMode', data=delivery_data, headers=post_delivery_headers)
                if post_delivery_response.status_code not in range(200, 299):
                    return post_delivery_response
                else:
                    return True
        else:
            return deliveryPayment_page.status_code
    
    def submitPayment(self, payment_id):
        # Request the delivery page again to scrape the payment tokens
        get_delivery_page_header = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://secure2.ldlc.com',
            'pragma': 'no-cache',
            'referer': 'https://secure2.ldlc.com/fr-fr/Cart',
            'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'
        }
        response_deliveryPayment_page = self.session.get('https://secure2.ldlc.com/fr-fr/DeliveryPayment', headers=get_delivery_page_header)

        if response_deliveryPayment_page.status_code in range(200, 299):
            payment_token = ''
            try:
                source_payment_page = html.fromstring(response_deliveryPayment_page.content)

                payment_methods = []
                payment_tokens = []
                for payment_m in source_payment_page.xpath('//*[@id="payment"]/div[2]//div//form//div//div//input'):
                    payment_methods.append(payment_m.attrib['value'])
                for payment_t in source_payment_page.xpath('//*[@id="payment"]/div[2]//div//form//input'):
                    if payment_t.attrib['name'] == '__RequestVerificationToken':
                        payment_tokens.append(payment_t.attrib['value'])

                for i in range(len(payment_methods)):
                    if payment_methods[i] == payment_id:
                        payment_token = payment_tokens[i]
                if payment_token == '':
                    return False
            except:
                return False
            else:
                post_payment_headers = {
                    'accept': '*/*',
                    'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
                    'cache-control': 'no-cache',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'origin': 'https://secure2.ldlc.com',
                    'pragma': 'no-cache',
                    'referer': 'https://secure2.ldlc.com/fr-fr/DeliveryPayment',
                    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }
                payment_data = {
                    '__RequestVerificationToken': payment_token,
                    'SelectedPaymentModeId': payment_id,
                    'X-Requested-With': 'XMLHttpRequest'
                }
                payment_response = self.session.post('https://secure2.ldlc.com/fr-fr/DeliveryPayment/SetPaymentMode', data=payment_data, headers=post_payment_headers)
                if payment_response.status_code in range(200, 299):
                    return True
                else:
                    return payment_response.status_code
        else:
            return response_deliveryPayment_page.status_code
    
    def submitOrder(self, payment_id, profile_request):
        # Request delivery page again to get the submit order token
        get_delivery_page_header = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://secure2.ldlc.com',
            'pragma': 'no-cache',
            'referer': 'https://secure2.ldlc.com/fr-fr/Cart',
            'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'
        }
        response_deliveryPayment_page = self.session.get('https://secure2.ldlc.com/fr-fr/DeliveryPayment', headers=get_delivery_page_header)
        if response_deliveryPayment_page.status_code in range(200, 299):
            try:
                source = html.fromstring(response_deliveryPayment_page.content)
                submit_order_token = source.xpath('//*[@id="form5"]/input[1]/@value')[0]
                cart_type = source.xpath('//*[@id="CartType"]/@value')[0]
            except:
                return [False]
            else:
                if payment_id == '260008':
                    order_data = {
                        '__RequestVerificationToken': submit_order_token,
                        'CartType': cart_type,
                        'Id': payment_id,
                        'ExistingOrderId': '', 
                        'GeneralTermsOfSaleAccepted': 'true',
                        'ShippingPassTermsOfSaleAccepted': 'True',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                    order_link = 'https://secure2.ldlc.com/fr-fr/StandardPayment/Order'
                if payment_id == '260062':
                    order_data = {
                        '__RequestVerificationToken': submit_order_token,
                        'CartType': cart_type,
                        'Id': payment_id,
                        'UnsettledInstalmentsOrderIdSage': '', 
                        'GeneralTermsOfSaleAccepted': 'true',
                        'ShippingPassTermsOfSaleAccepted': 'True',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                    order_link = 'https://secure2.ldlc.com/fr-fr/Paypal/Order'

                if payment_id == '260014':
                    cc_number = profile_request.getCCNumber()
                    cc_month = profile_request.getCCMonth()
                    cc_year = profile_request.getCCYear()
                    cc_cvv = profile_request.getCvv()
                    first_name = profile_request.getFirstName()
                    last_name = profile_request.getLastName()
                    exp_year = f"20{cc_year}"
                    
                    try:
                        req_token = self.check3DSForced()
                    except:
                        return [False]

                    order_data = {
                        '__RequestVerificationToken': req_token,
                        'CartType': 'SessionCart',
                        'Id': '260014',
                        'ExistingOrderId': '', 
                        'UnsettledInstalmentsOrderIdSage': '', 
                        'CardNumber': cc_number,
                        'ExpirationDate': f'{cc_month}/{cc_year}',
                        'ExpirationMonth': cc_month,
                        'ExpirationYear': exp_year,
                        'OwnerName': f'{first_name} {last_name}',
                        'Cryptogram': cc_cvv,
                        'GeneralTermsOfSaleAccepted': 'true',
                        'ShippingPassTermsOfSaleAccepted': 'True',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                    order_link = 'https://secure2.ldlc.com/fr-fr/Sips/Order'

                post_order_headers = {
                    'accept': '*/*',
                    'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
                    'cache-control': 'no-cache',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'origin': 'https://secure2.ldlc.com',
                    'pragma': 'no-cache',
                    'referer': 'https://secure2.ldlc.com/fr-fr/DeliveryPayment',
                    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
                }
                submit_order_response = self.session.post(order_link, data=order_data, headers=post_order_headers)

                if submit_order_response.status_code not in range(200, 299):
                    return submit_order_response.status_code
                else:
                    try:
                        order_confirmation = json.loads(submit_order_response.content)
                        redirectUrl = order_confirmation['redirectUrl']
                    except:
                        return [True]
                    else:
                        return [True, redirectUrl]
        else:
            return response_deliveryPayment_page.status_code
    
    def check3DSForced(self):
        # Request the delivery page again to scrape the payment tokens
        get_delivery_page_header = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://secure2.ldlc.com',
            'pragma': 'no-cache',
            'referer': 'https://secure2.ldlc.com/fr-fr/Cart',
            'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'
        }
        response_delivery_page = self.session.get('https://secure2.ldlc.com/fr-fr/DeliveryPayment', headers=get_delivery_page_header)
        
        if response_delivery_page.status_code not in range(200, 299):
            return response_delivery_page.status_code
        else:
            source = html.fromstring(response_delivery_page.content)
            for a in source.xpath('//*[@id="payment"]/div[2]//div//div//div//input'):
                if a.attrib['name'] == '__RequestVerificationToken':
                    req_token = a.attrib['value']
            return req_token
            
            """
            post_forced_3ds = {
                    'accept': '*/*',
                    'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
                    'cache-control': 'no-cache',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'origin': 'https://secure2.ldlc.com',
                    'pragma': 'no-cache',
                    'referer': 'https://secure2.ldlc.com/fr-fr/DeliveryPayment',
                    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest'
            }
            secure3d_data = {
                '__RequestVerificationToken': req_token,
                'CartType': 'SessionCart',
                'Id': '260014',
                'ExistingOrderId': ''
                'UnsettledInstalmentsOrderIdSage': ''
            }
            reponse_forced_3ds = self.session.post('https://secure2.ldlc.com/fr-fr/Sips/PartialSecure3DOption')
            """

    def privateWebhook(self, data):
        privatewebhook = self.settings['WEBHOOK']
        title = data[0]
        image = data[1]
        payment = data[2]
        price = data[3]
        pid = data[4]
        conf_link = data[5]
        account = data[6]

        if payment == 'Paypal':
            webhook_title = 'COMPLETE PAYPAL CHECKOUT!'
        if payment == 'Creditcard':
            webhook_title = 'CONFIRM 3DS PAYMENT!'
        if conf_link == False:
            conf_link = ''
            webhook_title = 'SUCCESSFUL CHECKOUT'
        else:
            webhook_title = 'ORDER COMPLETED!'
        webhook_data = {
            'embeds': [
                {
                    'title': webhook_title,
                    'url': conf_link,
                    'color': 3066993,
                    'fields': [
                        {
                            'name': '**Site**',
                            'value': '||LDLC||',
                            'inline': 'false'
                        },
                        {
                            'name': '**Product**',
                            'value': title,
                            'inline': 'false'
                        },
                        {
                            'name': '**PID**',
                            'value': pid,
                            'inline': 'false'
                        },
                        {
                            'name': '**Payment**',
                            'value': payment,
                            'inline': 'true'
                        },
                        {
                            'name': '**Price**',
                            'value': price,
                            'inline': 'true'
                        },
                        {
                            'name': '**Account**',
                            'value': f'||{account}||',
                            'inline': 'false'
                        }
                    ],
                    'thumbnail': {
                        'url': image
                    },
                    'footer' : {
                        'text': f'Alpha CLI | Private bot',
                        'icon_url': 'https://cdn.discordapp.com/attachments/759075867766030346/759075946338189382/3777a267fc46073d5c5c35709e2cbaa1.png'
                    }
                }
            ]
        }

        session = requests.Session()
        session.post(privatewebhook, data=json.dumps(webhook_data), headers={"Content-Type": "application/json"})
    
    def public_webhook(self, data):
        webhook_url = ''
        title = data[0]
        image = data[1]
        payment = data[2]
        price = data[3]
        pid = data[4]
        product_url = data[5]
        username = data[6]
        conf_link = data[7]

        if payment == 'Creditcard':
            webhook_title = 'CHECKOUT - 3DS REQUIRED'
        if conf_link == False:
            conf_link = ''
            webhook_title = 'SUCCESSFUL CHECKOUT'
        else:
            webhook_title = 'ORDER COMPLETED!'
        webhook_data = {
            'embeds': [
                {
                    'title': webhook_title,
                    'url': product_url,
                    'color': 3066993,
                    'fields': [
                        {
                            'name': '**Site**',
                            'value': 'LDLC',
                            'inline': 'false'
                        },
                        {
                            'name': '**Product**',
                            'value': title,
                            'inline': 'false'
                        },
                        {
                            'name': '**PID**',
                            'value': pid,
                            'inline': 'false'
                        },
                        {
                            'name': '**Payment**',
                            'value': payment,
                            'inline': 'true'
                        },
                        {
                            'name': '**Price**',
                            'value': price,
                            'inline': 'true'
                        },
                        {
                            'name': '**Username**',
                            'value': f'||{username}||',
                            'inline': 'false'
                        }
                    ],
                    'thumbnail': {
                        'url': image
                    },
                    'footer' : {
                        'text': f'Alpha CLI | Private bot',
                        'icon_url': 'https://cdn.discordapp.com/attachments/759075867766030346/759075946338189382/3777a267fc46073d5c5c35709e2cbaa1.png'
                    }
                }
            ]
        }

        session = requests.Session()
        response = session.post(webhook_url, data=json.dumps(webhook_data), headers={"Content-Type": "application/json"})