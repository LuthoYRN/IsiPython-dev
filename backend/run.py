import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    flask_env = os.environ.get('FLASK_ENV', 'production')
    
    # Configure based on environment
    if flask_env == 'development':
        host = '127.0.0.1'  
        port = 5000         
        debug = True       
    else:
        host = '0.0.0.0'    
        port = int(os.environ.get('PORT', 10000))  
        debug = True     
    
    app.run(
        host=host,
        port=port,
        debug=debug
    )