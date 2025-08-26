import json
from pathlib import Path
import logging
import requests
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

config_file = 'lisamaht.json'
path = Path(config_file)
if path.is_file() is not True:
    exit(f'ERROR: JSON configuration file {config_file} is not exist!')
config = json.load(open(config_file))

order_amount = config["order_amount"]
remote_host = config["remote_host"]
url = f'https://{remote_host}'
site_lisamaht = url + config['site_lisamaht']
api_info = url + config['site_api_info']
api_add = url + config['site_api_add']
user_agent = config['user_agent']
dst_nat_ip  = config['dst_nat_ip']

def logger(message, level='error'):
    log_file = config['log_file']
    try:
        file = open(log_file, 'a')
        file.close
    except:
        exit(f'ERROR: can\'t open log file!')

    logger = logging.getLogger("lisamaht")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    if level == 'info':
        info = message
        logger.info(info)
        print(f'INFO: {info}')
    elif level == 'error':
        error = message
        logger.error(error)
        exit(f'ERROR: {message}')
    else:
        exit('ERROR: Log level is incorrect')


def get_cookie_header():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-features=AsyncDns,UseDnsHttpsSvcb,UseDnsHttpsSvcbAlpn,NetworkServiceInProcess',
                    f'--host-resolver-rules=MAP {remote_host} {dst_nat_ip },MAP www.{remote_host} {dst_nat_ip }',
                    '--ignore-certificate-errors',
                ]
            )
            context = browser.new_context(user_agent=user_agent, ignore_https_errors=True)
            page = context.new_page()
            page.goto(
                site_lisamaht,
                wait_until="networkidle",
            )
            # Wait for scripts that might set extra cookies
            with page.expect_response(lambda r: "lisamaht" in r.url and r.status == 200):
                page.goto(site_lisamaht, wait_until="networkidle", timeout=60000)

            cookies = context.cookies()
            browser.close()
    
        # Build Cookie header
        cookie_header = "; ".join(
            f"{c.get('name', '')}={c.get('value', '')}" for c in cookies if 'name' in c and 'value' in c
        )

        return cookie_header
    
    except TimeoutError:
        logger(f"Timed out waiting load: {site_lisamaht}")
        return NotImplementedError
    except Exception as e:
        logger(f"Error in cookies: {str(e)}")
        return None

def send_request(cookie_header, site, payload=None, request="get"):
    headers = {
        "Cookie": cookie_header,
        "Content-Type": "application/json",
        "Origin": url,
        "Referer": site_lisamaht,
        "User-Agent": user_agent,
        "Accept": "application/json, text/plain, */*",
    }
    
    try:
        resp = None
        if request == "get":
            resp = requests.get(site, headers=headers, timeout=30)
        elif request == "put":
            resp = requests.put(site, headers=headers, data=json.dumps(payload), timeout=30)
        else:
            logger(f"Unsupported request type: {request}")
            return
        if resp is not None:
            if (request == "get" and resp.status_code == 200) or (request == "put" and resp.status_code == 412):
                return(resp.text)
        else:
            logger(f"Failed with status {resp.status_code}: {resp.text}")
    except requests.RequestException as e:
        logger(f"Request error: {str(e)}") 

def get_unused_data(cookie_header):
    try:
        json_get = send_request(cookie_header, api_info)
        if json_get is not None:
            data = json.loads(json_get)
            unusedData = round(data['unusedData'])

            return unusedData

        else:
            logger("Failed to get Unused data (GB) amount")
            return None
    
    except json.JSONDecodeError as e:
        logger(f"JSON decode error for Unused data (GB) amount: {str(e)}")
        return None

def add_plan():
    cookie_header = get_cookie_header()
    if cookie_header is not None:
        unused_data = get_unused_data(cookie_header)
        if unused_data is not None:
            if unused_data < config['unusedData_min']:
                logger(f"Current unused data: {unused_data} GB. Will add {order_amount} GB", level='info')
                payload = {"id":config["order_id"][f"{order_amount}"],"eraArve":False,"type":"ONCEOFF"}    
                json_put = send_request(cookie_header, api_add, payload, request="put")
                if json_put is not None:
                    data = json.loads(json_put)
                    if "errorCode" in data:
                        if data["errorCode"] == "ORDER_ALREADY_IN_PROCESSING":
                            logger(f"Failed to add plan. Previous order is still processing")
                            return
                updated_data = unused_data
                i = 0
                # Refresh every 10 seconfs until unused data is updated
                # or max attempts reached (10x30 seconds = 5 minutes)
                while unused_data == updated_data and i < 30:
                    updated_data = get_unused_data(cookie_header)
                    if updated_data is not None:
                        i += 1
                        time.sleep(10) # Wait 10 seconfs for the request to process

                logger(f"{order_amount} GB has been added. Now: {updated_data} GB unused data", level='info')
            else:
                print(f"Current unused data: {unused_data} GB\nNo need to add more:1 {order_amount} GB\nRequired minimum:    {config['unusedData_min']} GB")
def main():
    add_plan()

if __name__ == "__main__":
    main()