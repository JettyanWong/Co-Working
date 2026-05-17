from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models import User
import re

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=['POST'])
@limiter.limit("10/minute")
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({'error': 'Missing required fields'}), 400

    if len(data['username']) < 3 or len(data['username']) > 50:
        return jsonify({'error': 'Username must be 3-50 characters'}), 400

    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    email_re = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_re, data['email']):
        return jsonify({'error': 'Invalid email format'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400

    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': '注册成功，请等待管理员审核'}), 201


@bp.route('/login', methods=['POST'])
@limiter.limit("20/minute")
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400

    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401

    if user.status == 'pending':
        return jsonify({'error': '账号尚未通过管理员审核，请等待审核通过后再登录'}), 403
    if user.status == 'disabled':
        return jsonify({'error': '账号已被禁用，请联系管理员'}), 403

    login_user(user)
    return jsonify({'message': 'Login successful', 'user': user.to_dict()})


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logout successful'})


@bp.route('/me', methods=['GET'])
@login_required
def me():
    return jsonify({'user': current_user.to_dict()})


@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({'error': 'Missing current_password or new_password'}), 400

    if len(new_password) < 8:
        return jsonify({'error': 'New password must be at least 8 characters'}), 400

    if not current_user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect'}), 401

    current_user.set_password(new_password)
    db.session.commit()

    return jsonify({'message': 'Password changed successfully'})
