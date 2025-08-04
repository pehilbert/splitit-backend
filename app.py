from flask import Flask, json, jsonify, request
from flask_cors import CORS
import logging
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from blueprints.blueprint_util import setup_blueprint
from blueprints.users import users_bp
from blueprints.groups import groups_bp
from blueprints.expenses import expenses_bp
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Base, Expense
import os

from util.sensitive_info import SensitiveSanitizer

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Get blueprints to set up
BLUEPRINTS = [users_bp, groups_bp, expenses_bp]

# Get the environment variables
app.logger.info("Loading environment variables...")

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    app.logger.error("DATABASE_URL not set in environment variables.")
    raise ValueError("DATABASE_URL must be set in the environment variables.")

app.logger.info("Successfully loaded environment variables.")

# Set up CORS
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
app.logger.info("CORS configured successfully.")

# Initialize sensitive sanitizer
app.logger.info("Initializing SensitiveSanitizer...")
app.sanitizer = SensitiveSanitizer(app.logger, sensitive_fields=['password', 'access_token'])
app.logger.info("SensitiveSanitizer initialized successfully.")

# Initialize the database
app.logger.info("Initializing database...")

app.engine = create_engine(DATABASE_URL, echo=False)
#Base.metadata.drop_all(app.engine, checkfirst=True)
Base.metadata.create_all(app.engine)
app.Session = sessionmaker(bind=app.engine)

app.logger.info("Database initialized successfully.")

# Set up JWT
app.config["JWT_SECRET_KEY"] = "your-secret-key"
jwt = JWTManager(app)

# Define heartbeat endpoint
@app.route('/heartbeat', methods=['GET'])
def test_endpoint():
    app.logger.info("Heartbeat - Healthy.")
    return jsonify({"status": "Healthy"})

# Register blueprints
with app.app_context():
    app.logger.info("Registering blueprints...")

    for blueprint in BLUEPRINTS:
        setup_blueprint(app, blueprint)

    app.logger.info("Blueprints registered successfully.")

# Run the Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)