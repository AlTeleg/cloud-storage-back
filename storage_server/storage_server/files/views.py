import json
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from .models import File
from ..accounts.models import User
from datetime import datetime, timezone
from hashlib import sha256
import secrets
from urllib.parse import urlparse
import os
from django.conf import settings
from ..logger import logger
from django.shortcuts import render
import base64
import copy


@method_decorator(login_required, name='dispatch')
class ListView(View):
    def get(self, request):
        logger.debug('Entering ListView.get function')
        logger.debug('Exiting ListView.get function and rendering page')
        return render(request, 'index.html')


@method_decorator(login_required, name='dispatch')
class UploadView(View):
    def post(self, request):
        logger.debug('Entering UploadView.post function')
        file = request.FILES.get('file')
        comment = request.POST.get('comment')

        if not file:
            logger.error('No file provided')
            return HttpResponseBadRequest(json.dumps({'error': 'No file provided'}), content_type='application/json')

        if not comment:
            logger.debug('Empty comment')
            comment = ''

        logger.debug('Reading file_content...')
        file_content = file.read()
        logger.debug('Finished reading file_content')
        logger.debug('Initiating filename...')
        filename = os.path.join(settings.MEDIA_ROOT, str(request.user.id), file.name)
        logger.debug('Initiated filename')

        if os.path.exists(filename):
            logger.error('File with this name already exists')
            return HttpResponseBadRequest(json.dumps({'error': 'File with this name already exists'}),
                                          content_type='application/json')

        logger.debug('Creating filename...')
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        logger.debug('Created filename')

        logger.debug('Starting writing file_content...')
        with open(filename, 'wb') as f:
            f.write(file_content)
        logger.debug('Finished writing file_content')
        logger.debug(f"Creating uploaded file: user={request.user}, original_name={file.name}, size={file.size}"
                     f", comment={comment}, file_path={os.path.join(str(request.user.id), file.name)}...")
        uploaded_file = File(
            user=request.user,
            original_name=file.name,
            size=file.size,
            comment=comment,
            data=file_content,
            path=os.path.join(str(request.user.id), file.name)
        )
        logger.debug('Created uploaded file')

        logger.debug('Uploaded file saving to DB...')
        uploaded_file.save()
        logger.debug('Uploaded file saved to DB')

        logger.debug('Exiting UploadView.post function and responding with "message": "File uploaded successfully"')
        return JsonResponse({'message': 'File uploaded successfully'})

    def get(self, request):
        logger.debug('Entering UploadView.get function')
        logger.debug('Exiting UploadView.get function and rendering page')
        return render(request, 'index.html')


@method_decorator(login_required, name='dispatch')
class DeleteView(View):
    def delete(self, request, file_id):
        logger.debug('Entering DeleteView.delete function')
        logger.debug('Getting file by id...')
        file = get_object_or_404(File, id=file_id)

        logger.debug('Got file')

        if not file.user == request.user and not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)

        file.delete()

        logger.debug('Exiting DeleteView.delete function and responding with "message": "File deleted successfully"')
        return JsonResponse({'message': 'File deleted successfully'})


@method_decorator(login_required, name='dispatch')
class RenameView(View):
    def patch(self, request, file_id):
        logger.debug('Entering RenameView.patch function')
        logger.debug('Getting file by id...')
        file = get_object_or_404(File, id=file_id)

        logger.debug('Got file')

        if not file.user == request.user and not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)

        new_name = json.loads(request.body).get('name')
        if new_name:
            logger.debug('File name changing...')
            file.name = new_name
            logger.debug('File name changed')
            logger.debug('File saving...')
            file.save()
            logger.debug('File saved')

            logger.debug('Exiting RenameView.patch function and responding with "message": "File renamed successfully"')
            return JsonResponse({'message': 'File renamed successfully'})

        logger.error('New name not provided')
        return JsonResponse({'error': 'New name not provided'}, status=400)

    def get(self, request):
        logger.debug('RenameView.get, rendering page')
        return render(request, 'index.html')


@method_decorator(login_required, name='dispatch')
class CommentView(View):
    def patch(self, request, file_id):
        logger.debug('Entering CommentView.patch function')
        logger.debug('Getting file by id...')
        file = get_object_or_404(File, id=file_id)

        logger.debug('Got file')

        if not file.user == request.user and not (request.user.is_admin or request.user.is_superuser):
            return JsonResponse({'error': 'Access denied'}, status=403)

        new_comment = json.loads(request.body).get('comment')
        if new_comment:
            logger.debug('File comment changing...')
            file.comment = new_comment
            logger.debug('File comment changed')
            logger.debug('File saving...')
            file.save()
            logger.debug('File saved')

            logger.debug('Exiting CommentView.patch function and responding '
                         'with "message": "Comment updated successfully"')
            return JsonResponse({'message': 'Comment updated successfully'})

        logger.error('Comment not provided')
        return JsonResponse({'error': 'Comment not provided'}, status=400)

    def get(self, request):
        logger.debug('CommentView.get, rendering page')
        return render(request, 'index.html')


@method_decorator(login_required, name='dispatch')
class DownloadView(View):
    def get(self, request, file_id):
        logger.debug('Entering DownloadView.get function')
        logger.debug('Getting file by id...')
        file = get_object_or_404(File, id=file_id)

        logger.debug('Got file')

        if file.user != request.user and request.user not in file.recipients.all() and \
                not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)
        logger.debug('Updating last_download_date file...')
        file.last_download_date = datetime.now(timezone.utc)
        logger.debug('File last_download_date updated')
        logger.debug('File saving...')
        file.save()
        logger.debug('File saved')

        logger.debug('Preparing response with file_data...')
        response = HttpResponse(file.data, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file.original_name}"'
        logger.debug('Response with file_data prepared')

        logger.debug('Exiting DownloadView.get function'
                     ' and responding with file_data application/octet-stream')
        return response


class DownloadSpecialView(View):
    def get(self, request, _, file_id):
        logger.debug('Entering DownloadSpecialView.get function')
        logger.debug('Getting file by special_link...')
        file = get_object_or_404(File, special_link=request.path)
        if file_id == file.id:
            logger.debug('Got file')

            logger.debug('Updating last_download_date file...')
            file.last_download_date = datetime.now(timezone.utc)
            logger.debug('File last_download_date updated')
            logger.debug('File saving...')
            file.save()
            logger.debug('File saved')

            logger.debug('Preparing response with file_data...')
            response = HttpResponse(file.data, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{file.original_name}"'
            logger.debug('Response with file_data prepared')

            logger.debug('Exiting DownloadSpecialView.get function'
                         ' and responding with file_data application/octet-stream')
            return response


@method_decorator(login_required, name='dispatch')
class DetailView(View):
    def get(self, request):
        logger.debug('Entering GetFilesView.get function')
        logger.debug('Exiting GetFilesView.get function and rendering page')
        return render(request, 'index.html')


@method_decorator(login_required, name='dispatch')
class UserShareView(View):
    def post(self, request, file_id):
        logger.debug('Entering UserShareView.post function')
        logger.debug('Getting file by id...')
        file = get_object_or_404(File, id=file_id)

        logger.debug('Got file')

        recipient_username = request.POST.get('recipient_username')
        if recipient_username:
            logger.debug('Adding recipient_username to recipients...')
            file.recipients.add(recipient_username)
            logger.debug('Added recipient_username to recipients')
            logger.debug('File saving...')
            file.save()
            logger.debug('File saved')

            logger.debug('Exiting UserShareView.post function and responding with "files": file_list object')
            return JsonResponse({'message': 'File shared successfully'})

        logger.error('No recipient username provided')
        return JsonResponse({'error': 'No recipient username provided'})


@method_decorator(login_required, name='dispatch')
class GetFilesView(View):
    def get(self, request):
        logger.debug('Entering GetFilesView.get function')
        user_id = request.GET.get('user_id')

        if user_id and (request.user.is_admin or request.user.is_superuser):
            logger.debug('Admin/Superuser request')
            logger.debug('User finding...')
            user = get_object_or_404(User, id=user_id)

            logger.debug('Preparing File.objects filtered by user...')
            files = File.objects.filter(user=user)
            logger.debug('Prepared File.objects filtered by user')
        else:
            logger.debug('User request')
            logger.debug('Getting files filtered by request.user...')
            files = File.objects.filter(user=request.user)
            if files:
                logger.debug('Got files filtered by request.user')
            else:
                logger.debug('Files not found by request.user')
                logger.debug('Setting files empty...')
                files = []
                logger.debug('Set files empty')

        logger.debug('Starting file_list preparation...')
        file_list = []
        for file in files:
            file_data = {
                "id": file.id,
                "name": file.name,
                "comment": file.comment,
                "size": file.size,
                "upload_date": str(file.upload_date),
                "last_download_date": str(file.last_download_date)
            }
            file_list.append(file_data)
        logger.debug('Finished file_list preparation...')

        logger.debug('Exiting GetFilesView.get function, rendering page and responding with "files": file_list object')
        return JsonResponse({'files': file_list})


@method_decorator(login_required, name='dispatch')
class GetFileView(View):
    def get(self, request, file_id):
        logger.debug('Entering GetFileView.get function')
        logger.debug('Getting file by id...')
        file = get_object_or_404(File, id=file_id)
        logger.debug('Got file')
        if not file.user == request.user and not (request.user.is_admin or request.user.is_superuser):
            logger.error('Access denied')
            return JsonResponse({'error': 'Access denied'}, status=403)
        logger.debug('Popping data field from file...')
        file_obj = {
            'id': file.id,
            'name': file.name,
            'comment': file.comment,
            'original_name': file.original_name,
            'size': file.size,
            'upload_date': str(file.upload_date),
            'last_download_date': str(file.last_download_date),
            'special_link': file.special_link,
            'data': base64.b64encode(file.data).decode('utf-8'),
        }

        logger.debug('Popped data field from file')
        logger.debug('Exiting GetFileView.get function and responding with "file": file')
        return JsonResponse({'file': file_obj})

