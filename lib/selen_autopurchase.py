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
from selenium.common.exceptions import TimeoutException

import boto3 
import time  
import pickle

logger = logging.getLogger(__name__)

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

        # ※herokuなどの本番環境でヘッドレスモードを使用する
        env = os.environ['APP_ENV']
        if env == 'mywin':
            # self.options.add_argument('--headless'); # たまにヘッドレスモードで確認したい
            pass
        else:
            self.options.add_argument('--headless');

        if env == 'mywin':
            self.DRIVER_PATH = '/Users/ryzerk/develop/python/selenium/chromedriver'
        elif env == 'heroku':
            self.DRIVER_PATH = '/app/.chromedriver/bin/chromedriver'
        else:
            logger.warning('環境を設定してください！')
            raise Exception

    def login_google(self):
        # ブラウザの起動
        print('起動します')
        driver = webdriver.Chrome(executable_path=self.DRIVER_PATH, chrome_options=self.options)
        time.sleep(1)

        # Googleにアクセスする
        url = 'https://google.com/'
        driver.get(url)
        time.sleep(1)

        login_id_xpath = '//*[@id="identifierNext"]'
        driver.find_element_by_name("identifier").send_keys('jfkkdk')
        driver.find_element_by_xpath(login_id_xpath).click()
        

    def get_item(self, timestamp):
        # ブラウザの起動
        print('起動します')
        driver = webdriver.Chrome(executable_path=self.DRIVER_PATH, chrome_options=self.options)
        time.sleep(1)

        ##ウィンドウサイズの指定
        # driver.set_window_size(960, 540)

        # Amazonにアクセスする
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
        else:
            logger.warning(f'何にも当てはまってないお：availability is {availability} ですよ')
            
        #再読み込み
        # driver.refresh()

        #現在のURL取得
        # driver.current_url 


        # elem_login_btn = driver.find_element_by_id('add-to-cart-button')
        # elem_login_btn.click()

        # driver.get('https://amazon.co.jp/gp/cart/view.html/ref=nav_cart')

        # login = driver.find_element_by_name('proceedToRetailCheckout')
        # login.click()

        # すでにログイン済みの場合は注文内容確認ページへ遷移する
        # ログイン済みの場合エラーになってしまうので条件分岐が必要
        driver.find_element_by_xpath("//a[@id='nav-link-accountList']/span").click()
        driver.find_element_by_id('ap_email').send_keys(os.environ['AMAZON_EMAIL'])
        driver.find_element_by_id('continue').click()
        driver.find_element_by_id('ap_password').send_keys(os.environ['AMAZON_PASS'])
        driver.find_element_by_id('signInSubmit').click()
        time.sleep(2)

        s3_resorce = boto3.resource('s3')

        html = driver.page_source
        html_name = 'hoge.html'
        with open(html_name, 'w', encoding='utf-8') as f:
            f.write(html)
        s3_resorce.Bucket('my-bucket-ps5').upload_file(html_name, html_name)

        # 文字認証出てきたとき
        try:
            driver.find_element_by_id('auth-captcha-guess')
            # cookieの取得
            print('pkl送信します')
            pkl_name = 'captcha.pickle'
            with open(pkl_name, 'wb') as f:
                pickle.dump(driver.get_cookies(), f)
            s3_resorce.Bucket('my-bucket-ps5').upload_file(pkl_name, pkl_name)
            # urlの取得
            url_file = 'url_is.txt'
            current_url = driver.current_url
            with open(url_file, 'w') as f:
                f.write(current_url)
            s3_resorce.Bucket('my-bucket-ps5').upload_file(url_file, url_file)

            # スクリーンショットの保存
            image_name = f'shot{timestamp}.png'
            driver.save_screenshot(image_name)
            s3_resorce.Bucket('my-bucket-ps5').upload_file(image_name, image_name)
            return None 
        except Exception as e:
            print(f'not_find_of_error?_{e}!!!!!!')
            # スクリーンショットの保存
            image_name = f'shot{timestamp}.png'
            driver.save_screenshot(image_name)
            s3_resorce.Bucket('my-bucket-ps5').upload_file(image_name, image_name)
            driver.quit()
            return None


        

    def touch_captcha(self, captcha_string, timestamp):
        s3 = boto3.resource('s3')

        pkl_name = 'captcha.pickle'
        s3.Bucket('my-bucket-ps5').download_file(pkl_name, pkl_name)
        with open(pkl_name, 'rb') as f:
            cookies = pickle.load(f)
        driver = webdriver.Chrome(executable_path=self.DRIVER_PATH, chrome_options=self.options)
        driver.add_cookie(cookies)

        # urlの取得
        url_file = 'url_is.txt'
        s3.Bucket('my-bucket-ps5').download_file(url_file, url_file)
        with open(url_file, 'r') as f:
            url = f.read()

        driver.get(url)
        time.sleep(2)

        # スクリーンショットの保存
        image_name = f'link{timestamp}.png'
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