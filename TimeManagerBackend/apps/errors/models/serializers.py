from rest_framework import serializers


class ExceptionSerializer(serializers.Serializer):  # noqa must implement all abstract
    detail = serializers.CharField()
    code = serializers.CharField()
