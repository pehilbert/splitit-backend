from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from model import User

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/', methods=['GET'])
def get_users():
    user_id = request.args.get('user_id', type=int)
    username = request.args.get('username', type=str)
    limit = request.args.get('limit', default=20, type=int)
    session = current_app.Session()

    if user_id is not None:
        try:
            user = session.query(User).filter_by(id=user_id).first()

            if user is None:
                session.close()
                return jsonify({"message": "User not found"}), 404
            
            user_dict = user.to_dict()
        except Exception as e:
            current_app.logger.error(f"Error fetching user: {e}")
            session.close()
            return jsonify({"message": "Failed to fetch user", "error": f"{e}"}), 500
        finally:
            session.close()

        return jsonify({"users": [user_dict]})
    elif username is not None:
        try:
            users = session.query(User).filter(User.username.ilike(f"{username}%")).all()
            users_list = [user.to_dict() for user in users]
        except Exception as e:
            current_app.logger.error(f"Error searching users by username: {e}")
            return jsonify({"message": "Failed to search users", "error": f"{e}"}), 500
        finally:
            session.close()

        return jsonify({"users": users_list[:limit]})
    else:
        try:
            users = session.query(User).all()
            users_list = [user.to_dict() for user in users]
        except Exception as e:
            current_app.logger.error(f"Error fetching users: {e}")
            return jsonify({"message": "Failed to fetch users", "error": f"{e}"}), 500
        finally:
            session.close()

        return jsonify({"users": users_list[:limit]})
    
@users_bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json()

    if not data or not all(key in data for key in ('username', 'password', 'first_name', 'last_name')):
        return jsonify({"message": "Missing required fields"}), 400
    
    hashed_password = generate_password_hash(data['password'])
    data['password'] = hashed_password

    new_user = User(
        username=data['username'],
        password=data['password'],
        first_name=data['first_name'],
        last_name=data['last_name']
    )

    try:
        session = current_app.Session()
        session.add(new_user)
        session.commit()
        new_user_dict = new_user.to_dict()
    except Exception as e:
        current_app.logger.error(f"Error creating user: {e}")
        return jsonify({"message": "Failed to create user", "error": f"{e}"}), 500
    finally:
        session.close()

    return jsonify({"message": "User created successfully", "user": new_user_dict}), 201

@users_bp.route('/', methods=['PUT'])
@jwt_required()
def update_user():
    data = request.get_json()
    user_id = request.args.get('user_id', type=int)
    requesting_user_id = int(get_jwt_identity())

    if user_id is None:
        return jsonify({"message": "User ID is required"}), 400
    
    if requesting_user_id != user_id:
        return jsonify({"message": "Unauthorized to update this user"}), 403
    
    try:
        session = current_app.Session()
        user = session.query(User).filter_by(id=user_id).first()

        if user is None:
            session.close()
            return jsonify({"message": "User not found"}), 404
        
        # Hash the password if it is provided
        if 'password' in data:
            data['password'] = generate_password_hash(data['password'])

        for key, value in data.items():
            if hasattr(user, key) and key != 'user_id':
                setattr(user, key, value)

        user_dict = user.to_dict()
        session.commit()
    except Exception as e:
        current_app.logger.error(f"Error updating user: {e}")
        return jsonify({"message": "Failed to update user", "error": f"{e}"}), 500
    finally:
        session.close()
    
    return jsonify({"message": "User updated successfully", "user": user_dict}), 200

@users_bp.route('/', methods=['DELETE'])
@jwt_required()
def delete_user():
    user_id = request.args.get('user_id', type=int)
    requesting_user_id = int(get_jwt_identity())

    if user_id is None:
        return jsonify({"message": "User ID is required"}), 400
    
    if requesting_user_id != user_id:
        return jsonify({"message": "Unauthorized to delete this user"}), 403
    
    try:
        session = current_app.Session()
        user = session.query(User).filter_by(id=user_id).first()

        if user is None:
            session.close()
            return jsonify({"message": "User not found"}), 404
        
        session.delete(user)
        session.commit()
    except Exception as e:
        current_app.logger.error(f"Error deleting user: {e}")
        return jsonify({"message": "Failed to delete user", "error": f"{e}"}), 500
    finally:
        session.close()
    
    # Placeholder for deleting a user
    return jsonify({"message": "User deleted successfully"}), 200

@users_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not all(key in data for key in ('username', 'password')):
        return jsonify({"message": "Missing required fields"}), 400
    
    session = current_app.Session()
    user = session.query(User).filter_by(username=data['username']).first()
    user_dict = user.to_dict() if user else None

    if user and check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=str(user.id))
        session.close()
        return jsonify({"access_token": access_token, "user": user_dict}), 200
    else:
        session.close()
        return jsonify({"message": "Invalid username or password"}), 401