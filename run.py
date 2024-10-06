from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 80))
    app.run(debug=app.config['DEBUG'], host=host, port=port)
