module.exports = {
  apps: [{
    name: 'tennis-booking',
    cwd: '/opt/Tennis_Booking',
    script: './venv/bin/gunicorn',
    args: 'app:app --bind 0.0.0.0:5001 --workers 2 --timeout 120',
    interpreter: 'none',
    env: {
      FLASK_ENV: 'production'
    },
    error_file: './logs/error.log',
    out_file: './logs/out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
  }]
};
