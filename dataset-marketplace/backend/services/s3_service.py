# ============================================================================
# Dataset Marketplace - S3 Service
# AWS S3 operations for storing and retrieving dataset files
# ============================================================================

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from flask import current_app
import os
from datetime import datetime
import uuid


class S3Service:
    """
    Service class for AWS S3 operations.
    
    Handles:
    - Uploading dataset files to S3
    - Downloading/retrieving files from S3
    - Generating presigned URLs for direct downloads
    - Deleting files from S3
    
    Configuration is loaded from Flask app config.
    """
    
    def __init__(self, app=None):
        """
        Initialize S3 service.
        
        Args:
            app: Flask application instance (optional)
                 Can be initialized later with init_app()
        """
        self.client = None
        self.bucket_name = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize S3 service with Flask app configuration.
        
        Args:
            app: Flask application instance
        
        Reads AWS credentials and bucket name from app config.
        """
        # Store app reference for accessing config
        self.app = app
        
        # Get AWS configuration from Flask app config
        aws_access_key = app.config.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = app.config.get('AWS_SECRET_ACCESS_KEY')
        aws_region = app.config.get('AWS_REGION', 'us-east-1')
        self.bucket_name = app.config.get('S3_BUCKET_NAME')
        
        # Initialize boto3 S3 client with credentials
        # If credentials are empty, boto3 will use IAM role or environment variables
        if aws_access_key and aws_secret_key:
            self.client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
        else:
            # Use default credential chain (IAM role, env vars, etc.)
            self.client = boto3.client('s3', region_name=aws_region)
    
    def _get_client(self):
        """
        Get S3 client, initializing if needed.
        
        Returns:
            boto3.client: S3 client instance
        """
        if not self.client:
            # Initialize with current Flask app
            self.init_app(current_app)
        return self.client
    
    def _get_bucket(self):
        """
        Get S3 bucket name from config.
        
        Returns:
            str: S3 bucket name
        """
        if not self.bucket_name:
            self.bucket_name = current_app.config.get('S3_BUCKET_NAME')
        return self.bucket_name
    
    def generate_s3_key(self, user_id, filename):
        """
        Generate unique S3 object key for a file.
        
        Args:
            user_id: ID of user uploading the file
            filename: Original filename
        
        Returns:
            str: S3 object key in format "datasets/{user_id}/{timestamp}_{uuid}_{filename}"
        
        The key structure allows:
        - Organization by user
        - Unique identification via timestamp and UUID
        - Preservation of original filename
        """
        # Get current timestamp for uniqueness
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        # Generate short UUID to prevent collisions
        unique_id = str(uuid.uuid4())[:8]
        
        # Sanitize filename (remove special characters)
        safe_filename = "".join(c for c in filename if c.isalnum() or c in '._-')
        
        # Construct S3 key with hierarchical structure
        s3_key = f"datasets/{user_id}/{timestamp}_{unique_id}_{safe_filename}"
        
        return s3_key
    
    def upload_file(self, file_data, s3_key, content_type=None):
        """
        Upload file to S3 bucket.
        
        Args:
            file_data: File data as bytes or file-like object
            s3_key: S3 object key (path in bucket)
            content_type: MIME type of file (optional)
        
        Returns:
            dict: Success response with S3 key
                  {'success': True, 's3_key': '...'}
            
            dict: Error response on failure
                  {'success': False, 'error': '...'}
        """
        try:
            # Get S3 client and bucket
            client = self._get_client()
            bucket = self._get_bucket()
            
            # Prepare upload parameters
            extra_args = {}
            
            # Set content type if provided
            if content_type:
                extra_args['ContentType'] = content_type
            
            # Check if file_data is file-like object or bytes
            if hasattr(file_data, 'read'):
                # File-like object - use upload_fileobj
                client.upload_fileobj(
                    file_data,
                    bucket,
                    s3_key,
                    ExtraArgs=extra_args if extra_args else None
                )
            else:
                # Bytes data - use put_object
                client.put_object(
                    Bucket=bucket,
                    Key=s3_key,
                    Body=file_data,
                    **extra_args
                )
            
            # Return success response
            return {
                'success': True,
                's3_key': s3_key,
                'bucket': bucket
            }
        
        except NoCredentialsError:
            # AWS credentials not configured
            return {
                'success': False,
                'error': 'AWS credentials not configured'
            }
        
        except ClientError as e:
            # AWS API error (bucket not found, access denied, etc.)
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            return {
                'success': False,
                'error': f'S3 error ({error_code}): {error_msg}'
            }
        
        except Exception as e:
            # Unexpected error
            return {
                'success': False,
                'error': f'Upload failed: {str(e)}'
            }
    
    def download_file(self, s3_key):
        """
        Download file from S3 bucket.
        
        Args:
            s3_key: S3 object key to download
        
        Returns:
            dict: Success response with file data
                  {'success': True, 'data': bytes, 'content_type': '...'}
            
            dict: Error response on failure
                  {'success': False, 'error': '...'}
        """
        try:
            # Get S3 client and bucket
            client = self._get_client()
            bucket = self._get_bucket()
            
            # Get object from S3
            response = client.get_object(Bucket=bucket, Key=s3_key)
            
            # Read file data from response body
            file_data = response['Body'].read()
            
            # Get content type from response metadata
            content_type = response.get('ContentType', 'application/octet-stream')
            
            # Return success response with data
            return {
                'success': True,
                'data': file_data,
                'content_type': content_type,
                'content_length': response.get('ContentLength', len(file_data))
            }
        
        except ClientError as e:
            # Check for specific error codes
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            
            if error_code == 'NoSuchKey':
                return {
                    'success': False,
                    'error': 'File not found in S3'
                }
            
            return {
                'success': False,
                'error': f'S3 error: {error_code}'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Download failed: {str(e)}'
            }
    
    def generate_presigned_url(self, s3_key, expiration=3600):
        """
        Generate presigned URL for direct file download.
        
        Args:
            s3_key: S3 object key
            expiration: URL validity in seconds (default: 1 hour)
        
        Returns:
            dict: Success response with presigned URL
                  {'success': True, 'url': '...', 'expires_in': 3600}
            
            dict: Error response on failure
                  {'success': False, 'error': '...'}
        
        Presigned URLs allow clients to download directly from S3
        without proxying through the backend server.
        """
        try:
            # Get S3 client and bucket
            client = self._get_client()
            bucket = self._get_bucket()
            
            # Generate presigned URL for get_object operation
            url = client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            
            return {
                'success': True,
                'url': url,
                'expires_in': expiration
            }
        
        except ClientError as e:
            return {
                'success': False,
                'error': f'Failed to generate URL: {str(e)}'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'URL generation failed: {str(e)}'
            }
    
    def delete_file(self, s3_key):
        """
        Delete file from S3 bucket.
        
        Args:
            s3_key: S3 object key to delete
        
        Returns:
            dict: Success response
                  {'success': True}
            
            dict: Error response on failure
                  {'success': False, 'error': '...'}
        """
        try:
            # Get S3 client and bucket
            client = self._get_client()
            bucket = self._get_bucket()
            
            # Delete object from S3
            client.delete_object(Bucket=bucket, Key=s3_key)
            
            return {'success': True}
        
        except ClientError as e:
            return {
                'success': False,
                'error': f'Delete failed: {str(e)}'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Delete failed: {str(e)}'
            }
    
    def file_exists(self, s3_key):
        """
        Check if file exists in S3 bucket.
        
        Args:
            s3_key: S3 object key to check
        
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            # Get S3 client and bucket
            client = self._get_client()
            bucket = self._get_bucket()
            
            # Use head_object to check existence without downloading
            client.head_object(Bucket=bucket, Key=s3_key)
            return True
        
        except ClientError as e:
            # NoSuchKey or 404 means file doesn't exist
            if e.response.get('Error', {}).get('Code') in ['404', 'NoSuchKey']:
                return False
            # Re-raise other errors
            raise
        
        except Exception:
            return False


# Global S3 service instance (initialized in app.py)
s3_service = S3Service()
