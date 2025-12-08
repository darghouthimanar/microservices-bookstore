from flask import Flask, jsonify, request, Response
import requests, os, time

app = Flask(__name__)

BOOK_URL = os.getenv("BOOK_SERVICE_URL", "http://book-service:5001")
ORDER_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:5002")
TIMEOUT = float(os.getenv("TIMEOUT", "3"))

@app.before_request
def log_request():
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {request.method} {request.path}")

@app.route("/health", methods=["GET"])
def health():
    statuses = {}
    try:
        b = requests.get(f"{BOOK_URL}/health", timeout=TIMEOUT)
        statuses["book"] = {"status": "ok" if b.status_code==200 else "error","code":b.status_code}
    except requests.RequestException as e:
        statuses["book"] = {"status":"unavailable", "error": str(e)}
    try:
        o = requests.get(f"{ORDER_URL}/health", timeout=TIMEOUT)
        statuses["order"] = {"status":"ok" if o.status_code==200 else "error","code":o.status_code}
    except requests.RequestException as e:
        statuses["order"] = {"status":"unavailable", "error": str(e)}
    statuses["gateway"] = {"status":"ok"}
    return jsonify(statuses), 200

@app.route("/api/info", methods=["GET"])
def info():
    return jsonify({"gateway":"api-gateway","routes":["/api/books","/api/orders"]})

@app.route("/api/books", methods=["GET","POST"])
def proxy_books():
    if request.method == "GET":
        r = requests.get(f"{BOOK_URL}/books", timeout=TIMEOUT)
        return Response(r.content, status=r.status_code, content_type=r.headers.get('Content-Type'))
    else:
        r = requests.post(f"{BOOK_URL}/books", json=request.get_json(), timeout=TIMEOUT)
        return Response(r.content, status=r.status_code, content_type=r.headers.get('Content-Type'))

@app.route("/api/books/<int:book_id>", methods=["GET","PUT","DELETE"])
def proxy_book_id(book_id):
    if request.method == "GET":
        r = requests.get(f"{BOOK_URL}/books/{book_id}", timeout=TIMEOUT)
    elif request.method == "PUT":
        r = requests.put(f"{BOOK_URL}/books/{book_id}/stock", json=request.get_json(), timeout=TIMEOUT)
    else:
        r = requests.delete(f"{BOOK_URL}/books/{book_id}", timeout=TIMEOUT)
    return Response(r.content, status=r.status_code, content_type=r.headers.get('Content-Type'))

@app.route("/api/orders", methods=["GET","POST"])
def proxy_orders():
    if request.method == "GET":
        r = requests.get(f"{ORDER_URL}/orders", timeout=TIMEOUT)
    else:
        r = requests.post(f"{ORDER_URL}/orders", json=request.get_json(), timeout=TIMEOUT)
    return Response(r.content, status=r.status_code, content_type=r.headers.get('Content-Type'))

@app.route("/api/orders/customer/<email>", methods=["GET"])
def proxy_orders_by_customer(email):
    r = requests.get(f"{ORDER_URL}/orders/customer/{email}", timeout=TIMEOUT)
    return Response(r.content, status=r.status_code, content_type=r.headers.get('Content-Type'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
