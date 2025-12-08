from flask import Flask, jsonify, request
import os, requests, psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST","database")
DB_PORT = os.getenv("DB_PORT","5432")
DB_NAME = os.getenv("DB_NAME","bookstore_db")
DB_USER = os.getenv("DB_USER","bookstore_user")
DB_PASSWORD = os.getenv("DB_PASSWORD","bookstore_password")
BOOK_SERVICE_URL = os.getenv("BOOK_SERVICE_URL","http://book-service:5001")

def get_conn():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"ok","service":"order-service"}), 200

@app.route("/orders", methods=["GET"])
def list_orders():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM orders ORDER BY id;")
            return jsonify(cur.fetchall()), 200

@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json() or {}
    required = ["customer_name","customer_email","book_id","quantity"]
    for r in required:
        if r not in data:
            return jsonify({"error":f"{r} required"}), 400
    # Check book
    try:
        r = requests.get(f"{BOOK_SERVICE_URL}/books/{data['book_id']}", timeout=3)
    except requests.RequestException:
        return jsonify({"error":"Book service unavailable, please try again"}), 503
    if r.status_code != 200:
        return jsonify({"error":"Book not found"}), 404
    book = r.json()
    if book.get("stock",0) < data["quantity"]:
        return jsonify({"error":"Not enough stock"}), 409
    # Reserve
    try:
        r2 = requests.post(f"{BOOK_SERVICE_URL}/books/{data['book_id']}/reserve", json={"quantity":data["quantity"]}, timeout=5)
    except requests.RequestException:
        return jsonify({"error":"Book service unavailable during reservation"}), 503
    if r2.status_code not in (200,201):
        return jsonify({"error":"Unable to reserve book"}), 409
    total = float(book["price"]) * int(data["quantity"])
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO orders (customer_name,customer_email,book_id,book_title,quantity,total_price,status)
                VALUES (%s,%s,%s,%s,%s,%s) RETURNING id;
            """, (data["customer_name"], data["customer_email"], data["book_id"], book["title"], data["quantity"], total, "confirmed"))
            order_id = cur.fetchone()[0]
            conn.commit()
            return jsonify({"id":order_id,"status":"confirmed"}), 201

@app.route("/orders/customer/<email>", methods=["GET"])
def orders_by_customer(email):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM orders WHERE customer_email=%s ORDER BY order_date DESC;", (email,))
            return jsonify(cur.fetchall()), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
