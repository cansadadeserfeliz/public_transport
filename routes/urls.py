from django.urls import path

from .views import BusStopsDetailView
from .views import BusStopsListView
from .views import HomeView
from .views import RouteDetailView

app_name = 'routes'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('route/<uuid:pk>/', RouteDetailView.as_view(), name='route_detail'),
    path(
        'bus-stops/',
        BusStopsListView.as_view(),
        name='bus_stops_list',
    ),
    path(
        'bus-stops/<uuid:pk>/',
        BusStopsDetailView.as_view(),
        name='bus_stop_detail',
    ),
]
