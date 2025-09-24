from flask import Blueprint, jsonify, request
from models import User
from manage import db

bp = Blueprint('api_bp', __name__)

@bp.route('/health')
def health():
    return jsonify({'status':'ok', 'message':'API is running', 'version':'1.0.0', 'author':'Organiums'}), 200

@bp.route('/users', methods=['GET'])
def list_users():
    users = User.query.all()
    return jsonify([{'id':u.id,'email':u.email,'name':u.name} for u in users]), 200

@bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    if not data.get('email') or not data.get('password'):
        return jsonify({'error':'email and password required'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error':'email exists'}), 409
    user = User(email=data['email'], name=data.get('name'))
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'id': user.id, 'email': user.email}), 201
