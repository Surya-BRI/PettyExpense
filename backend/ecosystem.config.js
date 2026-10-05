module.exports = {
  apps: [
    {
      name: "expensetracker-api",
      cwd: "/home/ubuntu/bri-erp-api/expensetracker-api",
      script: "venv/bin/gunicorn",
      args: "main:app -k uvicorn.workers.UvicornWorker -b 127.0.0.1:5930 --workers 1 --timeout 90 --access-logfile - --error-logfile -",
      interpreter: "none",
      autorestart: true,
      watch: false,
    },
  ],
};
