# -*- coding: utf-8 -*-
from flask_data import create_app
app = create_app()

if __name__ == "__main__":
    # debug環境（wsgirefサーバ）で動作させるときはこちらを使う
    app.run()
    # herokuでgunicornを使うときはこっち
    # port = int(os.getenv("PORT", 5000))
    # app.run(host="0.0.0.0", port=port)