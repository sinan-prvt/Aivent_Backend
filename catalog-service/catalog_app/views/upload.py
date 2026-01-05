from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.core.files.storage import default_storage
import os
import uuid

class UploadImageView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('image')
        if not file_obj:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Generate unique filename to avoid collisions
        ext = os.path.splitext(file_obj.name)[1]
        filename = f"{uuid.uuid4()}{ext}"
        file_path_within_bucket = os.path.join('menu-items', filename)
        
        saved_path = default_storage.save(file_path_within_bucket, file_obj)
        file_url = default_storage.url(saved_path)

        return Response({"url": file_url}, status=status.HTTP_201_CREATED)
