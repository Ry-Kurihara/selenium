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

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../my_lib'))
import param_store as ps

logger = logging.getLogger('app.flask').getChild(__name__)

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


    def _upload_pkl_cookies(self, driver, upload_name):
        s3_resorce = boto3.resource('s3')
        with open(upload_name, 'wb') as f:
            pickle.dump(driver.get_cookies(), f)
        s3_resorce.Bucket('my-bucket-ps5').upload_file(upload_name, upload_name)

    def _return_checked_cookies_from_s3(self, cookie_name='captcha.pickle'):
        s3 = boto3.resource('s3')
        pkl_name = cookie_name
        s3.Bucket('my-bucket-ps5').download_file(pkl_name, pkl_name)
        with open(pkl_name, 'rb') as f:
            cookies = pickle.load(f)
        return cookies

    def _add_cookies_to_driver(self, driver, cookies):
        for cookie in cookies:
            driver.add_cookie(cookie)

    def _upload_page_souce(self, driver, html_name='hoge'):
        s3_resorce = boto3.resource('s3')
        html = driver.page_source
        html_name = f'{html_name}.html'
        with open(html_name, 'w', encoding='utf-8') as f:
            f.write(html)
        s3_resorce.Bucket('my-bucket-ps5').upload_file(html_name, html_name)

    def _upload_screen_shot(self, driver, image_name, timestamp, folder_name='created_image_file/'):
        s3_resorce = boto3.resource('s3')
        image_name = f'{folder_name}line_{image_name}_{timestamp}.png'
        driver.save_screenshot(image_name)
        s3_resorce.Bucket('my-bucket-ps5').upload_file(image_name, image_name)

    def _amazon_login_with_id_and_password(self, driver):
        driver.find_element_by_xpath("//a[@id='nav-link-accountList']/span").click()
        driver.find_element_by_id('ap_email').send_keys(ps.get_parameters('/amazon/shop/email'))
        driver.find_element_by_id('continue').click()
        driver.find_element_by_id('ap_password').send_keys(ps.get_parameters('/amazon/shop/pass'))
        driver.find_element_by_id('signInSubmit').click()
        return None

    def _amazon_login_with_password_only(self, driver):
        driver.find_element_by_id('ap_password').send_keys(ps.get_parameters('/amazon/shop/pass'))
        driver.find_element_by_id('signInSubmit').click()
        return None

    def _amazon_try_str_security(self, driver):
        # 文字認証画面ではないならNosuchElementError
        driver.find_element_by_id('auth-captcha-guess')
        driver.find_element_by_id('ap_password').send_keys(ps.get_parameters('/amazon/shop/pass'))
        driver.find_element_by_id('auth-captcha-guess').send_keys(input())
        driver.find_element_by_id('signInSubmit').click()
        # cookieの送信
        self._upload_pkl_cookies(driver, 'captcha_new.pickle')

    def _check_switch_account_and_login(self, driver):
        # たまにログインボタン押した後にアカウントの切り替え画面になる場合があるのでその場合に最初のアカウントを選択してログイン
        if len(driver.find_elements_by_class_name('cvf-widget-btn-verify-account-switcher')) > 0:
            driver.find_element_by_class_name('cvf-widget-btn-verify-account-switcher').click()
            time.sleep(1)
            self._amazon_login_with_password_only(driver)
            logger.info('account_was_switched_and_logined!!')
        # cookie情報でログインできている場合
        else:
            logger.info('switched_is_not_required')
            pass
        return None

    def _is_ok_availability_and_merchant(self, driver):
        # 在庫確認
        if len(driver.find_elements_by_css_selector('#availability')) > 0:
            element = driver.find_element_by_css_selector('#availability')
            availability = element.text
            if not self._is_availabile(availability):
                return False
        else:
            logger.warning('availability_selector_is_not_found')
            pass

        # ショップ確認
        if len(driver.find_elements_by_id('merchant-info')) > 0:
            merchant_info = driver.find_element_by_id('merchant-info').text 
            if not self._is_correct_merchant(merchant_info, 'Amazon.co.jp'):
                return False
        else:
            logger.warning('merchant_info_id_is_not_found')
            pass 
        return True

    def _is_availabile(self, availability):
        if '在庫あり' in availability:
            logger.info('in_stock')
            return True
        elif '入荷予定' in availability:
            logger.info('scheduled_to_arrive')
        elif '在庫切れ' in availability:
            logger.info('out_of_stock')
        elif '現在お取り扱いできません' in availability:
            logger.info('cant_purchase')
        else:
            logger.warning(f'others: availability is {availability} (@ _ @)')
        return False 

    def _is_correct_merchant(self, merchant_info, target_merchant):
        shop = merchant_info.split('が販売')[0].split('この商品は')[1]
        logger.info(f'shop_is_{shop}_!!!!!')
        if target_merchant in shop:
            return True 
        return False 


    def get_item(self, item_url):
        # ブラウザの起動
        logger.info('getting_started_get_item!')
        driver = webdriver.Chrome(executable_path=self.DRIVER_PATH, chrome_options=self.options)
        time.sleep(1)

        # amazonにアクセスする
        amazon_url = 'https://www.amazon.co.jp/'
        driver.get(amazon_url)
        self._add_cookies_to_driver(driver, self._return_checked_cookies_from_s3())

        # 商品ページにアクセスする
        driver.get(item_url)
        time.sleep(1)
        if not self._is_ok_availability_and_merchant(driver):
            logger.info('job finished because availability or merchant is not correct!!')
            driver.quit()
            return False

        driver.find_element_by_id('add-to-cart-button').click()
        driver.get('https://amazon.co.jp/gp/cart/view.html/ref=nav_cart')
        time.sleep(1)

        # login
        driver.find_element_by_name('proceedToRetailCheckout').click()
        self._check_switch_account_and_login(driver)
        time.sleep(1)

        self._upload_screen_shot(driver, 'cart', 'just_before_purchase')
        logger.info(f'just_before_purchase!！')
        driver.quit()
        return True
        # driver.find_element_by_name('placeYourOrder1').click()
        

    def get_title_and_asin_from_url(self, timestamp, item_url):
        # ブラウザの起動
        logger.info('started_get_title_and_asin_from_url')
        driver = webdriver.Chrome(executable_path=self.DRIVER_PATH, chrome_options=self.options)
        time.sleep(1)

        # amazonにアクセスする
        amazon_url = 'https://www.amazon.co.jp/'
        driver.get(amazon_url)

        self._add_cookies_to_driver(driver, self._return_checked_cookies_from_s3())
        # driver.refresh()

        # 商品ページにアクセスする
        driver.get(item_url)
        time.sleep(1)

        product_title = driver.find_element_by_id('productTitle').text
        # できればASINも
        self._upload_screen_shot(driver, 'get_title', timestamp)
        driver.quit()

        return product_title


    # 画像認証が出てきた場合のcookie保存
    def get_auth_info_for_img_captcha(self, timestamp, user_id):
        driver = webdriver.Chrome(executable_path=self.DRIVER_PATH, chrome_options=self.options)
        amazon_url = 'https://www.amazon.co.jp/'
        driver.get(amazon_url)

        self._amazon_login_with_id_and_password(driver)
        time.sleep(1)
        self._upload_screen_shot(driver, 'auth_img_before', timestamp)

        # 画像認証が出てくるはず  TODO: 本当はinputじゃなくてLINEから認証画像を見て入力したい
        driver.find_element_by_id('ap_password').send_keys(ps.get_parameters('/amazon/shop/pass'))
        driver.find_element_by_id('auth-captcha-guess').send_keys(input('please input character strings that displayed in the image: '))
        time.sleep(1)
        self._upload_screen_shot(driver, 'auth_img_after', timestamp)
        driver.find_element_by_id('signInSubmit').click()
        time.sleep(1)

        # cookieの送信
        self._upload_pkl_cookies(driver, f'captcha_cookie_{user_id}.pickle')
        driver.quit()
        return None