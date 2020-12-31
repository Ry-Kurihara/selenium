import os
import logging 
# import cv2
# buildpack apkを消す。（https://github.com/heroku/heroku-buildpack-apt）opencv-python消す：appfile消す

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

import boto3 
import time  
import pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SeleniumMainError(Exception):
    """Selenium関連のエラー基底クラス"""
    pass 


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
        env = os.environ['APP_ENV']
        if env == 'mywin':
            self.DRIVER_PATH = '/Users/ryzerk/develop/python/selenium/chromedriver'
            self.options.add_argument('--headless'); # たまにヘッドレスモードで確認したい
        elif env == 'heroku':
            self.DRIVER_PATH = '/app/.chromedriver/bin/chromedriver'
            self.options.add_argument('--headless');
        else:
            # TODO: あとでエラーと同時に文字列出力する
            logger.warning('環境を設定してください！')
            raise SeleniumMainError


    def _upload_pkl_cookies(self, driver, upload_name):
        s3_resorce = boto3.resource('s3')
        with open(upload_name, 'wb') as f:
            pickle.dump(driver.get_cookies(), f)
        s3_resorce.Bucket('my-bucket-ps5').upload_file(upload_name, upload_name)

    def _return_checked_cookies(self, cookie_name='captcha.pickle'):
        s3 = boto3.resource('s3')
        pkl_name = cookie_name
        s3.Bucket('my-bucket-ps5').download_file(pkl_name, pkl_name)
        with open(pkl_name, 'rb') as f:
            cookies = pickle.load(f)
        return cookies

    def _upload_page_souce(self, driver, html_name='hoge'):
        s3_resorce = boto3.resource('s3')
        html = driver.page_source
        html_name = f'{html_name}.html'
        with open(html_name, 'w', encoding='utf-8') as f:
            f.write(html)
        s3_resorce.Bucket('my-bucket-ps5').upload_file(html_name, html_name)

    def _upload_screen_shot(self, driver, image_name, timestamp):
        s3_resorce = boto3.resource('s3')
        image_name = f'line_{image_name}_{timestamp}.png'
        driver.save_screenshot(image_name)
        s3_resorce.Bucket('my-bucket-ps5').upload_file(image_name, image_name)

    def _amazon_login(self, driver):
        driver.find_element_by_xpath("//a[@id='nav-link-accountList']/span").click()
        driver.find_element_by_id('ap_email').send_keys(os.environ['AMAZON_EMAIL'])
        driver.find_element_by_id('continue').click()
        driver.find_element_by_id('ap_password').send_keys(os.environ['AMAZON_PASS'])
        driver.find_element_by_id('signInSubmit').click()
        return None

    def _amazon_try_str_security(self, driver):
        # 文字認証画面ではないならNosuchElementError
        driver.find_element_by_id('auth-captcha-guess')

        driver.find_element_by_id('ap_password').send_keys(os.environ['AMAZON_PASS'])
        driver.find_element_by_id('auth-captcha-guess').send_keys(input())
        driver.find_element_by_id('signInSubmit').click()

        # cookieの送信
        self._upload_pkl_cookies(driver, 'captcha_new.pickle')

        

    def get_item(self, timestamp):
        # ブラウザの起動
        logger.info('起動します')
        driver = webdriver.Chrome(executable_path=self.DRIVER_PATH, chrome_options=self.options)
        time.sleep(1)

        # amazonにアクセスする
        amazon_url = 'https://www.amazon.co.jp/'
        driver.get(amazon_url)

        # cookieを読み込む
        cookies = self._return_checked_cookies()
        for cookie in cookies:
            driver.add_cookie(cookie)

        # driver.refresh()

        # 商品ページにアクセスする
        url = 'https://www.amazon.co.jp/dp/B08GG247WR/ref=s9_acss_bw_cg_toio_md1_w?&me=AN1VRQENFRJN5&pf_rd_m=A3P5ROKL5A1OLE&pf_rd_s=merchandised-search-4&pf_rd_r=W83F5KPFR335M79YGQ4X&pf_rd_t=101&pf_rd_p=6cc9fda7-b07a-4770-bec3-ee1dff21047b&pf_rd_i=3355676051'
        driver.get(url)
        time.sleep(1)

        selector = '#availability'
        element = driver.find_element_by_css_selector(selector)
        availability = element.text

        # 在庫あり、入荷予定、在庫切れの3種類っぽい
        if '在庫あり' in availability:
            logger.warning('在庫あったーーーーーー')
            pass
        elif '入荷予定' in availability:
            logger.warning('入荷予定らしい')
        elif '在庫切れ' in availability:
            logger.warning('在庫切れらしい')
            self._upload_screen_shot(driver, 'debug', timestamp)
            return '在庫切れでした'
        else:
            logger.warning(f'該当なしです：availability is {availability} ですよ')
            self._upload_screen_shot(driver, 'debug', timestamp)
            return '在庫不明です'
        self._upload_screen_shot(driver, 'debug', timestamp)
        # try:
        #     self._amazon_login(driver)
        # except NoSuchElementException:
        #     logger.warning('ログイン済の可能性があります！！！！')
        #     url = 'https://www.amazon.co.jp/dp/B08GG247WR/ref=s9_acss_bw_cg_toio_md1_w?&me=AN1VRQENFRJN5&pf_rd_m=A3P5ROKL5A1OLE&pf_rd_s=merchandised-search-4&pf_rd_r=W83F5KPFR335M79YGQ4X&pf_rd_t=101&pf_rd_p=6cc9fda7-b07a-4770-bec3-ee1dff21047b&pf_rd_i=3355676051'
        #     driver.get(url)
        # time.sleep(2)

        elem_login_btn = driver.find_element_by_id('add-to-cart-button')
        elem_login_btn.click()
        driver.get('https://amazon.co.jp/gp/cart/view.html/ref=nav_cart')
        

        return '商品をカートに入れました。購入確定しますか？'

    def debug_screenshot(self, timestamp):
        # ブラウザの起動
        logger.info('debug起動します')
        driver = webdriver.Chrome(executable_path=self.DRIVER_PATH, chrome_options=self.options)
        time.sleep(1)

        # Googleにアクセスする
        url = 'https://google.com/'
        driver.get(url)
        time.sleep(1)

        # カマグチと検索
        search_bar = driver.find_element_by_name('q')
        search_bar.send_keys("カマグチ")
        search_bar.submit()

        # スクショを取ります
        self._upload_screen_shot(driver, 'debug', timestamp)


    def touch_captcha(self, captcha_string, timestamp):
        s3 = boto3.resource('s3')

        pkl_name = 'captcha.pickle'
        s3.Bucket('my-bucket-ps5').download_file(pkl_name, pkl_name)
        with open(pkl_name, 'rb') as f:
            cookies = pickle.load(f)
        driver = webdriver.Chrome(executable_path=self.DRIVER_PATH, chrome_options=self.options)
        amazon_url = 'https://www.amazon.co.jp/'
        driver.get(amazon_url)

        for cookie in cookies:
            driver.add_cookie(cookie)

        driver.refresh()
        print('captchaリフレッシュ後')

        # スクリーンショットの保存
        image_name = f'link_pre{timestamp}.png'
        driver.save_screenshot(image_name)
        s3_resorce = boto3.resource('s3')
        s3_resorce.Bucket('my-bucket-ps5').upload_file(image_name, image_name)

        driver.find_element_by_xpath("//a[@id='nav-link-accountList']/span").click()
        driver.find_element_by_id('ap_email').send_keys(os.environ['AMAZON_EMAIL'])
        driver.find_element_by_id('continue').click()
        driver.find_element_by_id('ap_password').send_keys(os.environ['AMAZON_PASS'])
        driver.find_element_by_id('signInSubmit').click()
        time.sleep(2)

        # スクリーンショットの保存
        image_name = f'link_after{timestamp}.png'
        driver.save_screenshot(image_name)
        s3_resorce = boto3.resource('s3')
        s3_resorce.Bucket('my-bucket-ps5').upload_file(image_name, image_name)

        driver.find_element_by_id('ap_password').send_keys(os.environ['AMAZON_PASS'])
        driver.find_element_by_id('auth-captcha-guess').send_keys(captcha_string)
        driver.find_element_by_id('signInSubmit').click()
        time.sleep(2)

        # スクリーンショットの保存
        image_name = f'captcha{timestamp}.png'
        driver.save_screenshot(image_name)
        s3_resorce = boto3.resource('s3')
        s3_resorce.Bucket('my-bucket-ps5').upload_file(image_name, image_name)