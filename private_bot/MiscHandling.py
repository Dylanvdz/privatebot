import time
import threading

from pypresence import Presence
from requestData import requestRunData
from playsound import playsound

"""
This class handles all misc stuff like rich presence, title bar for tasks/carts/checkouts and so on...
"""
class miscHandling():

    def displayRPC(self, version):
        client_id = ''
        RPC = Presence(client_id)
        RPC.connect()
        RPC.update(large_image='wolf', large_text=f'AlphaCLI', state=f'AlphaCLI {version}', start=int(time.time()))
    
    def playsoundCart(self):
        try:
            playsound('misc/cart.wav')
        except:
            pass

    def playsoundCheckout(self):
        try:
            playsound('misc/checkout.mp3')
        except:
            pass