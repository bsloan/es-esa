import api
from flask import Flask

app = Flask(__name__)
app.config.from_object("settings")
app.register_blueprint(api.search_api)


if __name__ == "__main__":
    app.run(host=app.config["HOST"])
