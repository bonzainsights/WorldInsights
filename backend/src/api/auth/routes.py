from flask import request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from src.api.auth import bp
from src.services.auth_service import register_user, authenticate_user, send_verification_email
from src.extensions import limiter

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    terms_accepted = data.get('terms_accepted', False)
    
    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400
        
    user, error = register_user(username, email, password, terms_accepted)
    if error:
        return jsonify({'error': error}), 400
        
    # Send verification (mock URL for now)
    # in real world, we pass the frontend URL from config
    send_verification_email(user, "http://localhost:3000")
    
    return jsonify({'message': 'Registration successful. Please verify email.', 'user_id': user.id}), 201



@bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Missing credentials'}), 400
        
    user, error = authenticate_user(email, password)
    if error:
        return jsonify({'error': error}), 401
        
    login_user(user)
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict()
    })

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@bp.route('/me', methods=['GET'])
@login_required
def me():
    return jsonify({'user': current_user.to_dict()})
