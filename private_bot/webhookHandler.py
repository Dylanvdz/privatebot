import requests
import json

class hook():

    def sendPublicWebhook(self, data):
        session = data[0]
        product_title = data[1]
        product_image = data[2]
        username = data[3]
        profile = data[4]
        email = data[5]
        payment = data[6]
        size = data[7]
        site = data[8]
        webhook_url = ''
        price = data[10]
        webhook_title = data[11]
        webhook_color = data[12]
        checkout_url = data[13]

        version = "v0.1.9.5"
        checkout = True
        if checkout == True:
            webhook_data = {
                'embeds': [
                    {
                        'title': webhook_title,
                        'color': webhook_color,
                        'fields':[
                            {
                                'name': '**Site**',
                                'value': site,
                                'inline': 'false'
                            },
                            {
                                'name': '**Product**',
                                'value': product_title,
                                'inline': 'true'
                            },
                            {
                                'name': '**Size**',
                                'value': size,
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
                                'name': '**User**',
                                'value': f'||{username}||',
                                'inline': 'false'
                            }
                        ],
                        'thumbnail': {
                            'url': product_image
                        },
                        'footer': {
                            'text': f'Alpha CLI | Private bot',
                            'icon_url': 'https://cdn.discordapp.com/attachments/759075867766030346/759075946338189382/3777a267fc46073d5c5c35709e2cbaa1.png'
                        }
                    }
                ]
            }
        
        session.post(webhook_url, data=json.dumps(webhook_data), headers={"Content-Type": "application/json"})

    def sendPrivateWebhook(self, data):
        session = data[0]
        product_title = data[1]
        product_image = data[2]
        username = data[3]
        profile = data[4]
        email = data[5]
        payment = data[6]
        size = data[7]
        site = data[8]
        webhook_url = data[9]
        price = data[10]
        webhook_title = data[11]
        webhook_color = data[12]
        checkout_url = data[13]


        version = "v0.1.9.5"

        checkout = True
        if checkout == True:
            webhook_data = {
                'embeds': [
                    {
                        'title': webhook_title,
                        'color': webhook_color,
                        'fields':[
                            {
                                'name': '**Site**',
                                'value': f"||{site}||",
                                'inline': 'false'
                            },
                            {
                                'name': '**Product**',
                                'value': product_title,
                                'inline': 'true'
                            },
                            {
                                'name': '**Size**',
                                'value': size,
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
                                'name': '**Email**',
                                'value': f'||{email}||',
                                'inline': 'false'

                            },
                            {
                                'name': '**Profile**',
                                'value': f'||{profile}||',
                                'inline': 'false'
                            }
                        ],
                        'thumbnail': {
                            'url': product_image
                        },
                        'footer': {
                            'text': f'Alpha CLI | Private bot',
                            'icon_url': 'https://cdn.discordapp.com/attachments/759075867766030346/759075946338189382/3777a267fc46073d5c5c35709e2cbaa1.png'
                        }
                    }
                ]
            }
        
        response = session.post(webhook_url, data=json.dumps(webhook_data), headers={"Content-Type": "application/json"})
        return response.status_code
    
    def sendTestWebhook(self, username, webhookurl, time):

        hook_data = {
            'embeds': [
                {
                'title': 'Test webhook',
                'description': f'{username}, your webhook is working!',
                'color': 3066993,
                'thumbnail': {
                    'url': 'https://cdn.discordapp.com/attachments/759075867766030346/759075946338189382/3777a267fc46073d5c5c35709e2cbaa1.png'
                    },
                "footer": {
                    'text': f'Alpha CLI | Test webhook - {time}',
                    'icon_url': 'https://cdn.discordapp.com/attachments/759075867766030346/759075946338189382/3777a267fc46073d5c5c35709e2cbaa1.png'
                    }
                }
            ],
        }

        response = requests.post(webhookurl, data=json.dumps(hook_data), headers={"Content-Type": "application/json"})
        if 200 <= response.status_code <= 299:
            return True
        else:
            return response.status_code