from apscheduler.schedulers.blocking import BlockingScheduler
from lib import selen_autopurchase

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=1)
def start_search():
    print('定期実行確認してますうううううううううう')


sched.start()
