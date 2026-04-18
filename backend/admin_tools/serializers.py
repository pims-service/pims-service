from rest_framework import serializers
from .models import ExportTask

class ExportTaskSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ExportTask
        fields = ['id', 'status', 'file_url', 'error_message', 'created_at']

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None
