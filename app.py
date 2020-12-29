# -*- coding: utf-8 -*-
from logging import error
from flask import Flask, request, abort
import os
import pandas as pd 
from sqlalchemy import create_engine

from lib import selen_autopurchase
import boto3 

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, QuickReplyButton, QuickReply, TextSendMessage, TemplateSendMessage, ImageSendMessage, PostbackEvent,
    CarouselColumn, CarouselTemplate, ButtonsTemplate,
    PostbackAction, URIAction, MessageAction
)

from linebot.models.template import CarouselColumn, TemplateSendMessage

app = Flask(__name__)

YOUR_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
HEROKU_POSTGRES_URL = os.environ["HEROKU_POSTGRES_URL"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

@app.route("/")
def hello_world():
    return "LINE API HOME!"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value: signatureは意味不明な文字列
    signature = request.headers['X-Line-Signature']

    # get request body as text: bodyはjson形式
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )

# クイックリプライ実践：下に書いたほうに上書きされる
@handler.add(MessageEvent, message=TextMessage)
def response_massage(event):
    language_list = ["Ruby", "Python", "PHP"]
    items = [QuickReplyButton(action=MessageAction(label=f"{langage}", text=f"{langage}だ")) for langage in language_list]
    messages = TextSendMessage(text="なんの言語？", quick_reply=QuickReply(items=items))
    print("クイックリプライ作動")
    line_bot_api.reply_message(
        event.reply_token,
        messages = messages 
    )

# カルーセルテンプレート実践
@handler.add(MessageEvent, message=TextMessage)
def response_carousel(event):
    carousel_template_message = TemplateSendMessage(
        alt_text="not_data",
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url='https://example.com/item1.jpg',
                    title='this_is',
                    text='description1',
                    actions=[
                        PostbackAction(
                        label='postback1',
                        display_text='postback text1',
                        data='action=buy&itemid=1'
                        ),
                        MessageAction(
                            label='message1',
                            text='message text1'
                        ),
                        URIAction(
                            label='uri1',
                            uri='http://example.com/1'
                        )
                    ]
                ),
                CarouselColumn(
                    thumbnail_image_url='https://example.com/item2.jpg',
                    title='this is menu2',
                    text='description2',
                    actions=[
                        PostbackAction(
                            label='postback2',
                            display_text='postback text2',
                            data='action=buy&itemid=2'
                        ),
                        MessageAction(
                            label='message2',
                            text='message text2'
                        ),
                        URIAction(
                            label='uri2',
                            uri='http://example.com/2'
                        )
                    ]
                )
            ]
        )
    )
    line_bot_api.reply_message(
        event.reply_token,
        messages=carousel_template_message
    )

# URLのキャッチ、監視時間の設定を聞く
@handler.add(MessageEvent, message=TextMessage)
def get_url_and_ask_time(event):
    engine = create_engine(HEROKU_POSTGRES_URL)

    user_id = str(event.source.user_id)
    timestamp = str(event.timestamp)
    message = event.message.text 

    df = pd.DataFrame(data=[[user_id, timestamp, message]], columns=['user_id', 'timestamp', 'message'])
    df.to_sql('line_autopurchase', con=engine, if_exists='append', index=False)

    if event.message.text in ('Amazonで購入'):
        messages = TextSendMessage(text='URLを入力してください')
        line_bot_api.reply_message(
            event.reply_token,
            messages=messages
        )

    elif 'asin_is:' in event.message.text:
        asin = event.message.text[8:] # url_isはいらない
        image_url = f'https://images-na.ssl-images-amazon.com/images/P/{asin}.09.THUMBZZZ.jpg'
        buttons_message = TemplateSendMessage(
            alt_text='画像が表示できません',
            template=ButtonsTemplate(
                thumbnail_image_url=image_url,
                title='Is_it?',
                text='we purchase this. OKEEEEEEY??',
                actions=[ 
                    PostbackAction(
                        label='購入します',
                        # display_text='購入', ユーザーが送るメッセージはいらない
                        data='itempurchase'
                    ),
                    MessageAction(
                        label='買わない',
                        text='買わないよ'
                    ),
                ]
            )
        )
        line_bot_api.reply_message(
            event.reply_token,
            messages=buttons_message
        )

    elif event.message.text in ('買わないよ'):
        messages = TextSendMessage(text='そうですか')
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
    try:
        options_with_env.get_item(timestamp=timestamp)
    except Exception as e:
        error_message = f'error_is_{e}!!!!!!'
        line_bot_api.reply_message(
            event.reply_token,
            messages=error_message
        )
        return None

    image_name = f'shot{timestamp}.png'
    s3_client = boto3.client('s3')
    s3_image_url = s3_client.generate_presigned_url(
        ClientMethod = 'get_object',
        Params = {'Bucket': 'my-bucket-ps5', 'Key': image_name},
        ExpiresIn = 600,
        HttpMethod = 'GET'
    )
    print(f'URLは{s3_image_url}だあああああああああ')

    message = TextSendMessage(text="購入確認します！")
    image_message = ImageSendMessage(
            original_content_url=s3_image_url,
            preview_image_url=s3_image_url, #'https://my-bucket-ps5.s3-ap-northeast-1.amazonaws.com/proto3.png'
        )
    messages = [message, image_message]
    line_bot_api.reply_message(
        event.reply_token,
        messages=messages
    )




if __name__ == "__main__":
    # debug環境（wsgirefサーバ）で動作させるときはこちらを使う
    app.run()
    # herokuでgunicornを使うときはこっち
    # port = int(os.getenv("PORT", 5000))
    # app.run(host="0.0.0.0", port=port)