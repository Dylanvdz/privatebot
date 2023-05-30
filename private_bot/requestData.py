
class requestProfileData():
    # Request the data from profiles
    def __init__(self, data):
        self.r_profile_name = data[0]
        # Billing information
        self.r_first_name = data[1]
        self.r_last_name = data[2]
        self.r_phone_number = data[3]
        self.r_address_1 = data[4]
        self.r_address_2 = data[5]
        self.r_house_number = data[6]
        self.r_city = data[7]
        self.r_state = data[8]
        self.r_zipcode = data[9]
        self.r_country = data[10]

        # Creditcard information
        self.r_cc_type = data[11]
        self.r_cc_number = data[12]
        self.r_cc_month = data[13]
        self.r_cc_year = data[14]
        self.r_cc_cvv = data[15]
    
    def getProfileName(self):
        return self.r_profile_name
    
    def getFirstName(self):
        return self.r_first_name
    
    def getLastName(self):
        return self.r_last_name
    
    def getPhoneNumber(self):
        return self.r_phone_number
    
    def getAddress1(self):
        return self.r_address_1
    
    def getAddress2(self):
        return self.r_address_2
    
    def getHouseNumber(self):
        return self.r_house_number

    def getCity(self):
        return self.r_city
    
    def getState(self):
        return self.r_state
    
    def getZipcode(self):
        return self.r_zipcode
    
    def getCountry(self):
        return self.r_country
    
    def getCCType(self):
        return self.r_cc_type
    
    def getCCNumber(self):
        return self.r_cc_number
    
    def getCCMonth(self):
        return self.r_cc_month
    
    def getCCYear(self):
        return self.r_cc_year
    
    def getCvv(self):
        return self.r_cc_cvv

class requestTaskData():
    # Request the data from tasks
    def __init__(self, data):
        # General task information
        self.r_profile = data[0]
        self.r_region = data[1]
        self.r_mode = data[2]
        self.r_product_url = data[3]
        self.r_pid = data[4]
        self.r_preload = data[5]
        self.r_size = data[6]
        self.r_email = data[7]
        self.r_password = data[8]
        self.r_payment = data[9]
        self.r_custom_shipping = data[10]
        self.r_company_name = data[11]
        self.r_discount_code = data[12]
        self.r_custom_1 = data[13]
        self.r_harvester = data[14]
    
    def getProfile(self):
        return self.r_profile
    
    def getRegion(self):
        return self.r_region
    
    def getMode(self):
        return self.r_mode
    
    def getProductUrl(self):
        return self.r_product_url
    
    def getPid(self):
        return self.r_pid
    
    def getPreload(self):
        return self.r_preload
    
    def getSize(self):
        return self.r_size
    
    def getEmail(self):
        return self.r_email
    
    def getPassword(self):
        return self.r_password

    def getPayment(self):
        return self.r_payment
    
    def getCustomShipping(self):
        return self.r_custom_shipping
    
    def getCompanyName(self):
        return self.r_company_name
    
    def getDiscountCode(self):
        return self.r_discount_code
    
    def getCustom1(self):
        return self.r_custom_1

    def getHarvester(self):
        return self.r_harvester
        
class requestRunData():
    def __init__(self, data):
        self.r_amount_tasks = data[0]
        self.r_amount_carts = data[1]
        self.r_amount_checkouts = data[2]