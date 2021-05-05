from lib import selen_autopurchase

purchase = selen_autopurchase.PurchaseClass()
title_and_asin = purchase.get_title_and_asin_from_url(
    '1223', 
    'https://www.amazon.co.jp/%E3%82%BD%E3%83%8B%E3%83%BC%E3%83%BB%E3%82%A4%E3%83%B3%E3%82%BF%E3%83%A9%E3%82%AF%E3%83%86%E3%82%A3%E3%83%96%E3%82%A8%E3%83%B3%E3%82%BF%E3%83%86%E3%82%A4%E3%83%B3%E3%83%A1%E3%83%B3%E3%83%88-PlayStation-5-%E3%83%87%E3%82%B8%E3%82%BF%E3%83%AB%E3%83%BB%E3%82%A8%E3%83%87%E3%82%A3%E3%82%B7%E3%83%A7%E3%83%B3-CFI-1000B01/dp/B08GGF7M7B/ref=sr_1_6?__mk_ja_JP=%E3%82%AB%E3%82%BF%E3%82%AB%E3%83%8A&dchild=1&keywords=ps5&qid=1620152532&sr=8-6'
)