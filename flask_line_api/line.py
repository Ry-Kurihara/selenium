# -*- coding: utf-8 -*-
from logging import error
from time import time
from botocore import args
from flask import request, abort
import os
import pandas as pd
from pytz import timezone
from sqlalchemy import create_engine

from lib import selen_autopurchase
import boto3

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask_data import scheduler

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, QuickReplyButton, QuickReply, 
    TextSendMessage, TemplateSendMessage, ImageSendMessage, StickerSendMessage, PostbackEvent,
    CarouselColumn, CarouselTemplate, ButtonsTemplate,
    PostbackAction, URIAction, MessageAction
)

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../my_lib'))
import param_store as ps
import requests

import logging
logger = logging.getLogger('app.flask').getChild(__name__)

YOUR_CHANNEL_ACCESS_TOKEN = ps.get_parameters('/line/message_api/line_channel_access_token')
YOUR_CHANNEL_SECRET = ps.get_parameters('/line/message_api/line_channel_secret')
HEROKU_POSTGRES_URL = ps.get_parameters('/heroku/postgres_url')

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

from flask import Blueprint
from flask import current_app as app 
line = Blueprint('line', __name__)

@line.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value: signatureは意味不明な文字列
    signature = request.headers['X-Line-Signature']

    # get request body as text: bodyはjson形式
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body: エラーメッセージを出力したくない場合tryでくるむ
    handler.handle(body, signature)
    # try:
    #     handler.handle(body, signature)
    # except InvalidSignatureError:
    #     abort(400)

    return 'OK'

# URLのキャッチ、監視時間の設定を聞く
@handler.add(MessageEvent, message=TextMessage)
def get_url_and_ask_time(event):
    user_id = str(event.source.user_id)
    timestamp = str(event.timestamp)
    message = event.message.text 

    engine = create_engine(HEROKU_POSTGRES_URL)
    df = pd.DataFrame(data=[[user_id, timestamp, message]], columns=['user_id', 'timestamp', 'message'])
    df.to_sql('line_autopurchase', con=engine, if_exists='append', index=False)

    if 'Amazonで購入' in message:
        messages = TextSendMessage(text='URLを入力してください')
        line_bot_api.reply_message(
            event.reply_token,
            messages=messages
        )

    elif 'https://www.amazon.co.jp' in message:
        item_url = message
        purchaser = selen_autopurchase.PurchaseClass()
        product_title = purchaser.get_title_and_asin_from_url(timestamp, item_url)
        s3_image_url = _get_s3_image_url('get_title', timestamp)
        df = pd.DataFrame(data=[[user_id, timestamp, item_url, product_title]], columns=['user_id', 'timestamp', 'item_url', 'product_title'])
        df.to_sql('line_purchase_list', con=engine, if_exists='append', index=False)

        text_message = TextSendMessage(text=f"商品名：{product_title}を監視します！ 上限金額を設定してください")
        image_message = ImageSendMessage(
                original_content_url=s3_image_url,
                preview_image_url=s3_image_url, 
        )
        messages = [text_message, image_message]
        line_bot_api.reply_message(
            event.reply_token,
            messages=messages
        )

    elif 'maxprice_' in message:
        df = pd.read_sql(sql=f"SELECT * from line_purchase_list WHERE user_id='{user_id}' ORDER BY CAST(timestamp AS BIGINT) DESC", con=engine)
        item_url = df.at[0, 'item_url']
        product_title = df.at[0, 'product_title']
        max_price = event.message.text[9:]
        df = pd.DataFrame(data=[[user_id, timestamp, item_url, product_title, max_price]], columns=['user_id', 'timestamp', 'item_url', 'product_title', 'max_price'])
        df.to_sql('line_purchase_list', con=engine, if_exists='append', index=False)

        schedule_list = ["30", "60", "120", "240"]
        items = [QuickReplyButton(action=MessageAction(label=f"{schedule}秒間隔で監視する", text=f"schedule_{schedule}")) for schedule in schedule_list]
        text_message = TextSendMessage(
            text=f"{product_title}の上限金額を{max_price}円に設定しました！ 最後に監視頻度を指定してください",
            quick_reply=QuickReply(items=items),
        )
        line_bot_api.reply_message(
            event.reply_token,
            messages=text_message,
        )

    elif 'schedule_' in message:
        schedule_seconds = int(event.message.text[9:])
        df = pd.read_sql(sql=f"SELECT * from line_purchase_list WHERE user_id='{user_id}' ORDER BY CAST(timestamp AS BIGINT) DESC", con=engine)
        product_title = df.at[0, 'product_title']
        product_url = df.at[0, 'item_url']
        max_price = df.at[0, 'max_price']
        text_message = TextSendMessage(text=f'{product_title}のスケジューラを{schedule_seconds}秒間隔で設定します')

        # db_job_store = SQLAlchemyJobStore(engine=engine, tablename='line_ps5_jobstore')
        scheduler.add_job(func=_start_search, id='job_get_item_from_amazon', trigger='interval', args=[schedule_seconds, product_url, user_id, max_price, timestamp], seconds=schedule_seconds)

        line_bot_api.reply_message(
            event.reply_token,
            messages=text_message
        )

    elif 'sched_end' in message:
        scheduler.remove_job('job_get_item_from_amazon')
        text_message = TextSendMessage(text='スケジューラを終了しました')
        logger.info('we killed scheduler!')
        line_bot_api.reply_message(
            event.reply_token,
            messages=text_message
        )

    # TODO: 後で作る
    elif 'my_sched' in message: 
        jobs = scheduler.get_jobs()
        for job in jobs:
            print(job.next_run_time)

    # リッチメニューからのメッセージ
    elif '使い方を教えて' in message:
        text_message = TextSendMessage(text='https://selen-ps5.herokuapp.com/histories/show/line_bot_description')
        line_bot_api.reply_message(
            event.reply_token,
            messages=text_message
        )

    elif 'my_userID' in message:
        messages = TextSendMessage(text=f"{user_id}")
        line_bot_api.reply_message(
            event.reply_token,
            messages=messages
        )

    # TODO: 通るか確認
    elif 'get_cookie' in message:
        purchaser = selen_autopurchase.PurchaseClass()

        purchaser.get_auth_info_for_img_captcha(timestamp, user_id)
        s3_image_url_before = _get_s3_image_url('auth_img_before', timestamp)
        s3_image_url_after = _get_s3_image_url('auth_img_after', timestamp)

        text_message = TextSendMessage(text="認証情報付きcookieをデータベースに送信しました")
        image_message1 = ImageSendMessage(
                original_content_url=s3_image_url_before,
                preview_image_url=s3_image_url_before, 
            )
        image_message2 = ImageSendMessage(
                original_content_url=s3_image_url_after,
                preview_image_url=s3_image_url_after, 
            )
        messages = [text_message, image_message1]
        line_bot_api.reply_message(
            event.reply_token,
            messages=messages
        )

    else:
        messages = TextSendMessage(text='何を言っているのかわかりません')
        line_bot_api.reply_message(
            event.reply_token,
            messages=messages
        )

@handler.add(PostbackEvent)
def get_target_item(event):
    timestamp = str(event.timestamp)
    options_with_env = selen_autopurchase.PurchaseClass()
    item_message = options_with_env.get_item(timestamp)
    s3_image_url = _get_s3_image_url('debug', timestamp)
    message = TextSendMessage(text=item_message)
    image_message = ImageSendMessage(
            original_content_url=s3_image_url,
            preview_image_url=s3_image_url,
    )
    messages = [message, image_message]
    line_bot_api.reply_message(
        event.reply_token,
        messages=messages
    )

"""
ファイル内関数

"""

def _get_s3_image_url(image_name, timestamp, folder_name='created_file/image/'):
    image_name = f'{folder_name}line_{image_name}_{timestamp}.png'
    s3_client = boto3.client('s3')
    s3_image_url = s3_client.generate_presigned_url(
        ClientMethod = 'get_object',
        Params = {'Bucket': 'my-bucket-ps5', 'Key': image_name},
        ExpiresIn = 600,
        HttpMethod = 'GET'
    )
    return s3_image_url

def _start_search(schedule_seconds, url, user_id, max_price, timestamp):
    logger.info(f'we_try_to_purchase_by_{schedule_seconds}_seconds!!')
    # sleep対策
    requests.get('https://selen-ps5.herokuapp.com/')
    purchaser = selen_autopurchase.PurchaseClass()
    status = purchaser.get_item(url, max_price, timestamp)
    if status:
        logger.info(f'got_it_over!!!!')
        sched.remove_job('job_get_item_from_amazon')
        logger.info(f"we killed scheduler!!!!!!!")
        # LINEで通知
        txt_messages = TextSendMessage(text='購入完了したよ')
        s3_image_url = _get_s3_image_url('order_finished', timestamp)
        image_message = ImageSendMessage(
                original_content_url=s3_image_url,
                preview_image_url=s3_image_url, 
        )
        sticker_messages = StickerSendMessage(package_id='6325', sticker_id='10979907')
        messages = [txt_messages, image_message, sticker_messages]
        line_bot_api.push_message(
            to=user_id,
            messages=messages
        )
    else:
        logger.info("continue...")

    return None