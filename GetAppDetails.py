import requests
import json
import re
import os
import time
import sys
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('logs/GetAppDetails.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))

logger.addHandler(file_handler)
logger.addHandler(console_handler)

app_list_folder = os.environ['GET_APP_LIST_FOLDER']

app_details_folder = os.environ['GET_APP_DETAILS_FOLDER']
app_details_folder_fail = os.environ['GET_APP_DETAILS_FOLDER_FAIL']

completed_file = f"{app_details_folder}/completed.txt"

def main():

    app_list_files = sorted(os.listdir(app_list_folder), key=extract_num)

    if os.path.exists(completed_file):
        lines = open(completed_file).read().splitlines()
        completed = set(lines[:-1])  
    else:
        completed = set()

    for file in app_list_files:
        logger.info(f"-------- Get appids for file {file} --------")
        appids = get_appids(file)

        for appid in appids:

            if str(appid) in completed:
                logger.info(f"Skipping appid {appid}, already completed")
                continue

            logger.info(f"Get app details for appid {appid}")
            response = get_appid_details(appid)
            time.sleep(1)

            if response == None:
                continue
            
            with open(completed_file, 'a') as f:
                f.write(f"{appid}\n")

            for dlc in response:
                logger.info(f"Get dlc details with appid {dlc} for appid {appid}")
                get_appid_details(dlc)
                time.sleep(1)

def get_appids(filename):

    filepath = app_list_folder + '/' + filename
    appids = []

    with open(filepath, 'r') as f:
        app_list = json.load(f)['response']['apps']

    for app in app_list:
        appids.append(app['appid'])

    return appids

def get_appid_details(appid):

    payload = {'appids': appid}

    for retry in range(3):

        logger.info(f"API call for appid {appid} - {retry}/3")
        try:
            r = requests.get("http://store.steampowered.com/api/appdetails/", params=payload)

            if r.status_code == 200:
                logger.info(f"API call for appid {appid} Successfull")
                break
            
            logger.warning(f"API call for appid {appid} Faild with status {r.status_code}")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Connection error for appid {appid}: {e}")

        time.sleep(5)
    else:
        
        with open(f"{app_details_folder_fail}/appid_api_failed.txt", 'a') as f:
            f.write(f"{appid}\n")
        return None
        
    json_response = r.json()

    if json_response[str(appid)]['success']:
        logger.info(f"App Details found for appid {appid}")

        path_to_save = f"{app_details_folder}/{appid}_{json_response.get(str(appid),{}).get('data',{}).get('type', 'Unknown')}.json"
        with open(path_to_save, 'w') as f:
            json.dump(json_response, f, indent=4)
    else:
        logger.warning(f"App Details NOT found for appid {appid}")

        path_to_save = f"{app_details_folder_fail}/appid_failed.txt"
        with open(path_to_save, 'a') as f:
            f.write(f"{appid}\n")

    dlc_list = json_response.get(str(appid),{}).get('data',{}).get('dlc',[])
    logger.info(f"Appid {appid} contains {len(dlc_list)} dlc's")

    return dlc_list

def extract_num(filename):
    match = re.search(r'\d+', filename)
    return int(match.group()) if match else float('inf')

if __name__ == '__main__':
    main()