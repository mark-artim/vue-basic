"""
Secure File Management Views

All endpoints require authentication and enforce company-level isolation.
Heritage users can ONLY access Heritage files. Crescent can ONLY access Crescent files.
"""

from django.http import JsonResponse, HttpResponse, FileResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core.decorators import require_product
from .models import CompanyFile, FileAccessLog
from .s3_service import get_s3_service
import logging
from datetime import datetime
import mimetypes

logger = logging.getLogger(__name__)


@require_product('eclipse')
def file_manager_page(request):
    """
    Render the File Manager HTML page.
    Requires Eclipse product authorization.
    """
    context = {
        'customer': {
            'email': request.session.get('customer_email'),
            'company_code': request.session.get('customer_company_code'),
        }
    }
    return render(request, 'files/file_manager.html', context)


def require_customer_auth(view_func):
    """
    Decorator to require customer authentication.
    Redirects to login if not authenticated.
    """
    def wrapper(request, *args, **kwargs):
        if not request.session.get('customer_logged_in'):
            return JsonResponse({
                'error': 'Authentication required'
            }, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


def get_user_info(request):
    """Extract user info from session"""
    return {
        'user_id': request.session.get('customer_user_id'),
        'email': request.session.get('customer_email'),
        'company_code': request.session.get('customer_company_code'),
        'company_name': request.session.get('customer_company_name', ''),
    }


def log_file_access(file_id, file_key, operation, user_info, request, success=True, error_message=None, metadata=None):
    """
    Log file access for audit trail.
    CRITICAL for security monitoring and compliance.
    """
    try:
        FileAccessLog.objects.create(
            file_id=file_id or '',
            file_key=file_key,
            operation=operation,
            user_id=user_info['user_id'],
            user_email=user_info['email'],
            company_code=user_info['company_code'],
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
    except Exception as e:
        logger.error(f"[Files] Failed to log file access: {e}")


@csrf_exempt
@require_customer_auth
@require_http_methods(["GET"])
def list_files(request):
    """
    List all files for the authenticated user's company.
    SECURITY: Only returns files belonging to user's company.
    """
    user_info = get_user_info(request)
    company_code = user_info['company_code']

    try:
        # Query MongoDB for files belonging to this company only
        files = CompanyFile.objects.filter(
            company_code=company_code,
            is_deleted=False
        ).order_by('-uploaded_at')

        files_list = [file.to_dict() for file in files]

        logger.info(f"[Files] Listed {len(files_list)} files for company {company_code}")

        return JsonResponse({
            'success': True,
            'files': files_list,
            'company_code': company_code,
        })

    except Exception as e:
        logger.error(f"[Files] List failed for company {company_code}: {e}")
        return JsonResponse({
            'error': f'Failed to list files: {str(e)}'
        }, status=500)


@csrf_exempt
@require_customer_auth
@require_http_methods(["POST"])
def upload_file(request):
    """
    Upload a file to Wasabi with company isolation.
    SECURITY: File is stored in company-specific folder.
    """
    user_info = get_user_info(request)
    company_code = user_info['company_code']

    if not request.FILES.get('file'):
        return JsonResponse({'error': 'No file provided'}, status=400)

    uploaded_file = request.FILES['file']
    original_filename = uploaded_file.name
    category = request.POST.get('category', '')
    description = request.POST.get('description', '')

    try:
        # Upload to Wasabi S3 with company prefix
        s3_service = get_s3_service()
        upload_result = s3_service.upload_file(
            file_obj=uploaded_file.file,
            company_code=company_code,
            filename=original_filename,
            content_type=uploaded_file.content_type
        )

        # Create MongoDB record
        file_record = CompanyFile.objects.create(
            filename=original_filename,
            original_filename=original_filename,
            file_key=upload_result['key'],
            file_size=upload_result['size'],
            content_type=upload_result['content_type'],
            company_code=company_code,
            company_name=user_info['company_name'],
            uploaded_by_user_id=user_info['user_id'],
            uploaded_by_email=user_info['email'],
            category=category,
            description=description,
        )

        # Log the upload
        log_file_access(
            file_id=str(file_record.id),
            file_key=upload_result['key'],
            operation='upload',
            user_info=user_info,
            request=request,
            metadata={
                'filename': original_filename,
                'size': upload_result['size'],
                'category': category,
            }
        )

        logger.info(f"[Files] Uploaded {original_filename} for company {company_code}")

        return JsonResponse({
            'success': True,
            'message': f'Uploaded {original_filename}',
            'file': file_record.to_dict(),
        })

    except Exception as e:
        logger.error(f"[Files] Upload failed for company {company_code}: {e}")

        # Log failed upload
        log_file_access(
            file_id=None,
            file_key=original_filename,
            operation='upload',
            user_info=user_info,
            request=request,
            success=False,
            error_message=str(e)
        )

        return JsonResponse({
            'error': f'Upload failed: {str(e)}'
        }, status=500)


@csrf_exempt
@require_customer_auth
@require_http_methods(["GET"])
def download_file(request, file_id):
    """
    Download a file.
    SECURITY: Validates that file belongs to user's company before download.
    """
    user_info = get_user_info(request)
    company_code = user_info['company_code']

    try:
        # Get file record - MUST belong to user's company
        file_record = CompanyFile.objects.get(
            id=file_id,
            company_code=company_code,  # CRITICAL: Company filter
            is_deleted=False
        )

        # Download from Wasabi (with company validation)
        s3_service = get_s3_service()
        file_content = s3_service.download_file(
            file_key=file_record.file_key,
            company_code=company_code  # Double validation
        )

        # Update last accessed
        file_record.last_accessed = datetime.utcnow()
        file_record.save()

        # Log the download
        log_file_access(
            file_id=str(file_record.id),
            file_key=file_record.file_key,
            operation='download',
            user_info=user_info,
            request=request,
            metadata={'filename': file_record.filename}
        )

        # Return file as download
        response = HttpResponse(file_content, content_type=file_record.content_type)
        response['Content-Disposition'] = f'attachment; filename="{file_record.filename}"'

        logger.info(f"[Files] Downloaded {file_record.filename} by {user_info['email']}")

        return response

    except CompanyFile.DoesNotExist:
        logger.warning(f"[Files] Unauthorized download attempt: {user_info['email']} tried to access file {file_id}")

        # Log failed attempt
        log_file_access(
            file_id=file_id,
            file_key=f'unknown-{file_id}',
            operation='download',
            user_info=user_info,
            request=request,
            success=False,
            error_message='File not found or access denied'
        )

        return JsonResponse({
            'error': 'File not found or access denied'
        }, status=404)

    except PermissionError as e:
        logger.warning(f"[Files] Permission denied: {user_info['email']} tried to access file from another company")

        log_file_access(
            file_id=file_id,
            file_key=file_record.file_key if 'file_record' in locals() else '',
            operation='download',
            user_info=user_info,
            request=request,
            success=False,
            error_message=str(e)
        )

        return JsonResponse({
            'error': 'Access denied'
        }, status=403)

    except Exception as e:
        logger.error(f"[Files] Download failed: {e}")

        return JsonResponse({
            'error': f'Download failed: {str(e)}'
        }, status=500)


@csrf_exempt
@require_customer_auth
@require_http_methods(["DELETE"])
def delete_file(request, file_id):
    """
    Delete a file (soft delete in MongoDB, hard delete in S3).
    SECURITY: Validates that file belongs to user's company.
    """
    user_info = get_user_info(request)
    company_code = user_info['company_code']

    try:
        # Get file record - MUST belong to user's company
        file_record = CompanyFile.objects.get(
            id=file_id,
            company_code=company_code,  # CRITICAL: Company filter
            is_deleted=False
        )

        # Delete from Wasabi (with company validation)
        s3_service = get_s3_service()
        s3_service.delete_file(
            file_key=file_record.file_key,
            company_code=company_code  # Double validation
        )

        # Soft delete in database
        file_record.is_deleted = True
        file_record.deleted_at = datetime.utcnow()
        file_record.deleted_by = user_info['user_id']
        file_record.save()

        # Log the deletion
        log_file_access(
            file_id=str(file_record.id),
            file_key=file_record.file_key,
            operation='delete',
            user_info=user_info,
            request=request,
            metadata={'filename': file_record.filename}
        )

        logger.info(f"[Files] Deleted {file_record.filename} by {user_info['email']}")

        return JsonResponse({
            'success': True,
            'message': f'Deleted {file_record.filename}'
        })

    except CompanyFile.DoesNotExist:
        logger.warning(f"[Files] Unauthorized delete attempt: {user_info['email']} tried to delete file {file_id}")

        log_file_access(
            file_id=file_id,
            file_key=f'unknown-{file_id}',
            operation='delete',
            user_info=user_info,
            request=request,
            success=False,
            error_message='File not found or access denied'
        )

        return JsonResponse({
            'error': 'File not found or access denied'
        }, status=404)

    except PermissionError as e:
        logger.warning(f"[Files] Permission denied: {user_info['email']} tried to delete file from another company")

        return JsonResponse({
            'error': 'Access denied'
        }, status=403)

    except Exception as e:
        logger.error(f"[Files] Delete failed: {e}")

        return JsonResponse({
            'error': f'Delete failed: {str(e)}'
        }, status=500)


@csrf_exempt
@require_customer_auth
@require_http_methods(["POST"])
def rename_file(request, file_id):
    """
    Rename a file.
    SECURITY: Validates that file belongs to user's company.
    """
    user_info = get_user_info(request)
    company_code = user_info['company_code']

    import json
    data = json.loads(request.body)
    new_filename = data.get('new_filename')

    if not new_filename:
        return JsonResponse({'error': 'New filename required'}, status=400)

    try:
        # Get file record - MUST belong to user's company
        file_record = CompanyFile.objects.get(
            id=file_id,
            company_code=company_code,  # CRITICAL: Company filter
            is_deleted=False
        )

        old_filename = file_record.filename
        old_key = file_record.file_key

        # Rename in Wasabi (with company validation)
        s3_service = get_s3_service()
        new_key = s3_service.rename_file(
            old_key=old_key,
            new_filename=new_filename,
            company_code=company_code  # Double validation
        )

        # Update database record
        file_record.filename = new_filename
        file_record.file_key = new_key
        file_record.save()

        # Log the rename
        log_file_access(
            file_id=str(file_record.id),
            file_key=new_key,
            operation='rename',
            user_info=user_info,
            request=request,
            metadata={
                'old_filename': old_filename,
                'new_filename': new_filename
            }
        )

        logger.info(f"[Files] Renamed {old_filename} to {new_filename} by {user_info['email']}")

        return JsonResponse({
            'success': True,
            'message': f'Renamed to {new_filename}',
            'file': file_record.to_dict()
        })

    except CompanyFile.DoesNotExist:
        return JsonResponse({
            'error': 'File not found or access denied'
        }, status=404)

    except PermissionError:
        return JsonResponse({
            'error': 'Access denied'
        }, status=403)

    except Exception as e:
        logger.error(f"[Files] Rename failed: {e}")

        return JsonResponse({
            'error': f'Rename failed: {str(e)}'
        }, status=500)
