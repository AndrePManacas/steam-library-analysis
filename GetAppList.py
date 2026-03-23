import requests
import os
import json
import time
import logging
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(filename='logs/GetAppList.log',
                    format='%(asctime)s %(levelname)s: %(message)s', 
                    level=logging.DEBUG)


key = os.environ['STEAM_WEB_API_KEY']
steamID = os.environ['USER_STEAM_ID']


def get_app_list(last_appid = 0):

    have_more_results = True

    while True:
        
        payload = {
            'key': key,
            'last_appid': last_appid
        }

        logger.info(f"Calling API with last_appid {last_appid}")
        r = requests.get('https://api.steampowered.com/IStoreService/GetAppList/v1/', params=payload)

        if r.status_code != 200:
            for retry in range(1,4):
                logger.warning(f"API satus code {r.status_code}")
                logger.info(f"Sleep for 5s and try again. Retry number: {retry}/3")
                time.sleep(5)
                r = requests.get('https://api.steampowered.com/IStoreService/GetAppList/v1/', params=payload)

                if r.status_code == 200:
                    logger.info(f"succeeded to get the appList at retry {retry}/3")
                    break
            else:
                logger.fatal("Failled to get appList after 3 retries")
                sys.exit()

        json_response = r.json()

        last_appid = json_response.get('response').get('last_appid', 'last')
        have_more_results = json_response.get('response').get('have_more_results', False)

        logger.info(f"Saving json response with last appid: {last_appid}")
        with open(f"json_response/GetAppList/last_appid_{last_appid}.json",'w') as f:
            json.dump(json_response, f, indent=4)

        if have_more_results == False:
            logger.info(f"All apps have been collected last appid: {last_appid}")
            sys.exit()

if __name__ == "__main__":
    get_app_list()
