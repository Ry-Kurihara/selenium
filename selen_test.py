#!/usr/bin/env python
# coding: utf-8

# ### PS5買いたい

# In[82]:

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

# In[77]:

logger = logging.getLogger(__name__)


# In[83]:


# Seleniumをあらゆる環境で起動させるChromeオプション
options = Options()
options.add_argument('--disable-gpu');
options.add_argument('--disable-extensions');
options.add_argument('--proxy-server="direct://"');
options.add_argument('--proxy-bypass-list=*');
options.add_argument('--start-maximized');

# ※herokuなどの本番環境でヘッドレスモードを使用する
env = os.environ['APP_ENV']
if env == 'mywin':
    options.add_argument('--headless');  # たまにヘッドレスモードで確認したい
    pass
else:
    options.add_argument('--headless'); 


# In[84]:

if env == 'mywin':
    DRIVER_PATH = '/Users/ryzerk/develop/python/selenium/chromedriver'
else:
    DRIVER_PATH = '/app/.chromedriver/bin/chromedriver' # heroku

# ブラウザの起動
driver = webdriver.Chrome(executable_path=DRIVER_PATH, chrome_options=options)


# In[85]:

##ウィンドウサイズの指定
driver.set_window_size(1920, 1080)


# Googleにアクセスする
url = 'https://google.com/'
driver.get(url)


### PS5の在庫確認
# In[87]:


# Amazonにアクセスする
url = 'https://www.amazon.co.jp/dp/B08GG247WR/ref=s9_acss_bw_cg_toio_md1_w?&me=AN1VRQENFRJN5&pf_rd_m=A3P5ROKL5A1OLE&pf_rd_s=merchandised-search-4&pf_rd_r=W83F5KPFR335M79YGQ4X&pf_rd_t=101&pf_rd_p=6cc9fda7-b07a-4770-bec3-ee1dff21047b&pf_rd_i=3355676051'
driver.get(url)


# In[88]:


selector = '#availability'
element = driver.find_element_by_css_selector(selector)
availability = element.text


# In[89]:


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
    
#In[]:

#再読み込み
# driver.refresh()

#現在のURL取得
# driver.current_url 

#スクリーンショットの保存
##ウィンドウサイズの指定
# driver.set_window_size(1250, 1036)
#スクリーンショットを撮る
driver.save_screenshot('proto2.png')
# imgCV = cv2.imread('proto.png')
# cv2.imshow("image", imgCV)
# cv2.waitKey(0)


# In[90]:


elem_login_btn = driver.find_element_by_id('add-to-cart-button')
elem_login_btn.click()


# In[96]:


driver.get('https://amazon.co.jp/gp/cart/view.html/ref=nav_cart')


# In[97]:


login = driver.find_element_by_name('proceedToRetailCheckout')
login.click()

# すでにログイン済みの場合は注文内容確認ページへ遷移する


# ### ログイン済みの場合エラーになってしまうので条件分岐が必要

# In[98]:


driver.find_element_by_id('ap_email').send_keys(os.environ['AMAZON_EMAIL'])

driver.find_element_by_id('continue').click()


# In[95]:


driver.find_element_by_id('ap_password').send_keys(os.environ['AMAZON_PASS'])

driver.find_element_by_id('signInSubmit').click()


# In[ ]:

driver.quit()


