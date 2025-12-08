from flask import Flask, jsonify, request
import os, psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST","database")
DB_PORT = os.getenv("DB_PORT","5432")
DB_NAME = os.getenv("DB_NAME","bookstore_db")
DB_USER = os.getenv("DB_USER","bookstore_user")
DB_PASSWORD = os.getenv("DB_PASSWORD","bookstore_password")

def get_conn():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"ok","service":"book-service"}), 200

@app.route("/books", methods=["GET"])
def list_books():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM books ORDER BY id;")
            rows = cur.fetchall()
            return jsonify(rows), 200

@app.route("/books/<int:book_id>", methods=["GET"])
def get_book(book_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM books WHERE id=%s;", (book_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({"error":"not found"}), 404
            return jsonify(row), 200

@app.route("/books", methods=["POST"])
def add_book():
    data = request.get_json() or {}
    required = ["title","author","price","stock"]
    for r in required:
        if r not in data:
            return jsonify({"error":f"{r} required"}), 400
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO books (title,author,price,stock,isbn) VALUES (%s,%s,%s,%s,%s) RETURNING id;
            """, (data["title"], data["author"], data["price"], data.get("stock",0), data.get("isbn")))
            book_id = cur.fetchone()[0]
            conn.commit()
            return jsonify({"id":book_id}), 201

@app.route("/books/<int:book_id>/reserve", methods=["POST"])
def reserve_book(book_id):
    data = request.get_json() or {}
    qty = int(data.get("quantity",1))
    if qty <= 0:
        return jsonify({"error":"invalid quantity"}), 400
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT stock FROM books WHERE id=%s FOR UPDATE;", (book_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({"error":"not found"}), 404
            stock = row[0]
            if stock < qty:
                return jsonify({"error":"not enough stock"}), 409
            cur.execute("UPDATE books SET stock = stock - %s WHERE id=%s;", (qty, book_id))
            conn.commit()
            return jsonify({"id":book_id, "reserved":qty}), 200

@app.route("/books/<int:book_id>/release", methods=["POST"])
def release_book(book_id):
    data = request.get_json() or {}
    qty = int(data.get("quantity",1))
    if qty <= 0:
        return jsonify({"error":"invalid quantity"}), 400
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE books SET stock = stock + %s WHERE id=%s RETURNING id;", (qty, book_id))
            if cur.rowcount==0:
                return jsonify({"error":"not found"}), 404
            conn.commit()
            return jsonify({"id":book_id, "released":qty}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
