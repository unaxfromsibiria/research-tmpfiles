from rest_framework import exceptions
from rest_framework.permissions import AllowAny
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_swagger.renderers import OpenAPIRenderer
from rest_framework_swagger.renderers import SwaggerUIRenderer

from rest_framework.schemas import SchemaGenerator as _SchemaGenerator
from rest_framework.schemas import is_list_view


def show_filter_backends(path, method, view):
    """Return True if view have an explicitly defined parameter
    `show_filter_backends`, which we can inspect or
    the given path/method appears to represent a list view.
    """
    if getattr(view, 'show_filter_backends', None):
        return True
    return is_list_view(path, method, view)


class SchemaGenerator(_SchemaGenerator):
    """Swagger magic.
    """
    def get_filter_fields(self, path, method, view):
        if not show_filter_backends(path, method, view):
            return []

        if not getattr(view, 'filter_backends', None):
            return []

        fields = []
        for filter_backend in view.filter_backends:
            fields += filter_backend().get_schema_fields(view)
        return fields


class SwaggerSchemaView(APIView):
    """Swagger is good.
    """
    _ignore_model_permissions = True
    exclude_from_schema = True
    permission_classes = [AllowAny]
    renderer_classes = [
        CoreJSONRenderer,
        OpenAPIRenderer,
        SwaggerUIRenderer
    ]

    def get(self, request):
        generator = SchemaGenerator(
            title='REST-API description'
        )
        schema = generator.get_schema(request=request)

        if not schema:
            raise exceptions.ValidationError(
                'The schema generator did not return a schema Document'
            )

        return Response(schema)
