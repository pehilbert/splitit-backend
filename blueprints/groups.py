from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from model import Group, User, group_membership

groups_bp = Blueprint('groups', __name__, url_prefix='/groups')

@groups_bp.route('/', methods=['GET'])
def get_groups():
    group_id = request.args.get('group_id', type=int)
    user_id = request.args.get('user_id', type=int)
    session = current_app.Session()

    if group_id is not None:
        try:
            group = session.query(Group).filter_by(id=group_id).first()
            if group is None:
                return jsonify({"message": "Group not found"}), 404
            group_dict = group.to_dict()
        except Exception as e:
            current_app.logger.error(f"Error fetching group: {e}")
            return jsonify({"message": "Failed to fetch group", "error": f"{e}"}), 500
        finally:
            session.close()
        return jsonify({"groups": [group_dict]})
    elif user_id is not None:
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user is None:
                return jsonify({"message": "User not found"}), 404
            groups_list = [group.to_dict() for group in user.groups]
        except Exception as e:
            current_app.logger.error(f"Error fetching groups for user: {e}")
            return jsonify({"message": "Failed to fetch groups", "error": f"{e}"}), 500
        finally:
            session.close()
        return jsonify({"groups": groups_list})
    else:
        try:
            groups = session.query(Group).all()
            groups_list = [group.to_dict() for group in groups]
        except Exception as e:
            current_app.logger.error(f"Error fetching groups: {e}")
            return jsonify({"message": "Failed to fetch groups", "error": f"{e}"}), 500
        finally:
            session.close()
        return jsonify({"groups": groups_list})

@groups_bp.route('/', methods=['POST'])
@jwt_required()
def create_group():
    data = request.get_json()
    if not data or not all(key in data for key in ('name',)):
        return jsonify({"message": "Missing required fields"}), 400

    owner_id = int(get_jwt_identity())
    session = current_app.Session()
    try:
        owner = session.query(User).filter_by(id=owner_id).first()
        if not owner:
            return jsonify({"message": "Owner not found"}), 404

        new_group = Group(
            name=data['name'],
            owner_id=owner_id
        )
        session.add(new_group)
        session.commit()
        # Add owner as a member
        new_group.members.append(owner)
        session.commit()
        group_dict = new_group.to_dict()
    except Exception as e:
        current_app.logger.error(f"Error creating group: {e}")
        return jsonify({"message": "Failed to create group", "error": f"{e}"}), 500
    finally:
        session.close()
    return jsonify({"message": "Group created successfully", "group": group_dict}), 201

@groups_bp.route('/', methods=['PUT'])
@jwt_required()
def update_group():
    data = request.get_json()
    group_id = request.args.get('group_id', type=int)
    requesting_user_id = int(get_jwt_identity())

    if group_id is None:
        return jsonify({"message": "Group ID is required"}), 400

    session = current_app.Session()
    try:
        group = session.query(Group).filter_by(id=group_id).first()
        if group is None:
            return jsonify({"message": "Group not found"}), 404
        if group.owner_id != requesting_user_id:
            return jsonify({"message": "Unauthorized to update this group"}), 403

        for key, value in data.items():
            if hasattr(group, key) and key not in ('id', 'owner_id', 'expenses', 'members'):
                setattr(group, key, value)
        session.commit()
        group_dict = group.to_dict()
    except Exception as e:
        current_app.logger.error(f"Error updating group: {e}")
        return jsonify({"message": "Failed to update group", "error": f"{e}"}), 500
    finally:
        session.close()
    return jsonify({"message": "Group updated successfully", "group": group_dict}), 200

@groups_bp.route('/', methods=['DELETE'])
@jwt_required()
def delete_group():
    group_id = request.args.get('group_id', type=int)
    requesting_user_id = int(get_jwt_identity())

    if group_id is None:
        return jsonify({"message": "Group ID is required"}), 400

    session = current_app.Session()
    try:
        group = session.query(Group).filter_by(id=group_id).first()
        if group is None:
            return jsonify({"message": "Group not found"}), 404
        if group.owner_id != requesting_user_id:
            return jsonify({"message": "Unauthorized to delete this group"}), 403

        session.delete(group)
        session.commit()
    except Exception as e:
        current_app.logger.error(f"Error deleting group: {e}")
        return jsonify({"message": "Failed to delete group", "error": f"{e}"}), 500
    finally:
        session.close()
    return jsonify({"message": "Group deleted successfully"}), 200

@groups_bp.route("/members", methods=["POST"])
@jwt_required()
def add_member():
    group_id = request.args.get('group_id', type=int)
    data = request.get_json()
    user_id = data.get("user_id")
    requesting_user_id = int(get_jwt_identity())

    session = current_app.Session()

    try:
        group = session.get(Group, group_id)
        user = session.get(User, user_id)
        
        if group.owner_id != requesting_user_id:
            return jsonify({"message": "You don't own this group"}), 403
    
        if not group or not user:
            session.close()
            return jsonify({"message": "User or group not found"}), 404

        if user in group.members:
            session.close()
            return jsonify({"message": "User is already a member"}), 400

        group.members.append(user)
        session.commit()
    except Exception as e:
        current_app.logger.error(f"Error adding member to group: {e}")
        return jsonify({"message": "Failed to add member to group", "error": f"{e}"}), 500
    finally:
        session.close()

    return jsonify({"message": "User added to group"})

@groups_bp.route("/members", methods=["DELETE"])
@jwt_required()
def remove_member():
    group_id = request.args.get('group_id', type=int)
    data = request.get_json()
    user_id = data.get("user_id")
    requesting_user_id = int(get_jwt_identity())
    
    session = current_app.Session()

    try:
        group = session.get(Group, group_id)
        user = session.get(User, user_id)

        if group.owner_id != requesting_user_id:
            return jsonify({"message": "You don't own this group"}), 403
    
        if not group or not user:
            session.close()
            return jsonify({"message": "User or group not found"}), 404

        if user not in group.members:
            session.close()
            return jsonify({"message": "User is not a member"}), 400

        if user_id == group.owner_id:
            session.close()
            return jsonify({"message": "Cannot remove the group owner"}), 400
        
        group.members.remove(user)
        session.commit()
    except Exception as e:
        current_app.logger.error(f"Error removing member from group: {e}")
        return jsonify({"message": "Failed to remove member from group", "error": f"{e}"}), 500
    finally:
        session.close()

    return jsonify({"message": "User removed from group"})
