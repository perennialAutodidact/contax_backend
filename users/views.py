import jwt
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import (
    api_view, permission_classes,
    authentication_classes
)

from .authentication import SafeJWTAuthentication
from .models import User, RefreshToken
from .serializers import UserCreateSerializer, UserDetailSerializer
from contacts.serializers import ContactCreateSerializer
from .utils import generate_access_token, generate_refresh_token
from contacts.utils import generate_phone_number
from datetime import date

from contacts.utils import set_default_contacts


def listify_serializer_errors(serializer_errors):
    '''Return serializer errors into a list of strings'''
    errors = []
    for key in serializer_errors.keys():
        for message in serializer_errors[key]:
            # only display username exists error on user update
            if key == 'username':
                continue
            
            errors.append(f"{key.capitalize()}: {message}")

    return errors



@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    '''Validate request POST data and create new User objects in database
    Set refresh cookie and return access token on successful registration'''
    # create response object
    response = Response()

    # extract form data from request
    form_data = request.data['form_data']

    # add email as defaut username
    form_data['username'] = form_data['email']

    # serialize request JSON data
    new_user_serializer = UserCreateSerializer(data=form_data)

    if form_data.get('password') != form_data.get('password_2'):
        # if password and password2 don't match return status 400
        response.data = {'message': "Passwords don't match"}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return response

    if new_user_serializer.is_valid():

        # If the data is valid, create the item in the database
        new_user = new_user_serializer.save()

        # generate access and refresh tokens for the new user
        access_token = generate_access_token(new_user)
        refresh_token = generate_refresh_token(new_user)

        # Create refresh token in the database
        RefreshToken.objects.create(token=refresh_token, user=new_user)

        # attach the access token to the response data
        # and set the response status code to 201
        response.data = {
            'accessToken': access_token,
            'user': new_user_serializer.validated_data
        }
        response.status_code = status.HTTP_201_CREATED

        # create refreshtoken cookie
        response.set_cookie(
            key='refreshtoken',  # cookie name
            value=refresh_token,  # cookie value
            httponly=True,  # to help prevent XSS attacks
            samesite='None',  # to help prevent XSS attacks
            secure=True # for https connections only
        )



        # return successful response
        return response

    # if the serialized data is NOT valid
    # send a response with error messages and status code 400
    
    response.data = {
        'message': listify_serializer_errors(new_user_serializer.errors)
    }

    response.status_code = status.HTTP_400_BAD_REQUEST
    # return failed response
    return response




@api_view(['POST'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def login(request):
    '''
    POST: Validate User credentials and generate refresh and access tokens
    '''
    # create response object
    response = Response()

    form_data = request.data

    email = form_data.get('email')
    password = form_data.get('password')

    if email is None or password is None:
        response.data = {'message': 'Email and password required.'}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return response

    user = User.objects.filter(email=email).first()


    if user is None or not user.check_password(password):
        response.data = {
            'message': 'Incorrect email or password'
        }
        response.status_code = status.HTTP_400_BAD_REQUEST
        return response
    
    # reset the guest account if needed
    if user.email == 'guest@contax.com':
        set_default_contacts()

    # generate access and refresh tokens for the current user
    access_token = generate_access_token(user)
    refresh_token = generate_refresh_token(user)

    try:
        # if the user has a refresh token in the db,
        # get the old token
        old_refresh_token = RefreshToken.objects.get(user=user.id)
        # delete the old token
        old_refresh_token.delete()
        # generate new token
        RefreshToken.objects.create(user=user, token=refresh_token)

    except RefreshToken.DoesNotExist:

        # assign a new refresh token to the current user
        RefreshToken.objects.create(user=user, token=refresh_token)

    # create refreshtoken cookie
    response.set_cookie(
        key='refreshtoken',  # cookie name
        value=refresh_token,  # cookie value
        httponly=True,  # to help prevent XSS
        samesite='None',  # to help prevent XSS
        secure=True # for https connections only
    )

    # return the access token in the reponse
    response.data = {
        'refreshToken': refresh_token,
        'accessToken': access_token,
        'message': 'Login successful!',
        'user': UserDetailSerializer(user).data
    }
    response.status_code = status.HTTP_200_OK
    return response




@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([SafeJWTAuthentication])
@ensure_csrf_cookie
def auth(request):
    '''Return the user data for the user id contained in a valid access token'''
    # create response object
    response = Response()

    # Get the access token from headers
    access_token = request.headers.get('Authorization')

    # if the access token doesn't exist, return 401
    if access_token is None:
        response.data = {'message': 'No access token'}
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return response

    # remove 'token' prefix
    access_token = access_token.split(' ')[1]

    # decode access token payload
    payload = jwt.decode(
        access_token,
        settings.SECRET_KEY,
        algorithms=['HS256']
    )

    # get the user with the same id as the token's user_id
    user = User.objects.filter(id=payload.get('user_id')).first()

    if user is None:
        response.data = {'message': 'User not found'}
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return response

    if not user.is_active:
        response.data = {'message': 'User not active'}
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return response

    # serialize the User object and attach to response data
    serialized_user = UserDetailSerializer(instance=user)
    response.data = {'user': serialized_user.data}
    return response




@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def extend_token(request):
    '''Return new access token if request's refresh token cookie is valid'''
    # create response object
    response = Response()


    # get the refresh token cookie
    refresh_token = request.COOKIES.get('refreshtoken')


    # if the refresh token doesn't exist
    # return 401 - Unauthorized
    if refresh_token is None:
        response.data = {
            'message': 'Authentication credentials were not provided'
        }

        response.status_code = status.HTTP_401_UNAUTHORIZED
        return response

    # if the refresh_token doesn't exist in the database,
    # return 401 - Unauthorized
    user_refresh_token = RefreshToken.objects.filter(
        token=refresh_token).first()

    if user_refresh_token is None:
        response.data = {
            'message': 'Authentication credentials were not provided'
        }

        response.status_code = status.HTTP_401_UNAUTHORIZED
        return response

    # if a token is found,
    # try to decode it
    try:
        payload = jwt.decode(
            refresh_token,
            settings.REFRESH_TOKEN_SECRET,
            algorithms=['HS256']
        )

    # if the token is expired, delete it from the database
    # return 401 Unauthorized
    except jwt.ExpiredSignatureError:
        # find the expired token in the database
        expired_token = RefreshToken.objects.filter(
            token=refresh_token).first()

        # delete the old token
        expired_token.delete()

        response.data = {
            'message': 'Expired refresh token, please log in again.'
        }
        response.status_code = status.HTTP_401_UNAUTHORIZED

        # remove exipred refresh token cookie
        response.delete_cookie('refreshtoken')
        return response

    # if the token is valid,
    # get the user asscoiated with token
    user = User.objects.filter(id=payload.get('user_id')).first()
    if user is None:
        response.data = {
            'message': 'User not found'
        }
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return response

    if not user.is_active:
        response.data = {
            'message': 'User is inactive'
        }
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return response

    # generate new refresh token for the user
    new_refresh_token = generate_refresh_token(user)

    # Delete old refresh token
    # if the user has a refresh token in the db,
    # get the old token
    old_refresh_token = RefreshToken.objects.filter(user=user.id).all().delete()

    # assign a new refresh token to the current user
    RefreshToken.objects.create(user=user, token=new_refresh_token)

    # change refreshtoken cookie
    response.set_cookie(
        key='refreshtoken',  # cookie name
        value=new_refresh_token,  # cookie value
        httponly=True,  # to help prevent XSS attacks
        samesite='None',  # to help prevent XSS attacks
        secure=True # for https connections only
    )

    # generate new access token for the user
    new_access_token = generate_access_token(user)

    expiry = settings.ACCESS_TOKEN_EXPIRY
    now = datetime.now()
    delta = timedelta(
        days=expiry['days'],
        hours=expiry['hours'],
        minutes=expiry['minutes'],
        seconds=expiry['seconds'],
    )

    token_expiry = (now + delta).strftime("%Y-%m-%d %H:%M:%S")

    response.data = {
        'accessToken': new_access_token,
        'tokenExpiry': token_expiry,
        'user': UserDetailSerializer(user).data
    }
    
    return response




@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([SafeJWTAuthentication])
@ensure_csrf_cookie
def user_detail(request, pk):
    '''
    GET: Get the user data associated with the pk
    POST: Update the user data associated with the pk
    '''
    # Create response object
    response = Response()

    # find the user associated with
    # the pk passed in the url
    user = User.objects.filter(pk=pk).first()

    if user is None:
        response.data = {
            'message': ['User not found']
        }
        response.status_code = status.HTTP_401_UNAUTHORIZED

        return response

    if not user.is_active:
        response.data = {
            'message': ['User is inactive']
        }
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return response

    # Get the access token from request headers
    access_token = request.headers.get('Authorization').split(' ')[1]

    # decode token payload
    payload = jwt.decode(
        access_token,
        settings.SECRET_KEY,
        algorithms=['HS256']
    )

    # reject the request if the requested
    # pk is not the owner of the token
    if pk != payload.get('user_id'):
        response.data = {
            'message': ['Not authorized']
        }
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return response

    # GET = view user details
    if request.method == 'GET':
        serialized_user = UserDetailSerializer(instance=user)

        response.data = {'user': serialized_user.data}
        response.status_code = status.HTTP_200_OK

        return response

    # PUT = update user info
    if request.method == 'PUT':

        # partial = True will allow for User fields to be missing
        serialized_user = UserCreateSerializer(data=request.data, partial=True)

        if serialized_user.is_valid():
            # combine updated with the current user instance and serialize
            serialized_user.update(
                instance=user, validated_data=serialized_user.validated_data)
            response.data = {'message': ['Account info updated successffully']}
            response.status_code = status.HTTP_202_ACCEPTED
            return response

        response.data = {'message': serialized_user.errors}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return response


@api_view(['POST'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def logout(request):
    '''Delete refresh token from the database
    and delete the refreshtoken cookie'''
    # Create response object
    response = Response()

    client_refresh_token = request.COOKIES.get('refreshtoken')

    if client_refresh_token is None:
        response.data = {'message': ['Not logged in']}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return response

    # find the logged in user's refresh token
    db_refresh_token = RefreshToken.objects.filter(
        token=client_refresh_token).first()

    if db_refresh_token:
        # if the token is found, delete it
        db_refresh_token.delete()

    # delete the refresh cookie
    response.delete_cookie('refreshtoken')

    response.data = {
        'message': ['Logout successful. See you next time!']
    }

    return response
