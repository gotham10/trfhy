import os
import requests
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/items')
def proxy_api():
    search = request.args.get('search')
    variant = request.args.get('variant')

    if not search or not variant:
        return jsonify({"error": "Missing search or variant parameter"}), 400

    api_url = f"https://bgsi-kyc3.onrender.com/api/items?search={search}&variant={variant}"
    
    try:
        res = requests.get(api_url)
        res.raise_for_status()
        raw_text = res.text
        
        json_str = ""
        if "<pre>" in raw_text and "</pre>" in raw_text:
            json_str = raw_text.split("<pre>")[1].split("</pre>")[0]
        else:
            json_str = raw_text
        
        data = json.loads(json_str)
        return jsonify(data)

    except Exception:
        return jsonify({"pagination": {}, "pets": []})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
