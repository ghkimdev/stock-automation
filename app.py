from __future__ import annotations

import os
import sys

# 기존 stock-automation 모듈(config, data, indicators, signals, utils)을
# import 할 수 있도록 프로젝트 루트를 sys.path 에 추가합니다.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template  # noqa: E402 (path must be set first)
from flask_cors import CORS  # noqa: E402

from api.routes import api_bp  # noqa: E402


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
