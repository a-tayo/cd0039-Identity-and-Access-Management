from hashlib import new
import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

# db_drop_and_create_all()

# ROUTES

@app.route("/drinks", methods=['GET'])
def get_drinks():
    try:
        drinks = Drink.query.all()
    except:
        abort(500)

    short_drinks = [drink.short() for drink in drinks]
    return jsonify({
        "success": True,
        "drinks": short_drinks
    })

@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail():
    try:
        drinks = Drink.query.all()
    except:
        abort(500)

    long_drinks = [drink.long() for drink in drinks]

    return jsonify({
        "success": True,
        "drinks": long_drinks
    })

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drinks():
    drink_data = request.get_json()

    new_drink = Drink(
        title=drink_data['title'] if 'title' in drink_data else abort(422),
        recipe=json.dumps(drink_data['recipe']) if 'recipe' in drink_data else abort(422)
    )

    try:
        new_drink.insert()
    except Exception as e:
        abort(422)

    return jsonify({
        'success': True,
        'message': f"{drink_data['title']} listed successfuly",
        'drinks': new_drink.short()
    })

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(id):
    new_data = request.get_json()
    drink = Drink.query.get_or_404(id)

    drink.title = new_data['title'] if 'title' in new_data else drink.title
    drink.recipe = json.dumps(new_data['recipe']) if 'recipe' in new_data else drink.recipe
    
    try:
        drink.update()
    except:
        abort(422)

    return jsonify({
        'success': True,
        'drinks': [drink.short()]
        })

@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(id):
    drink = Drink.query.get_or_404(id)
    try:
        drink.delete()
    except:
        abort(422)

    return jsonify({
        'success': True,
        'delete': id
        })

# Error Handling

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 400,
        'message': error.description
    }), 400

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": error.description
    }), 422


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": error.description
    }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": error.description
    }), 404

'''
implement error handler for AuthError
'''
@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": error.description
    }), 401

# permission error
@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": error.description
        }), 403
