from manage import create_app
import os

config = None
# allow overriding DB uri and secret via environment variables
if os.environ.get('FLASK_DATABASE_URI'):
    class EnvConfig:
        SQLALCHEMY_DATABASE_URI = os.environ['FLASK_DATABASE_URI']
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    config = EnvConfig

app = create_app(config)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
