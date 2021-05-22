from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'my_lib'))
import param_store as ps

class PurchaseClass:
    def __init__(self):
        # Seleniumをあらゆる環境で起動させるChromeオプション
        self.options = Options()
        self.options.add_argument('--disable-gpu');
        self.options.add_argument('--disable-extensions');
        self.options.add_argument('--proxy-server="direct://"');
        self.options.add_argument('--proxy-bypass-list=*');
        self.options.add_argument('--no-sandbox');
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--window-size=1920,1080')
        # self.options.add_argument("--user-data-dir=user") 
        # self.options.add_argument('--profile-directory=profile')

        # ※herokuなどの本番環境でヘッドレスモードを使用する
        env = ps.get_parameters('app_env')
        if env == 'mywin':
            self.DRIVER_PATH = '/Users/r_kurihara/Documents/local/bin/chromedriver'
            self.options.add_argument('--headless'); # たまにヘッドレスモードで確認したい
        elif env == 'heroku':
            self.DRIVER_PATH = '/app/.chromedriver/bin/chromedriver'
            self.options.add_argument('--headless');
        else:
            # TODO: あとでエラーと同時に文字列出力する
            logger.warning('please_set_environment!！')
            raise SeleniumMainError


if __name__ == "__main__":
    purchase = PurchaseClass()
    driver = webdriver.Chrome(executable_path=purchase.DRIVER_PATH, chrome_options=purchase.options)

    amazon_url = 'https://www.amazon.co.jp/'
    driver.get(amazon_url)

    value = driver.find_elements_by_id('ap').click()
    print(value)