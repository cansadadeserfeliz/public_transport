from django.contrib import admin
from django.utils.html import mark_safe

from .models import Route


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'code_display', 'route_type')

    def code_display(self, obj):
        return mark_safe(
            f'<span style="border-left: none; '
            f'border-bottom: 5px solid {obj.color};">'
            f'{obj.code}</span>'
        )
