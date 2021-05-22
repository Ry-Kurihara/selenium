# -*- coding: utf-8 -*-
import logging

from flask_data import create_app
app = create_app()

def _setup_logger(name, logfile='LOGFILENAME.txt'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # create file handler which logs even DEBUG messages
    fh = logging.FileHandler(logfile, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(name)s - %(funcName)s - %(message)s')
    fh.setFormatter(fh_formatter)

    # create console handler with a INFO log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
    ch.setFormatter(ch_formatter)

    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

logger = _setup_logger('app.flask')

if __name__ == "__main__":
    # debug環境（wsgirefサーバ）で動作させるときはこちらを使う
    app.run()
    # herokuでgunicornを使うときはこっち
    # port = int(os.getenv("PORT", 5000))
    # app.run(host="0.0.0.0", port=port)