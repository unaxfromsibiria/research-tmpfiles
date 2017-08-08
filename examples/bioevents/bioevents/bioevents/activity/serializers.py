
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import get_error_detail

from .models import BaseEvent, SleepEventModel, MovementEventModel


class LocationPointListField(serializers.ListField):
    """Point as list.
    """

    child = serializers.FloatField()

    def point_validator(self, value, min_value, max_value):
        """Check the value.
        """

        validators = []
        point_errors = []

        message = self.child.error_messages["max_value"].format(
            max_value=max_value)

        validators.append(
            MaxValueValidator(max_value, message=message))

        message = self.child.error_messages["min_value"].format(
            min_value=min_value)

        validators.append(
            MinValueValidator(min_value, message=message))

        for validator in validators:
            try:
                validator(value)
            except ValidationError as exc:
                if isinstance(exc.detail, dict):
                    raise
                point_errors.extend(exc.detail)
            except DjangoValidationError as exc:
                point_errors.extend(get_error_detail(exc))

        return point_errors

    def run_validators(self, value):
        """Check the value of longitude/latitude is correct.
        """
        result = super().run_validators(value)
        point_errors = []
        lng, lat = value
        lng_max_value, lng_min_value = 180, -180
        lat_max_value, lat_min_value = 90, -90

        point_errors.extend(
            self.point_validator(lng, lng_min_value, lng_max_value))

        point_errors.extend(
            self.point_validator(lat, lat_min_value, lat_max_value))

        if point_errors:
            raise ValidationError(point_errors)
        return result


class EventModelSerializer(serializers.ModelSerializer):
    """Serializer for event model.
    """

    class Meta:
        model = BaseEvent
        fields = (
            "time_start",
            "time_end",
        )

    def validate(self, attrs):
        """Check that the start is before the end.
        """
        if ("time_end" in attrs) and (attrs["time_start"] > attrs["time_end"]):
            raise serializers.ValidationError(
                "Value of time_start have to less then time_end")

        return attrs

    def create(self, validated_data):
        """Make location from point.
        """
        if "point" in validated_data:
            point = validated_data.pop("point")
            if point:
                validated_data["location"] = Point(*point)

        return super().create(validated_data)


class SleepModelSerializer(EventModelSerializer):
    """Serializer for sleep model.
    """

    point = LocationPointListField(max_length=2, min_length=2, required=False, allow_null=True)  # noqa

    class Meta:
        model = SleepEventModel
        fields = (
            "id",
            "uid",
            "time_start",
            "time_end",
            "point",
        )


class MovementModelSerializer(EventModelSerializer):
    """Serializer for movement event model.
    """

    point = LocationPointListField(max_length=2, min_length=2, required=False, allow_null=True)  # noqa

    class Meta:
        model = MovementEventModel
        fields = (
            "id",
            "uid",
            "time_start",
            "time_end",
            "step_count",
            "point",
        )

    def validate(self, attrs):
        """Check value of steps less than zero is wrong
        """
        super().validate(attrs)
        step_count = int(attrs["step_count"] or 0)
        if step_count < 0:
            raise serializers.ValidationError(
                "Count of steps less than zero")

        return attrs
