import random
import time

from PIL import Image
import datetime
import base64
import requests
from io import BytesIO
import numpy as np
from PIL import ImageOps
import ddddocr
from loguru import logger

ocr = ddddocr.DdddOcr(show_ad=False, det=False, ocr=False, import_onnx_path="dawn.onnx", charsets_path="charsets.json")


def process_image(image):
    gray_img = ImageOps.grayscale(image)
    img_array = np.array(gray_img)
    processed_img_array = np.ones_like(img_array) * 255
    black_threshold_low = 0
    black_threshold_high = 50
    mask = (img_array >= black_threshold_low) & (img_array <= black_threshold_high)
    processed_img_array[mask] = 0
    processed_img = Image.fromarray(processed_img_array)
    return processed_img


def run(email, password, proxy=None):
    session = requests.session()
    session.verify = False
    try:
        if proxy is None:
            proxies = None
        else:
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'no-cache',
            'origin': 'chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        }
        response = session.get('https://www.aeropres.in/chromeapi/dawn/v1/puzzle/get-puzzle',
                               headers=headers, proxies=proxies).json()
        puzzle_id = response['puzzle_id']
        headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'no-cache',
            'origin': 'chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        }
        params = {'puzzle_id': puzzle_id, }
        response = session.get('https://www.aeropres.in/chromeapi/dawn/v1/puzzle/get-puzzle-image', params=params,
                               headers=headers, proxies=proxies).json()
        base64_image = response['imgBase64']
        image_data = base64.b64decode(base64_image)
        image = Image.open(BytesIO(image_data))
        new_image = process_image(image)
        result = ocr.classification(new_image)
        headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        }
        current_time = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace(
            "+00:00", "Z")
        json_data = {'username': email, 'password': password, 'logindata': {'_v': '1.0.7', 'datetime': current_time, },
                     'puzzle_id': puzzle_id, 'ans': result}
        response = session.post('https://www.aeropres.in/chromeapi/dawn/v1/user/login/v2', headers=headers,
                                json=json_data, proxies=proxies).json()
        logger.debug(response)
        if response['status']:
            logger.success(response['message'])
            token = response['data']['token']
            while True:
                try:
                    headers = {
                        'accept': '*/*',
                        'accept-language': 'zh-CN,zh;q=0.9',
                        'authorization': f'Berear {token}',
                        'cache-control': 'no-cache',
                        'content-type': 'application/json',
                        'origin': 'chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp',
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
                    }

                    json_data = {'username': email, 'extensionid': 'fpdkjdnhkakefebpekbdhillbhonfjjp',
                                 'numberoftabs': 0,
                                 '_v': '1.0.7'}

                    response = session.post('https://www.aeropres.in/chromeapi/dawn/v1/userreward/keepalive',
                                            headers=headers,
                                            json=json_data, proxies=proxies, timeout=30).json()
                    logger.debug(response)
                    time.sleep(random.randint(100, 150))
                except Exception as e:
                    logger.error(e)
        else:
            logger.warning(response['message'])
    except Exception as e:
        logger.error(e)


if __name__ == '__main__':
    # proxy ip:port:user:pwd
    run('email', 'password', proxy=None)
