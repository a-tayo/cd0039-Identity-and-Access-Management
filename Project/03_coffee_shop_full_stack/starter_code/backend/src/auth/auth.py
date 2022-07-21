import json
import re
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen

from sqlalchemy import desc


AUTH0_DOMAIN = 'coffeeapp95.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffee'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

def get_token_auth_header():
    auth = request.headers.get('Authorization', None)
    if not auth:
        raise AuthError({'code':'Invalid header',
        'description': 'Missing Authorization header'
        }, 401)

    parts = auth.split()

    if not parts[1]:
        raise AuthError({'description':'Authorization token not in header'}, 401)
    elif parts[0].lower() != 'bearer':
        raise AuthError({'description':'Authorization header should be a bearer token'}, 401)
    elif len(parts) > 2:
        raise AuthError({'description':'Authorization header has more than 2 parts'}, 401)
    return parts[1]

def check_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError({'description':'InvalidHeader'}, 403)
    elif permission not in payload['permissions']:
        raise AuthError({'description':'You are Not Allowed to make this request'}, 403)
    return True


def verify_decode_jwt(token):
    rsa_key = {}

    jsonurl= urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)

    if 'kid' not in unverified_header:
        raise AuthError({'description':'InvalidHeader'}, 401)
    
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
                )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({'code':'Token Expired',
            'description':'ExpiredSignature'}, 401)

        except jwt.JWTClaimsError:
            raise AuthError({'code':'Ivalid claims',
            'description':'Incorrect claims please check the audience and issuer'}, 401)
        except:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
        'code': 'InvalidHeader',
        'description': 'Invalid Authorization header.'}, 401)
    
            
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                print('Getting token from header...')
                token = get_token_auth_header()
                print('Success')
            except:
                print('Authorization token not found in header!')
                abort(401)
            try:
                print('Verifying token...')
                payload = verify_decode_jwt(token)
                print('v: token verified')
            except:
                print('Token verification failed!')
                abort(403)
            try:
                print('Checking permissions...')
                check_permissions(permission, payload)
                print('Permission check successful')
            except:
                print('Required permission not present!')
                abort(403)

            return f(*args, **kwargs)

        return wrapper
    return requires_auth_decorator