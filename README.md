# 启动

- gateway启动(backend下): PYTHONPATH=. uv run uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001
- agent启动(backend下)：uv run langgraph dev --no-browser --no-reload --n-jobs-per-worker 10

## 环境变量配置

创建

nano /etc/systemd/system/deerflow-gateway.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/deer-flow/backend
Environment=DEER_FLOW_CONFIG_PATH=/home/ubuntu/config.yml
ExecStart=/home/ubuntu/.local/bin/uv run uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001
Restart=always

nano /etc/systemd/system/deerflow-agent.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/deer-flow/backend
Environment=DEER_FLOW_CONFIG_PATH=/home/ubuntu/config.yml
ExecStart=/home/ubuntu/.local/bin/uv run langgraph dev --no-browser --no-reload --n-jobs-per-worker 10
Restart=always


配置

Environment=DEER_FLOW_CONFIG_PATH=/home/ubuntu/config.yml
Environment=DEER_FLOW_CONFIG_PATH=/home/ubuntu/config.yml

执行
sudo systemctl daemon-reload
sudo systemctl restart deerflow-gateway.service deerflow-agent.service
sudo systemctl show deerflow-gateway.service -p Environment
sudo systemctl show deerflow-agent.service -p Environment
