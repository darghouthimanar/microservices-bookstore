#!/bin/bash
NODE_IP=${NODE_IP:-$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[0].address}')}
GATEWAY_URL="http://$NODE_IP:30080/api"

echo "Add a book..."
curl -s -X POST $GATEWAY_URL/books -H "Content-Type: application/json" -d '{"title":"Test Book","author":"Me","price":9.99,"stock":5,"isbn":"TEST-1"}' | jq

echo "List books..."
curl -s $GATEWAY_URL/books | jq

echo "Create order..."
curl -s -X POST $GATEWAY_URL/orders -H "Content-Type: application/json" -d '{"customer_name":"John Doe","customer_email":"john@example.com","book_id":1,"quantity":2}' | jq

echo "Check book stock..."
curl -s $GATEWAY_URL/books/1 | jq

