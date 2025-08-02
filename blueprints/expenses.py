from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from model import Group, User, Expense, ExpenseSplit
import datetime

expenses_bp = Blueprint('expenses', __name__, url_prefix='/expenses')

@expenses_bp.route('/', methods=['GET'])
def get_expenses():
    group_id = request.args.get('group_id', type=int)

    if group_id is None:
        return jsonify({"message": "Group ID is required"}), 400
    
    session = current_app.Session()

    try:
        group = session.query(Group).filter_by(id=group_id).first()

        if group is None:
            session.close()
            return jsonify({"message": "Group not found"}), 404
        
        expenses = session.query(Expense).filter_by(group_id=group_id).all()
        
        group_dict = group.to_dict()
        del group_dict['expenses']  # Remove expenses from group dict to avoid redundancy
        expenses_list = [expense.to_dict() for expense in expenses]
    except Exception as e:
        current_app.logger.error(f"Error fetching expenses: {e}")
        return jsonify({"message": "Failed to fetch expenses", "error": f"{e}"}), 500
    finally:
        session.close()

    return jsonify({"group": group_dict, "expenses": expenses_list})

@expenses_bp.route('/', methods=['POST'])
@jwt_required()
def create_expense():
    group_id = request.args.get('group_id')
    data = request.get_json()
    requesting_user_id = int(get_jwt_identity())

    if group_id is None:
        return jsonify({"message": "Group ID is required"}), 400
    
    if not data or not all([key in data for key in ('title', 'description', 'total_cost', 'payer_portion', 'splits')]):
        return jsonify({"message": "Missing required fields"}), 400
    
    session = current_app.Session()

    try:
        group = session.query(Group).filter_by(id=group_id).first()

        if group is None:
            session.close()
            return jsonify({"message": "Group not found"}), 404
        
        if requesting_user_id not in [member.id for member in group.members]:
            session.close()
            return jsonify({"message": "User not a member of the group"}), 403
        
        paid_by = session.query(User).filter_by(id=requesting_user_id).first()

        if paid_by is None:
            session.close()
            return jsonify({"message": "Paid by user not found"}), 404

        if data.get('date'):
            data['date'] = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()

        new_expense = Expense(
            title=data['title'],
            description=data['description'],
            date=data.get('date', datetime.date.today()),
            totalCost=data['total_cost'],
            paid_by_id=paid_by.id,
            payer_portion=data['payer_portion'],
            group_id=group_id
        )

        session.add(new_expense)
        session.commit()

        for split in data['splits']:
            if 'user_id' not in split or 'amount_paid' not in split or 'amount_owed' not in split:
                session.rollback()
                session.delete(new_expense)
                session.commit()
                session.close()
                return jsonify({"message": "Invalid split data"}), 400
            
            if split['user_id'] not in [member.id for member in group.members]:
                session.rollback()
                session.delete(new_expense)
                session.commit()
                session.close()
                return jsonify({"message": "One or more Split users are not a member of the group"}), 403
            
            expense_split = ExpenseSplit(
                user_id=split['user_id'],
                expense_id=new_expense.id,
                amount_paid=split['amount_paid'],
                amount_owed=split['amount_owed']
            )
            session.add(expense_split)

        new_expense_dict = new_expense.to_dict()
        session.commit()
    except Exception as e:
        current_app.logger.error(f"Error creating expense: {e}")
        session.rollback()
        return jsonify({"message": "Failed to create expense", "error": f"{e}"}), 500
    finally:
        session.close()
    
    return jsonify({"message": "Expense created successfully", "expense": new_expense_dict}), 201

@expenses_bp.route('/', methods=['PUT'])
@jwt_required()
def update_expense():
    expense_id = request.args.get('expense_id', type=int)
    data = request.get_json()
    requesting_user_id = int(get_jwt_identity())

    if expense_id is None:
        return jsonify({"message": "Expense ID is required"}), 400
    
    session = current_app.Session()

    try:
        expense = session.query(Expense).filter_by(id=expense_id).first()

        if expense is None:
            session.close()
            return jsonify({"message": "Expense not found"}), 404
        
        if expense.paid_by_id != requesting_user_id and expense.group.owner_id != requesting_user_id:
            session.close()
            return jsonify({"message": "Unauthorized to update this expense"}), 403
        
        if 'date' in data:
            expense.date = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()

        for key in ('title', 'description', 'total_cost', 'payer_portion'):
            if key in data and hasattr(expense, key):
                setattr(expense, key, data[key])

        split_updates = data.get('splits', [])

        for new_split in split_updates:
            if 'user_id' not in new_split or 'amount_paid' not in new_split or 'amount_owed' not in new_split:
                session.rollback()
                session.close()
                return jsonify({"message": "Invalid split data"}), 400
            
            existing_split = session.query(ExpenseSplit).filter_by(
                expense_id=expense.id, user_id=new_split['user_id']
            ).first()

            if existing_split:
                existing_split.amount_paid = new_split['amount_paid']
                existing_split.amount_owed = new_split['amount_owed']

        expense_dict = expense.to_dict()
        session.commit()

    except Exception as e:
        current_app.logger.error(f"Error updating expense: {e}")
        return jsonify({"message": "Failed to update expense", "error": f"{e}"}), 500
    finally:
        session.close()

    return jsonify({"message": "Expense updated successfully", "expense": expense_dict}), 200

@expenses_bp.route('/', methods=['DELETE'])
@jwt_required()
def delete_expense():
    expense_id = request.args.get('expense_id', type=int)
    requesting_user_id = int(get_jwt_identity())

    if expense_id is None:
        return jsonify({"message": "Expense ID is required"}), 400
    
    session = current_app.Session()

    try:
        expense = session.query(Expense).filter_by(id=expense_id).first()
        group = session.query(Group).filter_by(id=expense.group_id).first()

        if expense is None:
            session.close()
            return jsonify({"message": "Expense not found"}), 404
        
        if expense.paid_by_id != requesting_user_id and group.owner_id != requesting_user_id:
            session.close()
            return jsonify({"message": "Unauthorized to delete this expense"}), 403

        session.delete(expense)
        session.commit()
    except Exception as e:
        current_app.logger.error(f"Error deleting expense: {e}")
        return jsonify({"message": "Failed to delete expense", "error": f"{e}"}), 500
    finally:
        session.close()

    return jsonify({"message": "Expense deleted successfully"}), 200