from django.contrib.auth import login, logout, authenticate
from django.shortcuts import redirect
from django.views import View
from rest_framework import status
from .serializers import UserSerializer
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import User
from ..files.models import File
from django.db.models import Q
from django.conf import settings
import os
from datetime import datetime, timedelta, timezone
from ..logger import logger
from django.shortcuts import render
from django.middleware.csrf import get_token
import json


class RegistrationView(View):
    def post(self, request):
        logger.debug('Entering RegistrationView.post function')
        logger.debug('Popping is_admin and is_superuser fields if provided somehow...')
        data = json.loads(request.body.decode('utf-8'))
        data.pop('is_admin', None)
        data.pop('is_superuser', None)
        logger.debug('Popped is_admin and is_superuser fields')

        logger.debug('Creating serializer based on UserSerializer...')
        serializer = UserSerializer(data=data)
        logger.debug('Created serializer based on UserSerializer')

        logger.debug('Checking serializer.is_valid...')
        if serializer.is_valid():
            logger.debug('Checked, serializer.is_valid confirmed')
            logger.debug('Creating new_user from request.data...')
            username = data.get('username')
            password = data.get('password')
            data.pop('username')
            data.pop('password')
            new_user = User.objects.create_user(username=username, password=password, **data)
            logger.debug('Created new_user from request.data')
            logger.debug('Creating path to user_folder...')
            user_folder = os.path.join(settings.MEDIA_ROOT, str(new_user.id))
            logger.debug('Created path to user_folder')
            logger.debug('Creating user_folder...')
            os.makedirs(user_folder)
            logger.debug('Created user_folder')
            logger.debug('Setting new_user.storage_path using user_folder...')
            new_user.storage_path = user_folder
            logger.debug('Set new_user.storage_path using user_folder')
            logger.debug('Saving new user...')
            new_user.save()
            logger.debug('New user saved')

            logger.debug('Authenticating user...')
            user = authenticate(request, username=username, password=password)
            if user:
                logger.debug('Authenticated user')
                logger.debug('Starting login user...')
                login(request, user)
                logger.debug('Finished login user')
                logger.debug('Redirecting home')
                return redirect('/home/')
            else:
                logger.error('Authentication failed')
                return JsonResponse({'error': 'Authentication failed'})

        logger.error(serializer.errors)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        csrf_token = get_token(request)
        response = render(request, 'index.html')
        response.set_cookie('csrftoken', csrf_token)
        logger.debug('RegistrationView.get, rendering page and sending csrf_token')
        return response


class LoginView(View):
    def post(self, request):
        logger.debug('Entering LoginView.post function')
        data = json.loads(request.body.decode('utf-8'))
        username = data.get('username')
        password = data.get('password')
        logger.debug('Authenticating user...')
        user = authenticate(request, username=username, password=password)
        if user:
            logger.debug('Authenticated user')
            logger.debug('Starting login user...')
            login(request, user)
            logger.debug('Finished login user')

            logger.debug('Exiting LoginView.post function and redirecting home')
            return redirect('/home/')
        else:
            logger.error('Invalid credentials')
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

    def get(self, request):
        csrf_token = get_token(request)
        logout(request)
        response = render(request, 'index.html')
        response.set_cookie('csrftoken', csrf_token)
        logger.debug('LoginView.get, rendering page and sending csrf_token')
        return response


class LogoutView(View):
    def post(self, request):
        logger.debug('Entering LogoutView.post function')
        if not request.user.is_authenticated:
            logger.error('Logged out already')
            return JsonResponse({'error': 'Logged out already'}, status=403)

        logger.debug('Starting logout user...')
        logout(request)
        logger.debug('Finished logout user')

        logger.debug('Exiting LogoutView.post function and '
                     'redirecting to main page')
        return redirect('/')

    def get(self, request):
        logger.debug('LogoutView.get, rendering page')
        return render(request, 'index.html')


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class HomeView(View):
    def get(self, request):
        logger.debug('Entering HomeView.get function')
        if not request.user.is_authenticated:
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)

        logger.info("Welcome to your home storage page!")
        logger.debug('Exiting HomeView.get function and rendering home page')
        return render(request, 'index.html')


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class AllUsersAdminView(View):
    def get(self, request):
        logger.debug('Entering AllUsersAdminView.get function')
        if not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)
        logger.debug('Exiting AllUsersAdminView.get function and rendering users page')
        return render(request, 'index.html')


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class AdminView(View):
    def get(self, request):
        logger.debug('Entering AdminView.get function')
        if not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)

        logger.info('Greeting admin!')
        logger.debug('Exiting AdminView.get function and rendering admin home page')
        return render(request, 'index.html')


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class AllFilesAdminView(View):
    def get(self, request):
        logger.debug('Entering AllFilesAdminView.get function')
        if not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)

        logger.debug('Exiting AllFilesAdminView.get function and rendering admin files page')
        return render(request, 'index.html')


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class GetFilesAdminView(View):
    def get(self, request):
        logger.debug('Entering GetFilesAdmin.get function')
        if not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)

        sort_field = request.GET.get('sort')

        if not sort_field:
            logger.error('Sort parameter is required')
            return JsonResponse({'error': 'Sort parameter is required'}, status=400)

        files = File.objects

        filter_field = request.GET.get('filter')

        if filter_field == 'user_id':
            logger.debug('Filter = user_id case')
            user_id = request.GET.get('filter_value')
            if user_id and user_id.isdigit():
                logger.debug('Getting files filtered by user_id...')
                files = files.filter(user=user_id)
                if files:
                    logger.debug('Got files filtered by user_id')
                else:
                    logger.debug('Files not found by user_id')
                    logger.debug('Getting user by user_id...')
                    user = User.objects.get(id=user_id)
                    if user:
                        logger.debug('Got user')
                        logger.debug('Setting files empty...')
                        files = []
                        logger.debug('Set files empty')
                    else:
                        logger.error('User not found')

        elif filter_field == 'username':
            logger.debug('Filter = username case')
            username = request.GET.get('filter_value')
            if username:
                logger.debug('Getting user by username...')
                user = User.objects.get(username=username)
                if user:
                    logger.debug('Got user by username')
                    logger.debug('Getting files filtered by user_id...')
                    files = files.filter(user=user.id)
                else:
                    logger.error('User not found')

        elif filter_field == 'original_name':
            logger.debug('Filter = original_name case')
            original_name = request.GET.get('filter_value')
            if original_name:
                logger.debug('Getting files filtered by original_name(contains)...')
                files = files.filter(original_name__icontains=original_name)
                if files:
                    logger.debug('Got files filtered by original_name')
                else:
                    logger.error('Files not found by original name')

        elif filter_field == 'name':
            logger.debug('Filter = name case')
            name = request.GET.get('filter_value')
            if name:
                logger.debug('Getting files filtered by name(contains)...')
                files = files.filter(name__icontains=name)
                if files:
                    logger.debug('Got files filtered by name')
                else:
                    logger.error('Files not found by name')

        elif filter_field == 'size':
            logger.debug('Filter = size case')
            size = request.GET.get('filter_value')
            if size and size.isdigit():
                logger.debug('Getting files filtered by size(+-10%)...')
                files = files.filter(Q(size__gte=int(size) * 0.9) & Q(size__lte=int(size) * 1.1))
                if files:
                    logger.debug('Got files filtered by size')
                else:
                    logger.error('Files not found by size')

        elif filter_field == 'upload_date':
            logger.debug('Filter = upload_date case')
            upload_date = request.GET.get('filter_value')
            if upload_date:
                try:
                    logger.debug('Getting files filtered by upload_date...')
                    upload_date = datetime.strptime(upload_date, '%d.%m.%Y')
                    files = files.filter(upload_date__gte=upload_date)
                except ValueError:
                    logger.error('Invalid upload_date format')
                if files:
                    logger.debug('Got files filtered by upload_date')
                else:
                    logger.error('Files not found by upload_date')

        elif filter_field == 'last_download_date':
            logger.debug('Filter = last_download_date case')
            last_download_date = request.GET.get('filter_value')
            if last_download_date:
                try:
                    logger.debug('Getting files filtered by last_download_date...')
                    last_download_date = datetime.strptime(last_download_date, '%d.%m.%Y')
                    files = files.filter(last_download_date__gte=last_download_date)
                except ValueError:
                    logger.error('Invalid upload_date format')
                if files:
                    logger.debug('Got files filtered by last_download_date')
                else:
                    logger.error('Files not found by last_download_date')
        else:
            logger.debug('No filter case')
            logger.debug('Getting current_date(utc)...')
            current_date = datetime.now(timezone.utc)
            logger.debug('Got current_date')
            logger.debug('Getting start_date(utc)...')
            start_date = current_date - timedelta(days=1)
            logger.debug('Got current_date')
            logger.debug('Getting files filtered by upload_date < 1day...')
            files = files.filter(upload_date__gte=start_date)
            if files:
                logger.debug('Got files filtered by last_download_date')
            else:
                logger.debug('Files not found by last_download_date')
                logger.debug('Exiting AllFilesAdminView.get function and responding '
                             'with "files": files (empty)')
                file_list = []
                return JsonResponse({'files': file_list})

        if files:
            logger.debug('Starting files order_by sort_filed...')
            files = files.order_by(sort_field)
            logger.debug('Finished files order_by sort_filed')

        logger.debug('Starting file_list preparation...')
        file_list = []
        for file in files:
            file_data = {
                'id': file.id,
                'name': file.name,
                'comment': file.comment,
                'size': file.size,
                'upload_date': str(file.upload_date),
                'last_download_date': str(file.last_download_date)
            }
            file_list.append(file_data)
        logger.debug('Finished file_list preparation')

        logger.debug('Exiting AllFilesAdminView.get function and  responding '
                     'with "files": file_list')
        return JsonResponse({'files': file_list})


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class CreateUserAdminView(View):
    def post(self, request):
        logger.debug('Entering CreateUserAdminView.post function')
        if not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)

        case = 'user'
        data = json.loads(request.body.decode('utf-8'))
        permissions = data.get('permissions')
        if permissions.get('is_admin'):
            logger.debug('Setting admin permissions...')
            case = 'admin'
            logger.debug('Set admin permissions')

        if permissions.get('is_superuser'):
            logger.debug('Setting superuser permissions...')
            case = 'superuser'
            logger.debug('Set superuser permissions')

        data.pop('permissions', None)
        logger.debug('Creating serializer based on UserSerializer...')
        serializer = UserSerializer(data=data)
        logger.debug('Created serializer based on UserSerializer')

        logger.debug('Checking serializer.is_valid...')
        if serializer.is_valid():
            logger.debug('Checked, serializer.is_valid confirmed')
            logger.debug('Creating new_user from request.data...')
            username = data.get('username')
            password = data.get('password')
            data.pop('username')
            data.pop('password')
            if case == 'user':
                new_user = User.objects.create_user(username=username, password=password, **data)
            elif case == 'admin':
                new_user = User.objects.create_admin(username=username, password=password, **data)
            elif case == 'superuser':
                if not request.user.is_superuser:
                    logger.error('Access denied')
                    return JsonResponse({'error': 'Access denied'}, status=403)
                new_user = User.objects.create_superuser(username=username, password=password, **data)
            logger.debug('Created new_user from request.data')
            logger.debug('Creating path to user_folder...')
            user_folder = os.path.join(settings.MEDIA_ROOT, str(new_user.id))
            logger.debug('Created path to user_folder')
            logger.debug('Creating user_folder...')
            os.makedirs(user_folder)
            logger.debug('Created user_folder')
            logger.debug('Setting new_user.storage_path using user_folder...')
            new_user.storage_path = user_folder
            logger.debug('Set new_user.storage_path using user_folder')
            logger.debug('Saving new user...')
            new_user.save()
            logger.debug('New user saved')

            logger.debug('Exiting AllFilesAdminView.get function and responding '
                         'with "message": "User created"')
            return JsonResponse({'message': 'User created'})

        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        if not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)
        logger.debug('CreateUserAdminView.get, rendering page')
        return render(request, 'index.html')


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ChangeUserAdminView(View):
    def delete(self, request, user_id):
        logger.debug('Entering ChangeUserAdminView.delete function')
        if not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)
        logger.debug('Getting user by id...')
        user = get_object_or_404(User, id=user_id)

        if user.is_superuser:
            if not request.user.is_superuser:
                logger.error('Access denied')
                return JsonResponse({'error': 'Access denied'}, status=403)
        logger.debug('Got user by id')
        logger.debug('Deleting user...')
        user.delete()
        logger.debug('Deleted user')

        logger.debug('Exiting ChangeUserAdminView.delete function and responding '
                     'with "message": "User deleted successfully"')
        return JsonResponse({'message': 'User deleted successfully'})

    def patch(self, request, user_id):
        logger.debug('Entering ChangeUserAdminView.patch function')
        if not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)
        logger.debug('Getting user by id...')
        user = get_object_or_404(User, id=user_id)
        logger.debug('Toggling user.is_admin...')
        user.is_admin = not user.is_admin
        user.save()
        logger.debug('Toggled user.is_admin')
        logger.debug('Exiting ChangeUserAdminView.patch function and responding '
                     'with "message": "User rights updated successfully"')
        return JsonResponse({'message': 'User rights updated successfully'})


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class GetUsersAdminView(View):
    def get(self, request):
        logger.debug('Entering GetUsersAdminView.get function')
        if not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)
        logger.debug('Preparing User.objects...')
        users = User.objects.all()
        logger.debug('Prepared User.objects')
        logger.debug('Preparing user_list...')
        user_list = []
        logger.debug('Prepared user_list')
        logger.debug('Writing user_data to user_list...')
        for user in users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email,
                'is_admin': 'Yes' if user.is_admin else 'No',
                'is_superuser': 'Yes' if user.is_superuser else 'No',
            }
            user_list.append(user_data)
        logger.debug('Finished writing user_data to user_list')

        logger.debug('Exiting GetUsersAdminView.get function and responding '
                     'with "users": user_list')
        return JsonResponse({'users': user_list})


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class RedirectView(View):
    def get(self, request):
        logger.debug('Entering RedirectView.get function')
        logger.debug('Exiting RedirectView.get function and redirecting to /home/')
        return redirect('/home/')
