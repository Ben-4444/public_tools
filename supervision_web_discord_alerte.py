#!/bin/python3
from time import sleep
import requests
from requests.exceptions import Timeout


def get_msg_alert(WEBHOOK,ip,alias):
    data = {
        "username" : "ALERT",
        "avatar_url" : "",
    }

    try :
        r = requests.get(ip,timeout=1)
        #print('pc on')
        #data["content"] = f"<@id_user> Site {alias} OK"
        #requests.post(WEBHOOK, json = data)

    except :
        #print('The request timed out')
        data["content"] = f"<@id_user> \nSite {alias} DOWN !\nurl : {ip}"
        requests.post(WEBHOOK, json = data)
        sleep(240)
        try :
            r = requests.get(ip,timeout=1)
            #print('pc on')
            data["content"] = f"<@id_user> Site {alias} revenu OK"
            requests.post(WEBHOOK, json = data)
        except :
            data["content"] = f"<@id_user> \nSite {alias} DOWN !\nurl : {ip}"
            requests.post(WEBHOOK, json = data)



url_webhook = [
    "",
    ""
]

ip = [
    "",
    ""
]

alias = [
    "",
    ""
]

for i in range(len(ip)) :
    #print(url_webhook[i],ip[i])
    get_msg_alert(url_webhook[i],ip[i],alias[i])
