from rest_framework import viewsets
from rest_framework import permissions

from control.models.probes import ProbeRequests
from .serializers import ProbeRequestsSerializer

# Create your views here.
class ProbeRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows probe requests to be viewed"""
    queryset = ProbeRequests.objects.all().order_by('time')
    serializer_class = ProbeRequestsSerializer
    permission_classes = [permissions.IsAdminUser]
