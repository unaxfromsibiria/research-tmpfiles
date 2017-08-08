
from django.db import models
from django.contrib.gis.db import models as gis_models


class BaseEvent(models.Model):
    """Base event of users activity.
    """
    EVENT_TYPE_SLEEP = 1
    EVENT_TYPE_MOVEMENT = 2

    EVENT_TYPE = 0

    event_type = models.SmallIntegerField("Event type", default=0)
    time_start = models.DateTimeField("Event time begin")
    time_end = models.DateTimeField("Event time end")
    uid = models.UUIDField("User or device ID")
    location = gis_models.PointField("Location of this event", geography=True, null=True)  # noqa

    class Meta:
        verbose_name = "Base event"
        db_table = "bioevent_activity_base"

    def __str__(self):
        if self.location:
            loc = "[{}, {}]".format(*self.point)
        else:
            loc = "unknown location"

        return "{}:{}({}-{} in {})".format(
            self.__class__.__name__,
            self.uid,
            self.time_start.isoformat(),
            self.time_end.isoformat(),
            loc)

    def save(self, *args, **kwargs):
        self.event_type = self.__class__.EVENT_TYPE
        return super().save(*args, **kwargs)

    @property
    def latitude(self):
        return self.location.y

    @property
    def longitude(self):
        return self.location.x

    @property
    def point(self):
        return [self.longitude, self.latitude]

    @property
    def period(self):
        return [self.time_start, self.time_end]


class SleepEventModel(BaseEvent):
    """User activity is sleep.
    """
    EVENT_TYPE = BaseEvent.EVENT_TYPE_SLEEP

    class Meta:
        verbose_name = "Sleep"
        db_table = "bioevent_activity_sleep"


class MovementEventModel(BaseEvent):
    """User activity is movement.
    """
    EVENT_TYPE = BaseEvent.EVENT_TYPE_MOVEMENT

    step_count = models.IntegerField("Count of steps", default=0)

    class Meta:
        verbose_name = "Movement"
        db_table = "bioevent_activity_movement"
