module.exports = {
    apps : [
        {
              name: 'trip-planner',
              script: 'main.py',
              args: '',
              instances: 1,
              autorestart: true,
              watch: false,
              max_memory_restart: '1G',
        }
    ]
  };