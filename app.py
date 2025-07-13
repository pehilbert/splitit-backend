from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/heartbeat', methods=['GET'])
def test_endpoint():
    return jsonify({"status": "Healthy"})

if __name__ == '__main__':
    app.run(debug=True)