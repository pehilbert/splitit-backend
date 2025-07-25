from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from blueprints.users import users_bp
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Base
import os

app = Flask(__name__)

# Get the environment variables
app.logger.info("Loading environment variables...")
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    app.logger.error("DATABASE_URL not set in environment variables.")
    raise ValueError("DATABASE_URL must be set in the environment variables.")

app.logger.info("Successfully loaded environment variables.")

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
app.register_blueprint(users_bp)

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)