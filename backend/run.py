import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    flask_env = os.environ.get('FLASK_ENV', 'production')
    
    if flask_env == 'development':
        print("Development mode - Flask dev server")
        host = '127.0.0.1'  
        port = 5000         
        debug = True
        
        app.run(
            host=host,
            port=port,
            debug=debug
        )