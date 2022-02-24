from django.urls import path

from .views import HomeView
from .views import RouteDetailView

app_name = 'routes'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('route/<int:pk>/', RouteDetailView.as_view(), name='route_detail'),
]
