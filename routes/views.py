from django.views.generic import TemplateView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.http import JsonResponse

from .models import Route
from .models import RouteStations
from .models import BusStation
from transmiapp.services import get_buses_by_route_name


class HomeView(TemplateView):
    template_name = 'routes/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['route_list'] = Route.objects.all()
        return context


class RouteDetailView(DetailView):
    model = Route
    context_object_name = 'route'

    def get_context_data(self, **kwargs):
        context = super(RouteDetailView, self).get_context_data(**kwargs)
        route_1 = self.object.route_stations.filter(
            direction=RouteStations.DIRECTION_1,
        ).all()
        route_2 = self.object.route_stations.filter(
            direction=RouteStations.DIRECTION_2,
        ).all()
        context['route_station_groups'] = [route_1, route_2]
        return context


class RouteBusesAPIView(DetailView):
    model = Route
    context_object_name = 'route'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        buses_list = get_buses_by_route_name(self.object.code)

        response_geo_json = []
        for bus in buses_list:
            response_geo_json.append(
                {
                    'type': 'Feature',
                    'properties': {
                        'id': bus.bus_id,
                    },
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [bus.longitude, bus.latitude],
                    },
                }
            )

        return JsonResponse(
            {
                'type': 'FeatureCollection',
                'features': response_geo_json,
            }
        )


class RouteStationsAPIView(DetailView):
    model = Route
    context_object_name = 'route'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        route_1 = self.object.route_stations.filter(
            direction=RouteStations.DIRECTION_1,
        ).all()
        # route_2 = self.object.route_stations.filter(
        #     direction=RouteStations.DIRECTION_2,
        # ).all()

        coordinates = []
        for route_station in route_1:
            coordinates.append(
                [
                    route_station.bus_station.longitude,
                    route_station.bus_station.latitude,
                ]
            )

        return JsonResponse(
            {
                'type': 'Feature',
                'properties': {},
                'geometry': {
                    'type': 'LineString',
                    'coordinates': coordinates,
                },
            }
        )


class BusStationsListView(ListView):
    model = BusStation
    paginate_by = 100


class BusStationsDetailView(DetailView):
    model = BusStation
    context_object_name = 'bus_station'
