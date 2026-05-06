#!/bin/bash
set -eu

LT_SUBDOMAIN=${LT_SUBDOMAIN:-"my-secure-test-123"}

if ! [[ "$LT_SUBDOMAIN" =~ ^[a-zA-Z0-9-]{3,63}$ ]]; then
  echo "Invalid LT_SUBDOMAIN. Use 3-63 letters, numbers, or hyphens."
  exit 1
fi

echo "Starting Streamlit in the background..."
streamlit run app.py \
  --server.port=8503 \
  --server.address=0.0.0.0 \
  --server.enableCORS=false \
  --server.enableXsrfProtection=true \
  --browser.gatherUsageStats=false &

sleep 3

echo "Starting localtunnel for subdomain: ${LT_SUBDOMAIN}"
npx localtunnel --port 8503 --subdomain "$LT_SUBDOMAIN"
