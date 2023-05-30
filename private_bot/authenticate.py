import base64
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

key_list = [b'5H_tU9kIm7tgioO7C_v1r2hvuhujkUKbPdTrOPZuDn4=', b'nuWVVzTpOVOnaGUcKWXpmbP6pGMAwymbJ88gY-tIyi8=', b'qC9PVUZvTM-f6Eslp5KCX6mtfZBV_Fsy10jSaEMnx58=', b'0zKzOWRteU1BQN5iwMWNSFO5sVF4tysL37N5tjt_D0k='
, b'EbODMSLV4pL7L_GmGPz_AfeQymXoRTH9T--sg745DqA=', b'rxAGl608yXDywN1dxtBp9dGT4Fh_iLZHNS_3HNcECh8=', b'ewU4fS_Vl5DFjgTbXFN1gxdKE3d1ZyBB_cj2mVBRoiY=', b'J52hAuhD1POommTexZ19-6ZFXywF4BsCzHi6HmhNOiQ='
, b'7p9niZUN6BwtsDEzNroGFe_GANu-YLuVEWQSQyH1WUU=', b'U5rdfreWY5pDk5ZhSCwQcLZZDsNRjMeTwQ5Vy6GidYs=']

class auth():

    def user(self, token):
        # KEY CRACK CHALLENGE
        password_provided = token
        password = password_provided.encode()
        salt = b'salty_boy_trying_to_crack_this' # Get salty 
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        key = base64.urlsafe_b64encode(kdf.derive(password))
        if key in key_list:
            return True
        else:
            return False