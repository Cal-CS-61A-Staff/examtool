import os

from flask import Flask, send_from_directory, request, jsonify

from convert import convert_str

app = Flask(__name__, static_folder="static", static_url_path="")


@app.route("/exam-server/convert", methods=["POST"])
def convert():
    text = request.json["text"]
    try:
        return jsonify({
            "success": True,
            "examJSON": convert_str(text),
        })
    except SyntaxError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        })


@app.route('/')
def index():
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
