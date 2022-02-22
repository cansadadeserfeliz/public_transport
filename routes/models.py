from django.db import models


class Route(models.Model):
    ROUTE_TYPE_BRT = 'transmilenio'
    ROUTE_TYPE_SHUTTLE = 'alimentador'
    ROUTE_TYPE_URBAN = 'urbano'
    ROUTE_TYPE_COMPLEMENTARY = 'complementario'
    ROUTE_TYPE_SPECIAL = 'especial'
    ROUTE_TYPES = (
        (ROUTE_TYPE_BRT, 'TransMilenio'),
        (ROUTE_TYPE_SHUTTLE, 'Alimentador'),
        (ROUTE_TYPE_URBAN, 'Urbano'),
        (ROUTE_TYPE_COMPLEMENTARY, 'Complementario'),
        (ROUTE_TYPE_SPECIAL, 'Especial'),
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    route_type = models.CharField(max_length=50, choices=ROUTE_TYPES)
    map_link = models.URLField(default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code

    class Meta:
        ordering = ['code']
