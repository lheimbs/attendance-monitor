from rest_framework import serializers

from . import models


class ProbeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProbeRequest
        fields = ['time', 'mac', 'vendor', 'ssid', 'rssi', 'raw']

    def create(self, validated_data):
        return models.ProbeRequest.objects.create(**validated_data)
