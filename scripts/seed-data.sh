#!/bin/bash
set -e
POD=$(kubectl get pods -l app=database -o jsonpath="{.items[0].metadata.name}")

kubectl exec -i $POD -- psql -U ${DB_USER:-bookstore_user} -d ${DB_NAME:-bookstore_db} <<'SQL'
CREATE TABLE IF NOT EXISTS books (
  id SERIAL PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  author VARCHAR(100) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  stock INTEGER NOT NULL DEFAULT 0,
  isbn VARCHAR(20) UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS orders (
  id SERIAL PRIMARY KEY,
  customer_name VARCHAR(100) NOT NULL,
  customer_email VARCHAR(100) NOT NULL,
  book_id INTEGER NOT NULL,
  book_title VARCHAR(200),
  quantity INTEGER NOT NULL,
  total_price DECIMAL(10,2) NOT NULL,
  status VARCHAR(20) DEFAULT 'pending',
  order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO books (title, author, price, stock, isbn) VALUES
('Clean Code','Robert Martin',29.99,10,'978-0132350884'),
('Design Patterns','Gang of Four',39.99,5,'978-0201633610'),
('Refactoring','Martin Fowler',34.99,8,'978-0201485677'),
('The Pragmatic Programmer','Hunt & Thomas',32.99,12,'978-0135957059')
ON CONFLICT DO NOTHING;
SQL
echo "Seed done"

