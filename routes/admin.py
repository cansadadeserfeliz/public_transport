from django.contrib import admin
from django.utils.html import mark_safe

from .models import BusStop
from .models import Route
from .models import RouteStations


class RouteStationsInline(admin.TabularInline):
    model = RouteStations


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code_display',
        'route_mode',
        'service_tier',
        'created_at',
        'updated_at',
    )

    def code_display(self, obj):
        return mark_safe(
            f'<span style="border-left: none; '
            f'border-bottom: 5px solid {obj.color};">'
            f'{obj.code}</span>'
        )


@admin.register(BusStop)
class BusStopAdmin(admin.ModelAdmin):
    search_fields = ('name', 'cenefa', 'gtfs_stop_id')
    list_display = (
        'name',
        'stop_type',
        'link',
        'created_at',
        'updated_at',
    )


@admin.register(RouteStations)
class RouteStationsAdmin(admin.ModelAdmin):
    list_display = (
        'route',
        'direction',
        'position',
        'bus_stop',
        'created_at',
        'updated_at',
    )
    list_select_related = ('route', 'bus_stop')
