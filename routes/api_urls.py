from django.urls import path

from .views import RouteBusesAPIView
from .views import RouteStationsAPIView

app_name = 'routes'

urlpatterns = [
    path(
        'route/<uuid:pk>/buses/',
        RouteBusesAPIView.as_view(),
        name='route_buses',
    ),
    path(
        'route/<uuid:pk>/stations/',
        RouteStationsAPIView.as_view(),
        name='route_stations',
    ),
]
