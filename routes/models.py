import uuid

from django.contrib.gis.db import models as gis_models
from django.db import models
from django.urls import reverse


class Corridor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Example: Calle 26',
    )
    zone_letter = models.CharField(max_length=5)
    color = models.CharField(
        max_length=50,
        help_text='Example: #95B734',
    )
    pdf_link = models.URLField(default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(color__regex=r'^#[0-9A-Fa-f]{6}$'),
                name='corridor_color_valid_hex',
            ),
        ]


class Route(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ROUTE_MODE_TRUNK = 'transmilenio'
    ROUTE_MODE_ZONAL = 'transmizonal'
    ROUTE_MODE_CABLE = 'transmicable'
    ROUTE_MODES = (
        (ROUTE_MODE_TRUNK, 'TransMilenio'),
        (ROUTE_MODE_ZONAL, 'TransMiZonal'),
        (ROUTE_MODE_CABLE, 'TransMiCable'),
    )

    SERVICE_TIER_TRUNK = 'troncal'
    SERVICE_TIER_FEEDER = 'alimentador'
    SERVICE_TIER_DUAL = 'dual'
    SERVICE_TIER_URBAN = 'urbano'
    SERVICE_TIER_COMPLEMENTARY = 'complementario'
    SERVICE_TIER_SPECIAL = 'especial'
    SERVICE_TIER_CABLE = 'cable'
    SERVICE_TIERS = (
        (SERVICE_TIER_TRUNK, 'Troncal'),
        (SERVICE_TIER_FEEDER, 'Alimentador'),
        (SERVICE_TIER_DUAL, 'Dual'),
        (SERVICE_TIER_URBAN, 'Urbano'),
        (SERVICE_TIER_COMPLEMENTARY, 'Complementario'),
        (SERVICE_TIER_SPECIAL, 'Especial'),
        (SERVICE_TIER_CABLE, 'Cable'),
    )

    name = models.CharField(
        max_length=255,
        help_text='Example: Auto Norte Estación Alcalá',
    )
    code = models.CharField(
        max_length=50,
        help_text='Example: 19-1',
    )
    gtfs_route_id = models.CharField(
        max_length=50,
        unique=True,
        help_text='routes.txt route_id — refresh natural key.',
    )
    route_mode = models.CharField(max_length=20, choices=ROUTE_MODES)
    service_tier = models.CharField(max_length=20, choices=SERVICE_TIERS)
    color = models.CharField(
        max_length=50,
        default='',
        help_text='Example: #95B734',
    )
    corridor = models.ForeignKey(
        'routes.Corridor',
        null=True,
        blank=True,
        related_name='routes',
        # PROTECT, not SET_NULL: route_corridor_required_for_troncal_only
        # forbids a troncal route from ever having corridor=NULL, so
        # SET_NULL would raise IntegrityError on delete instead of a
        # clean, expected ProtectedError.
        on_delete=models.PROTECT,
    )
    path = gis_models.MultiLineStringField(
        null=True,
        help_text='GTFS shape geometry.',
    )
    is_active = models.BooleanField(default=True)
    ciclovia_affected = models.BooleanField(default=False)

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
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        service_tier='troncal',
                        corridor__isnull=False,
                    )
                    | (
                        ~models.Q(service_tier='troncal')
                        & models.Q(corridor__isnull=True)
                    )
                ),
                name='route_corridor_required_for_troncal_only',
            ),
            # Only 7 (route_mode, service_tier) pairs occur in the real
            # feed (see Dev Notes' agency_id table in the story) — reject
            # any other combination rather than silently allow it.
            models.CheckConstraint(
                condition=(
                    models.Q(route_mode='transmilenio', service_tier='troncal')
                    | models.Q(
                        route_mode='transmilenio', service_tier='alimentador'
                    )
                    | models.Q(route_mode='transmilenio', service_tier='dual')
                    | models.Q(
                        route_mode='transmizonal', service_tier='urbano'
                    )
                    | models.Q(
                        route_mode='transmizonal',
                        service_tier='complementario',
                    )
                    | models.Q(
                        route_mode='transmizonal', service_tier='especial'
                    )
                    | models.Q(route_mode='transmicable', service_tier='cable')
                ),
                name='route_mode_service_tier_valid_combination',
            ),
        ]


class RouteSchedule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Confirmed against the real GTFS calendar.txt's 7 active service_id
    # weekday patterns (2026-08-19 verification). Ingestion (Story 1.3)
    # must reject any future weekday combination that doesn't match one
    # of these 7, not guess the nearest bucket.
    DAY_TYPE_WEEKDAY = 'L-V'  # service_id 1: Mon-Fri
    DAY_TYPE_SATURDAY = 'SAB'  # service_id 2: Sat only
    DAY_TYPE_WEEKDAY_SATURDAY = 'L-S'  # service_id 3: Mon-Sat
    DAY_TYPE_SUNDAY = 'DOM'  # service_id 4: Sun only
    DAY_TYPE_WEEKDAY_SUNDAY = 'L-V-D'  # service_id 5: Mon-Fri + Sun
    DAY_TYPE_WEEKEND = 'SAB-DOM'  # service_id 6: Sat + Sun
    DAY_TYPE_DAILY = 'DIARIO'  # service_id 7: every day
    DAY_TYPES = (
        (DAY_TYPE_WEEKDAY, 'Lunes a viernes'),
        (DAY_TYPE_SATURDAY, 'Sábado'),
        (DAY_TYPE_WEEKDAY_SATURDAY, 'Lunes a sábado'),
        (DAY_TYPE_SUNDAY, 'Domingo'),
        (DAY_TYPE_WEEKDAY_SUNDAY, 'Lunes a viernes y domingo'),
        (DAY_TYPE_WEEKEND, 'Sábado y domingo'),
        (DAY_TYPE_DAILY, 'Diario'),
    )

    route = models.ForeignKey(
        'routes.Route',
        related_name='schedules',
        on_delete=models.CASCADE,
    )
    day_type = models.CharField(max_length=10, choices=DAY_TYPES)
    # DurationField (not TimeField): GTFS stop_times.txt/frequencies.txt
    # times can exceed 24:00:00 for a trip starting before and continuing
    # past midnight of the same service day.
    start_time = models.DurationField()
    end_time = models.DurationField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # Python `choices` + `full_clean()` alone don't stop a raw
            # `.save()`/`bulk_create()` (Story 1.3's ingestion path) from
            # persisting an unrecognized day_type — enforce at the DB.
            models.CheckConstraint(
                condition=models.Q(
                    day_type__in=[
                        'L-V',
                        'SAB',
                        'L-S',
                        'DOM',
                        'L-V-D',
                        'SAB-DOM',
                        'DIARIO',
                    ]
                ),
                name='routeschedule_day_type_valid',
            ),
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F('start_time')),
                name='routeschedule_end_after_start',
            ),
        ]


class RouteStations(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

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
    bus_stop = models.ForeignKey(
        'routes.BusStop',
        related_name='route_stations',
        on_delete=models.PROTECT,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['route', 'direction', 'position']


class BusStop(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    STOP_TYPE_TRUNK = 'estacion_troncal'
    STOP_TYPE_ZONAL = 'paradero_zonal'
    STOP_TYPE_CABLE = 'estacion_cable'
    STOP_TYPES = (
        (STOP_TYPE_TRUNK, 'Estación troncal'),
        (STOP_TYPE_ZONAL, 'Paradero zonal'),
        (STOP_TYPE_CABLE, 'Estación de cable'),
    )

    name = models.CharField(max_length=150)
    stop_type = models.CharField(max_length=20, choices=STOP_TYPES)
    gtfs_stop_id = models.CharField(
        max_length=50,
        unique=True,
        help_text='stops.txt stop_id — refresh natural key.',
    )
    location = gis_models.PointField()
    address = models.CharField(max_length=255, default='')
    link = models.URLField(default='')

    # Zonal-only (paradero) — null when stop_type != paradero_zonal
    cenefa = models.CharField(
        max_length=50, null=True, blank=True, unique=True
    )
    zona_sitp = models.CharField(max_length=10, blank=True)
    audio = models.CharField(max_length=255, blank=True)

    # Trunk-only (estación) — null when stop_type != estacion_troncal.
    # transmilenio_id is the identity field, enforced by the CheckConstraint
    # below. numero_vagones/numero_accesos/biciestacion are supplementary
    # capacity attributes deliberately left out of that constraint (i.e. not
    # required non-null even for estacion_troncal rows) — the real source
    # data (Estaciones_Troncales_de_TRANSMILENIO.geojson) explicitly flags
    # these as incomplete ("Valores de capacidad de buses en proceso de
    # actualización"), so requiring them would reject legitimate refresh
    # data for stations whose capacity simply hasn't been published yet.
    transmilenio_id = models.IntegerField(null=True, blank=True, unique=True)
    numero_vagones = models.PositiveSmallIntegerField(null=True, blank=True)
    numero_accesos = models.PositiveSmallIntegerField(null=True, blank=True)
    biciestacion = models.BooleanField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('routes:bus_stop_detail', args=[self.id])

    class Meta:
        ordering = ['name']
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        stop_type='paradero_zonal',
                        cenefa__isnull=False,
                        transmilenio_id__isnull=True,
                    )
                    | models.Q(
                        stop_type='estacion_troncal',
                        transmilenio_id__isnull=False,
                        cenefa__isnull=True,
                    )
                    | models.Q(
                        stop_type='estacion_cable',
                        cenefa__isnull=True,
                        transmilenio_id__isnull=True,
                    )
                ),
                name='busstop_type_specific_fields_consistent',
            ),
        ]
