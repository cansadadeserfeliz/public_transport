from django.urls import path

from .views import RouteBusesAPIView
from .views import RouteStationsAPIView

app_name = 'routes'

urlpatterns = [
    path(
        'route/<int:pk>/buses/',
        RouteBusesAPIView.as_view(),
        name='route_buses',
    ),
    path(
        'route/<int:pk>/stations/',
        RouteStationsAPIView.as_view(),
        name='route_stations',
    ),
]
