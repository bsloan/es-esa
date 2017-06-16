import api
import web_ui
from flask import Flask

app = Flask(__name__)
app.config.from_object("settings")
app.config.from_envvar("ES_ESA_SETTINGS")
app.register_blueprint(api.search_api)
app.register_blueprint(web_ui.web_ui)


if __name__ == "__main__":
    with app.app_context():
        api.init_elasticsearch()
    app.run(host=app.config["HOST"])
