from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^sleep-events/$', views.SleepEventListView.as_view(), name='sleep-events-list'),  # noqa
    url(r'^move-events/$', views.MovementEventListView.as_view(), name='move-events-list'),  # noqa
]
