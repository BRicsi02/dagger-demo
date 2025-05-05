# backend/app.py
from flask import Flask, jsonify, send_from_directory


app = Flask(__name__, static_folder="frontend", static_url_path="")

@app.route("/api")
def api():
    return jsonify(message="Hello from Backend!")

@app.route("/", methods=["GET"])
def root():
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
