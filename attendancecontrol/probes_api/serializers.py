from rest_framework import serializers
from control.models.probes import ProbeRequests

class ProbeRequestsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ProbeRequests
        fields = '__all__'
