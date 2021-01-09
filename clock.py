from apscheduler.schedulers.blocking import BlockingScheduler
from lib import selen_autopurchase

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=1)
def start_search():
    print('定期実行確認してますうううううううううう')
    # options_with_env = selen_autopurchase.PurchaseClass()
    # options_with_env.touch_captcha(captcha_string=captcha, timestamp=timestamp)


sched.start()
