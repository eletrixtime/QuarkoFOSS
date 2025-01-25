'''
QuarkoFOSS - Main

This is the original Quarko code
Under the MIT license a copy is available in the LICENSE file

(some code is changed for privacy reasons.. (tokens etc))
'''


import requests
import config

LINK =  config.WEBHOOK_LOG_URL

def send_log_webhook(title,text,color="5814783"):
    embed = {
        "title": title,
        "description": text,
        "color": color
    }
    payload = {"embeds": [embed]}
    r = requests.post(url=LINK,json=payload)
    print(r.text)