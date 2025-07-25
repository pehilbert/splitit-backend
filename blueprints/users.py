from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from model import User

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/', methods=['GET'])
def get_users():
    user_id = request.args.get('user_id', type=int)
    session = current_app.Session()

    if user_id is not None:
        try:
            user = session.query(User).filter_by(id=user_id).first()

            if user is None:
                session.close()
                return jsonify({"error": "User not found"}), 404
            
            user_dict = user.to_dict()
        except Exception as e:
            current_app.logger.error(f"Error fetching user: {e}")
            session.close()
            return jsonify({"error": "Failed to fetch user"}), 500
        finally:
            session.close()

        return jsonify({"users": [user_dict]})
    else:
        try:
            users = session.query(User).all()
            users_list = [user.to_dict() for user in users]
        except Exception as e:
            current_app.logger.error(f"Error fetching users: {e}")
            return jsonify({"error": "Failed to fetch users"}), 500
        finally:
            session.close()

        return jsonify({"users": users_list})
    
@users_bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json()

    if not data or not all(key in data for key in ('username', 'password', 'firstName', 'lastName')):
        return jsonify({"error": "Missing required fields"}), 400
    
    hashed_password = generate_password_hash(data['password'])
    data['password'] = hashed_password

    new_user = User(
        username=data['username'],
        password=data['password'],
        first_name=data['firstName'],
        last_name=data['lastName']
    )

    try:
        session = current_app.Session()
        session.add(new_user)
        session.commit()
        new_user_dict = new_user.to_dict()
    except Exception as e:
        current_app.logger.error(f"Error creating user: {e}")
        return jsonify({"error": "Failed to create user"}), 500
    finally:
        session.close()

    return jsonify({"message": "User created successfully", "user": new_user_dict}), 201

@users_bp.route('/', methods=['PUT'])
def update_user():
    data = request.get_json()
    user_id = request.args.get('user_id', type=int)

    if user_id is None:
        return jsonify({"error": "User ID is required"}), 400
    
    try:
        session = current_app.Session()
        user = session.query(User).filter_by(id=user_id).first()

        if user is None:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        for key, value in data.items():
            if hasattr(user, key) and key != 'id':
                setattr(user, key, value)

        user_dict = user.to_dict()
        session.commit()
    except Exception as e:
        current_app.logger.error(f"Error initializing session: {e}")
        return jsonify({"error": "Failed to initialize database session"}), 500
    finally:
        session.close()
    
    return jsonify({"message": "User updated successfully", "user": user_dict}), 200

@users_bp.route('/', methods=['DELETE'])
def delete_user():
    user_id = request.args.get('user_id', type=int)

    if user_id is None:
        return jsonify({"error": "User ID is required"}), 400
    
    try:
        session = current_app.Session()
        user = session.query(User).filter_by(id=user_id).first()

        if user is None:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        session.delete(user)
        session.commit()
    except Exception as e:
        current_app.logger.error(f"Error deleting user: {e}")
        return jsonify({"error": "Failed to delete user"}), 500
    finally:
        session.close()
    
    # Placeholder for deleting a user
    return jsonify({"message": "User deleted successfully"}), 200

@users_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not all(key in data for key in ('username', 'password')):
        return jsonify({"error": "Missing required fields"}), 400
    
    session = current_app.Session()
    user = session.query(User).filter_by(username=data['username']).first()

    if user and check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=user.id)
        session.close()
        return jsonify({"access_token": access_token}), 200
    else:
        session.close()
        return jsonify({"error": "Invalid username or password"}), 401