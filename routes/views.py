from django.views.generic import TemplateView

from .models import Route


class HomeView(TemplateView):
    template_name = 'routes/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['route_list'] = Route.objects.all()
        return context
