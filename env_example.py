import os

os.environ.setdefault("IP", "0.0.0.0")
os.environ.setdefault("PORT", "3000")
os.environ.setdefault("SECRET_KEY", "secret_key_goesHere")
os.environ.setdefault("MONGO_URI", "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<database>?retryWrites=true&w=majority")
os.environ.setdefault("MONGO_DBNAME", "<database>")
