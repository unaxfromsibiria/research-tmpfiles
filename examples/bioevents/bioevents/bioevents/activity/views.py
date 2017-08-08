
from rest_framework import permissions
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response

from .serializers import EventModelSerializer
from .serializers import MovementModelSerializer
from .serializers import SleepModelSerializer


class BaseEventListView(ListCreateAPIView):
    """Base view for events.
    """
    serializer_class = EventModelSerializer
    permission_classes = (permissions.AllowAny, )

    def get_queryset(self):
        """Apply filters.
        """
        serializer = self.get_serializer_class()
        return serializer.Meta.model.objects.all()

    def get(self, request, *args, **kwargs):
        """Result filter by period for records list.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = EventModelSerializer(data=request.GET)
        # required fields of period
        serializer.is_valid(raise_exception=True)

        time_start = serializer.validated_data.get("time_start")
        time_end = serializer.validated_data.get("time_end")
        serializer = self.get_serializer(
            queryset.filter(time_start__range=(time_start, time_end)),
            many=True)
        return Response(serializer.data)


class SleepEventListView(BaseEventListView):
    """Manage sleep events.
    """
    serializer_class = SleepModelSerializer
    permission_classes = (permissions.AllowAny, )


class MovementEventListView(BaseEventListView):
    """Manage move events.
    """
    serializer_class = MovementModelSerializer
    permission_classes = (permissions.AllowAny, )
