module.exports = {
  apps: [
    {
      name: 'fastapi-app',
      script: './venv/bin/python3',  // Full path to the Uvicorn script
      args: './src/main.py',
      interpreter: 'none',
      exec_mode: 'fork',
      env: {
        PYTHONUNBUFFERED: '1',
        PATH: '/full/path/to/your/project/venv/bin:$PATH'  // Full path to the virtual environment
      }
    }
  ]
}