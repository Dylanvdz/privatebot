from customLogging import Clogging

class HttpResponseHandler():

    def QueensResponse(self, response_code, log):
        # Handle 4xx client errors
        if response_code == 400:
            log.printRed("Error bad request getting page...")
            return
        if response_code == 403:
            log.printRed("Proxy banned, rotating...")
            return
        if response_code == 404:
            log.printRed("404 product page not found, retying...")
            return
        if response_code == 429:
            log.printYellow("Proxy rate limited, rotating...")
            return
        elif 400 <= response_code <= 499:
            log.printRed(f"Client error, response code {response_code}")
            return
        
        # Handle 5xx server errors
        if response_code == 502:
            log.printYellow("Server error, bad gateway...")
        if response_code == 504:
            log.printYellow("Server overload, gateway timeout...")
        elif 500 <= response_code <= 599:
            log.printRed(f"Server error, response code {response_code}...")