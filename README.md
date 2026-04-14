# 启动

- gateway启动(backend下): PYTHONPATH=. uv run uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001
- agent启动(backend下)：uv run langgraph dev --no-browser --no-reload --n-jobs-per-worker 10