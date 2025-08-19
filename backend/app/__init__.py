from flask import Flask
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY") 
supabase: Client = create_client(supabase_url, supabase_key)

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)

    from .routes.code_execution import main
    from .routes.admin_challenges import admin_challenges
    from .routes.admin_quizzes import admin_quizzes
    from .routes.student_challenges import student_challenges
    from .routes.student_quizzes import student_quizzes
    app.register_blueprint(main)
    app.register_blueprint(admin_challenges)
    app.register_blueprint(admin_quizzes)
    app.register_blueprint(student_challenges)
    app.register_blueprint(student_quizzes)

    return app