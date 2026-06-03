Start the MacBook Security Dashboard.

1. Kill any existing instance: `pkill -f "src/app.py"` (ignore errors if nothing is running)
2. Start in the background: `PORT=8000 .venv/bin/python src/app.py &`
3. Wait 2 seconds, then `curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:8000/` to confirm HTTP 200
4. Report the port and any startup errors
