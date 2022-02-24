from django.views.generic import TemplateView
from django.views.generic import DetailView

from .models import Route
from .models import RouteStations


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
