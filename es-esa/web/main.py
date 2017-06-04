from flask import Flask
from api import search_api

app = Flask(__name__)
app.config.from_object("settings")
app.config.from_envvar("ES_ESA_SETTINGS")
app.register_blueprint(search_api)


if __name__ == "__main__":
    app.run()
