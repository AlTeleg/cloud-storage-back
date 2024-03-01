from django.contrib.auth import login, logout, authenticate
from django.shortcuts import redirect
from django.views import View
from rest_framework import status
from .serializers import UserSerializer
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import User
from ..files.models import File
from django.db.models import Q
from django.conf import settings
import os
from datetime import datetime, timedelta, timezone
from ..logger import logger


class RegistrationView(View):
    def post(self, request):
        logger.debug('Entering RegistrationView.post function')
        logger.debug('Popping is_admin and is_superuser fields if provided somehow...')
        request.data.pop('is_admin', None)
        request.data.pop('is_superuser', None)
        logger.debug('Popped is_admin and is_superuser fields')

        logger.debug('Creating serializer based on UserSerializer...')
        serializer = UserSerializer(data=request.data)
        logger.debug('Created serializer based on UserSerializer')

        logger.debug('Checking serializer.is_valid...')
        if serializer.is_valid():
            logger.debug('Checked, serializer.is_valid confirmed')
            logger.debug('Creating new_user from request.data...')
            new_user = User.objects.create_user(request.data)
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
            logger.debug('Authenticating user...')
            user = authenticate(request, username=new_user.username, password=new_user.password)
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


class LoginView(View):
    def post(self, request):
        logger.debug('Entering LoginView.post function')
        username = request.POST.get('username')
        password = request.POST.get('password')
        logger.debug('Authenticating user...')
        user = authenticate(request, username=username, password=password)
        if user:
            logger.debug('Authenticated user')
            logger.debug('Starting login user...')
            login(request, user)
            logger.debug('Finished login user')

            logger.debug('Exiting LoginView.post function and responding '
                         'with "message": "Authentication successful"')
            return JsonResponse({'message': 'Authentication successful'})
        else:
            logger.error('Invalid credentials')
            return JsonResponse({'error': 'Invalid credentials'}, status=401)


@login_required
class LogoutView(View):
    def post(self, request):
        logger.debug('Entering LogoutView.post function')
        if not request.user.is_authenticated:
            logger.error('Logged out already')
            return JsonResponse({'error': 'Logged out already'}, status=403)

        logger.debug('Starting logout user...')
        logout(request)
        logger.debug('Finished logout user')

        logger.debug('Exiting LogoutView.post function and responding '
                     'with "message": "Logged out successfully"')
        return JsonResponse({'message': 'Logged out successfully'})


@login_required
class HomeView(View):
    def get(self, request):
        logger.debug('Entering HomeView.get function')
        if not request.user.is_authenticated:
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)

        logger.debug('Exiting LogoutView.post function and responding '
                     'with "message": "Welcome to your home storage page!"')
        return JsonResponse({'message': 'Welcome to your home storage page!'})


@login_required
class AllUsersAdminView(View):
    def get(self, request):
        logger.debug('Entering AllUsersAdminView.get function')
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
                'username': user.username,
                'full_name': user.full_name,
                'is_admin': user.is_admin
            }
            user_list.append(user_data)
            logger.debug('Finished writing user_data to user_list')

        logger.debug('Exiting AllUsersAdminView.post function and responding '
                     'with "users": user_list')
        return JsonResponse({'users': user_list})


@login_required
class AdminView(View):
    def get(self, request):
        logger.debug('Entering AdminView.get function')
        if not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)

        logger.debug('Exiting AdminView.get function and responding '
                     'with "message": "Greetings admin!"')
        return JsonResponse({'message': 'Greetings admin!'})


@login_required
class AllFilesAdminView(View):
    def get(self, request):
        logger.debug('Entering AllFilesAdminView.get function')
        if not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)

        sort_field = request.GET.get('sort')

        if not sort_field:
            logger.error('Sort parameter is required')
            return JsonResponse({'error': 'Sort parameter is required'}, status=400)

        files = File.objects

        filter_field = request.GET.get('filter')

        if filter_field == 'user':
            logger.debug('Filter = user_id case')
            user_id = request.GET.get('user')
            if user_id and user_id.isdigit():
                logger.debug('Getting files filtered by user_id...')
                files = files.filter(user_id=user_id)
                if files:
                    logger.debug('Got files filtered by user_id')
                else:
                    logger.debug('Files not found by user_id')
                    logger.debug('Getting user by user_id...')
                    user = User.objects.filter(user_id=user_id)
                    if user:
                        logger.debug('Got user')
                        logger.debug('Setting files empty...')
                        files = []
                        logger.debug('Set files empty')
                    else:
                        logger.error('User not found')

        elif filter_field == 'original_name':
            logger.debug('Filter = original_name case')
            original_name = request.GET.get('original_name')
            if original_name:
                logger.debug('Getting files filtered by original_name(contains)...')
                files = files.filter(original_name__icontains=original_name)
                if files:
                    logger.debug('Got files filtered by original_name')
                else:
                    logger.error('Files not found by original name')

        elif filter_field == 'name':
            logger.debug('Filter = name case')
            name = request.GET.get('name')
            if name:
                logger.debug('Getting files filtered by name(contains)...')
                files = files.filter(name__icontains=name)
                if files:
                    logger.debug('Got files filtered by name')
                else:
                    logger.error('Files not found by name')

        elif filter_field == 'size':
            logger.debug('Filter = size case')
            size = request.GET.get('size')
            if size and size.isdigit():
                logger.debug('Getting files filtered by size(+-10%)...')
                files = files.filter(Q(size__gte=int(size) * 0.9) & Q(size__lte=int(size) * 1.1))
                if files:
                    logger.debug('Got files filtered by size')
                else:
                    logger.error('Files not found by size')

        elif filter_field == 'upload_date':
            logger.debug('Filter = upload_date case')
            upload_date = request.GET.get('upload_date')
            if upload_date:
                logger.debug('Getting files filtered by upload_date...')
                files = files.filter(upload_date=upload_date)
                if files:
                    logger.debug('Got files filtered by upload_date')
                else:
                    logger.error('Files not found by upload_date')

        elif filter_field == 'last_download_date':
            logger.debug('Filter = last_download_date case')
            last_download_date = request.GET.get('last_download_date');
            if last_download_date:
                logger.debug('Getting files filtered by last_download_date...')
                files = files.filter(last_download_date=last_download_date)
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
            logger.debug('Getting files filtered by last_download_date < 1day...')
            files = files.filter(last_download_date__gte=start_date)
            if files:
                logger.debug('Got files filtered by last_download_date')
            else:
                logger.debug('Files not found by last_download_date')
                logger.debug('Exiting AllFilesAdminView.get function and responding '
                             'with "files": files (empty)')
                file_list = []
                return JsonResponse({'files': file_list})

        logger.debug('Starting files order_by sort_filed...')
        files = files.order_by(sort_field)
        logger.debug('Finished files order_by sort_filed')

        logger.debug('Starting file_list preparation...')
        file_list = []
        for file in files:
            file_data = {
                'file_name': file.file_name,
                'comment': file.comment,
                'size': file.size,
                'upload_date': str(file.upload_date),
                'last_download_date': str(file.last_download_date)
            }
            file_list.append(file_data)
            logger.debug('Finished file_list preparation')

        logger.debug('Exiting AllFilesAdminView.get function and responding '
                     'with "files": file_list')
        return JsonResponse({'files': file_list})


class CreateUserAdminView(View):
    def post(self, request):
        logger.debug('Entering CreateUserAdminView.post function')
        if not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)

        permissions = request.POST.get('permissions')

        if permissions == 'admin':
            logger.debug('Setting admin permissions...')
            request.data.is_admin = True
            request.data.is_superuser = False
            logger.debug('Set admin permissions')

        if permissions == 'superuser':
            logger.debug('Setting superuser permissions...')
            request.data.is_admin = True
            request.data.is_superuser = True
            logger.debug('Set superuser permissions')

        logger.debug('Creating serializer based on UserSerializer...')
        serializer = UserSerializer(data=request.data)
        logger.debug('Created serializer based on UserSerializer')

        logger.debug('Checking serializer.is_valid...')
        if serializer.is_valid():
            logger.debug('Checked, serializer.is_valid confirmed')
            logger.debug('Creating new_user from request.data...')
            new_user = User.objects.create_user(request.data)
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

            logger.debug('Exiting AllFilesAdminView.get function and responding '
                         'with "message": "User created"')
            return JsonResponse({'message': 'User created'})
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@login_required
class DeleteUserAdminView(View):
    def delete(self, request, user_id):
        logger.debug('Entering DeleteUserAdminView.delete function')
        if not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)

        logger.debug('Getting user by id...')
        user = get_object_or_404(User, id=user_id)

        if user:
            logger.debug('Got user by id')
            logger.debug('Deleting user...')
            user.delete()
            logger.debug('Deleted user')

            logger.debug('Exiting DeleteUserAdminView.delete function and responding '
                         'with "message": "User deleted successfully"')
            return JsonResponse({'message': 'User deleted successfully'})

        logger.error('User not found by id')
        return JsonResponse({'error': 'User not found by id'})


@login_required(None, 'login', '/login/')
class RedirectView(View):
    def get(self):
        logger.debug('Entering RedirectView.get function')
        logger.debug('Exiting RedirectView.get function and redirecting to /home/')
        return redirect('/home/')
