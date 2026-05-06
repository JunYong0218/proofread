#!/bin/bash
set -eu

echo "Starting Streamlit..."
exec streamlit run streamlit_app.py \
  --server.port=8503 \
  --server.address=0.0.0.0 \
  --server.enableXsrfProtection=true \
  --browser.gatherUsageStats=false
