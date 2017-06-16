from flask import Blueprint, send_file

web_ui = Blueprint("web_ui", __name__)


@web_ui.route("/")
def render_index():
    return send_file("static/html/index.html")
