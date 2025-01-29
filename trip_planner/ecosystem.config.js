module.exports = {
    apps : [
        {
              name: 'trip-planner',
            script: 'uvicorn main:app --host 0.0.0.0 --port 5009',
              args: '',
              instances: 1,
              autorestart: true,
              watch: false,
              max_memory_restart: '1G',
        }
    ]
  };