from django.db import models
from django.urls import reverse


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
    name = models.CharField(
        max_length=255,
        help_text='Example: Auto Norte Estación Alcalá',
    )
    code = models.CharField(
        max_length=50,
        help_text='Example: 19-1',
    )
    route_type = models.CharField(max_length=50, choices=ROUTE_TYPES)
    color = models.CharField(
        max_length=50,
        default='',
        help_text='Example: #95B734',
    )
    schedule = models.CharField(max_length=500)
    map_link = models.URLField(default='')
    details_link = models.URLField(
        default='',
        help_text='Link to detail page on transmilenio.gov.co.',
    )

    publication_date = models.DateTimeField(
        null=True,
        help_text='Data from transmilenio.gov.co.',
    )
    last_update = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code

    class Meta:
        ordering = ['code']
        unique_together = ('code', 'name')


class RouteStations(models.Model):
    DIRECTION_1 = 1
    DIRECTION_2 = 2

    direction = models.PositiveSmallIntegerField(
        choices=((DIRECTION_1, 'Recorrido 1'), (DIRECTION_2, 'Recorrido 2')),
    )
    position = models.PositiveIntegerField()
    route = models.ForeignKey(
        'routes.Route',
        related_name='route_stations',
        on_delete=models.PROTECT,
    )
    bus_station = models.ForeignKey(
        'routes.BusStation',
        related_name='route_stations',
        on_delete=models.PROTECT,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['route', 'direction', 'position']


class BusStation(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, unique=True)
    link = models.URLField(default='')
    address = models.CharField(max_length=255, default='')

    cenefa = models.CharField(max_length=50, blank=True)
    audio = models.CharField(max_length=255, blank=True)
    longitude = models.DecimalField(
        null=True, max_digits=30, decimal_places=15
    )
    latitude = models.DecimalField(null=True, max_digits=30, decimal_places=15)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code

    def get_absolute_url(self):
        return reverse('routes:bus_station_detail', args=[self.id])
