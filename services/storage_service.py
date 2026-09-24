import os
import uuid
from typing import Optional, Tuple


class StorageService:
    """Handles object storage for training videos and assets.
    
    Supports Google Cloud Storage with transparent fallback to local persistent
    static storage when GCS_BUCKET or credentials are not configured.
    """

    def __init__(self, bucket_name: Optional[str] = None, local_upload_dir: str = "static/uploads"):
        self.bucket_name = bucket_name or os.environ.get("GCS_BUCKET", "")
        self.local_upload_dir = local_upload_dir
        os.makedirs(self.local_upload_dir, exist_ok=True)
        self._storage_client = None

    def _get_bucket(self):
        if not self.bucket_name:
            return None
        if self._storage_client is None:
            try:
                from google.cloud import storage
                self._storage_client = storage.Client()
            except Exception as e:
                print(f"[StorageService] Warning: Could not initialize Google Cloud Storage Client: {e}")
                return None
        try:
            return self._storage_client.bucket(self.bucket_name)
        except Exception as e:
            print(f"[StorageService] Error getting bucket {self.bucket_name}: {e}")
            return None

    def upload_video(self, video_bytes: bytes, mime_type: str = "video/mp4") -> Tuple[Optional[str], bool]:
        """Uploads video bytes to GCS or falls back to local storage.
        
        Returns:
            (url_or_path, is_cloud)
        """
        ext = "mp4" if "mp4" in mime_type else "webm"
        filename = f"{uuid.uuid4().hex}.{ext}"

        # Attempt GCS upload if bucket configured
        bucket = self._get_bucket()
        if bucket:
            try:
                blob_name = f"training-videos/{filename}"
                blob = bucket.blob(blob_name)
                blob.upload_from_string(video_bytes, content_type=mime_type)
                blob.make_public()
                return blob_name, True
            except Exception as e:
                print(f"[StorageService] GCS upload failed ({e}). Falling back to local storage.")

        # Fallback: Save to local directory
        local_path = os.path.join(self.local_upload_dir, filename)
        try:
            with open(local_path, "wb") as f:
                f.write(video_bytes)
            return f"/{self.local_upload_dir}/{filename}", False
        except Exception as e:
            print(f"[StorageService] Local storage write failed: {e}")
            return None, False

    def get_public_url(self, resource_path: str) -> str:
        """Returns the public accessible URL for a given resource."""
        if not resource_path:
            return ""
        if resource_path.startswith("http://") or resource_path.startswith("https://") or resource_path.startswith("/"):
            return resource_path
        if self.bucket_name:
            return f"https://storage.googleapis.com/{self.bucket_name}/{resource_path}"
        return f"/{self.local_upload_dir}/{resource_path}"
