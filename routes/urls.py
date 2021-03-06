from django.urls import path

from .views import HomeView
from .views import RouteDetailView
from .views import BusStationsListView
from .views import BusStationsDetailView

app_name = 'routes'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('route/<int:pk>/', RouteDetailView.as_view(), name='route_detail'),
    path(
        'bus-stations/',
        BusStationsListView.as_view(),
        name='bus_stations_list',
    ),
    path(
        'bus-stations/<int:pk>/',
        BusStationsDetailView.as_view(),
        name='bus_station_detail',
    ),
]
