"""Model and constraint tests for the amended GTFS-ready data model.

Exercises every CheckConstraint from both sides (accepting and
rejecting), confirms UUID primary keys, and guards against
regressions in the natural-key uniqueness decisions made in Story 1.2.
"""

import uuid

import pytest
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction
from django.db.models import ProtectedError

from routes.models import BusStop
from routes.models import Corridor
from routes.models import Route
from routes.models import RouteSchedule

BOGOTA_POINT = Point(-74.05, 4.65)


def make_corridor(**overrides):
    defaults = {
        'name': 'Calle 26',
        'zone_letter': 'K',
        'color': '#95B734',
    }
    defaults.update(overrides)
    return Corridor.objects.create(**defaults)


def make_route(gtfs_route_id, **overrides):
    defaults = {
        'name': 'Auto Norte Estación Alcalá',
        'code': '19-1',
        'gtfs_route_id': gtfs_route_id,
        'route_mode': Route.ROUTE_MODE_ZONAL,
        'service_tier': Route.SERVICE_TIER_URBAN,
    }
    defaults.update(overrides)
    return Route.objects.create(**defaults)


@pytest.mark.django_db
def test_route_and_bus_stop_use_uuid_primary_keys():
    route = make_route('gtfs-route-1')
    bus_stop = BusStop.objects.create(
        name='Portal 20 de Julio',
        stop_type=BusStop.STOP_TYPE_TRUNK,
        gtfs_stop_id='10000',
        location=BOGOTA_POINT,
        transmilenio_id=7103,
    )

    assert isinstance(route.id, uuid.UUID)
    assert isinstance(bus_stop.id, uuid.UUID)


@pytest.mark.django_db
def test_gtfs_route_id_uniqueness_is_enforced():
    make_route('duplicate-id')

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            make_route('duplicate-id')


@pytest.mark.django_db
def test_gtfs_stop_id_uniqueness_is_enforced():
    BusStop.objects.create(
        name='Br. Islandia',
        stop_type=BusStop.STOP_TYPE_ZONAL,
        gtfs_stop_id='51975',
        location=BOGOTA_POINT,
        cenefa='513A09',
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            BusStop.objects.create(
                name='Br. Islandia (duplicate)',
                stop_type=BusStop.STOP_TYPE_ZONAL,
                gtfs_stop_id='51975',
                location=BOGOTA_POINT,
                cenefa='513A10',
            )


@pytest.mark.django_db
def test_route_code_and_name_are_not_required_to_be_unique():
    """Regression guard for AC #5 — real feed data has 252 duplicate
    (code, name) pairs, so `unique_together` was dropped. Two routes
    sharing a code+name but differing only in gtfs_route_id must both
    save successfully.
    """
    make_route('route-a', code='G45', name='Suba')
    make_route('route-b', code='G45', name='Suba')

    assert Route.objects.filter(code='G45', name='Suba').count() == 2


@pytest.mark.django_db
def test_bus_stop_constraint_accepts_valid_combinations_per_stop_type():
    BusStop.objects.create(
        name='Paradero válido',
        stop_type=BusStop.STOP_TYPE_ZONAL,
        gtfs_stop_id='zonal-1',
        location=BOGOTA_POINT,
        cenefa='001A00',
    )
    BusStop.objects.create(
        name='Estación válida',
        stop_type=BusStop.STOP_TYPE_TRUNK,
        gtfs_stop_id='trunk-1',
        location=BOGOTA_POINT,
        transmilenio_id=7103,
    )
    BusStop.objects.create(
        name='Cable válido',
        stop_type=BusStop.STOP_TYPE_CABLE,
        gtfs_stop_id='cable_jpablo',
        location=BOGOTA_POINT,
    )

    assert BusStop.objects.count() == 3


@pytest.mark.django_db
def test_bus_stop_constraint_rejects_zonal_stop_with_transmilenio_id():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            BusStop.objects.create(
                name='Paradero inválido',
                stop_type=BusStop.STOP_TYPE_ZONAL,
                gtfs_stop_id='zonal-invalid',
                location=BOGOTA_POINT,
                cenefa='001A01',
                transmilenio_id=9999,
            )


@pytest.mark.django_db
def test_bus_stop_constraint_rejects_trunk_stop_missing_transmilenio_id():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            BusStop.objects.create(
                name='Estación inválida',
                stop_type=BusStop.STOP_TYPE_TRUNK,
                gtfs_stop_id='trunk-invalid',
                location=BOGOTA_POINT,
            )


@pytest.mark.django_db
def test_bus_stop_constraint_rejects_cable_stop_with_cenefa():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            BusStop.objects.create(
                name='Cable inválido',
                stop_type=BusStop.STOP_TYPE_CABLE,
                gtfs_stop_id='cable-invalid',
                location=BOGOTA_POINT,
                cenefa='999Z99',
            )


@pytest.mark.django_db
def test_route_constraint_requires_corridor_for_troncal_service_tier():
    corridor = make_corridor()

    route = make_route(
        'troncal-with-corridor',
        route_mode=Route.ROUTE_MODE_TRUNK,
        service_tier=Route.SERVICE_TIER_TRUNK,
        corridor=corridor,
    )

    assert route.corridor == corridor


@pytest.mark.django_db
def test_route_constraint_rejects_troncal_route_without_corridor():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            make_route(
                'troncal-without-corridor',
                route_mode=Route.ROUTE_MODE_TRUNK,
                service_tier=Route.SERVICE_TIER_TRUNK,
            )


@pytest.mark.django_db
def test_route_constraint_rejects_non_troncal_route_with_corridor():
    corridor = make_corridor(name='Autopista Norte')

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            make_route(
                'dual-with-corridor',
                route_mode=Route.ROUTE_MODE_TRUNK,
                service_tier=Route.SERVICE_TIER_DUAL,
                corridor=corridor,
            )


@pytest.mark.django_db
def test_route_dual_and_cable_tiers_do_not_require_a_corridor():
    dual_route = make_route(
        'dual-route',
        code='M86-K86',
        route_mode=Route.ROUTE_MODE_TRUNK,
        service_tier=Route.SERVICE_TIER_DUAL,
    )
    cable_route = make_route(
        'cable-route',
        code='CABLE',
        route_mode=Route.ROUTE_MODE_CABLE,
        service_tier=Route.SERVICE_TIER_CABLE,
    )

    assert dual_route.corridor is None
    assert cable_route.corridor is None


@pytest.mark.django_db
def test_corridor_accepts_valid_hex_color():
    corridor = make_corridor(color='#4f7a5b')

    assert corridor.color == '#4f7a5b'


@pytest.mark.django_db
def test_corridor_rejects_non_hex_color():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            make_corridor(name='Invalid color corridor', color='green')


@pytest.mark.django_db
def test_corridor_rejects_short_hex_color():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            make_corridor(name='Short hex corridor', color='#4f7a5')


@pytest.mark.django_db
@pytest.mark.parametrize(
    'day_type',
    ['L-V', 'SAB', 'L-S', 'DOM', 'L-V-D', 'SAB-DOM', 'DIARIO'],
)
def test_route_schedule_accepts_all_seven_real_day_types(day_type):
    route = make_route(f'route-for-{day_type}')

    schedule = RouteSchedule.objects.create(
        route=route,
        day_type=day_type,
        start_time='04:00:00',
        end_time='22:00:00',
    )

    assert schedule.day_type == day_type


@pytest.mark.django_db
def test_route_schedule_rejects_unrecognized_day_type():
    route = make_route('route-for-unknown-day-type')
    schedule = RouteSchedule(
        route=route,
        day_type='UNKNOWN',
        start_time='04:00:00',
        end_time='22:00:00',
    )

    with pytest.raises(ValidationError):
        schedule.full_clean()


@pytest.mark.django_db
def test_route_schedule_day_type_constraint_catches_raw_save_bypass():
    """Regression guard: full_clean() isn't the only path — a raw
    .save() (e.g. from Story 1.3's bulk ingestion) must also be
    rejected at the DB level, not just by Python-side validation.
    """
    route = make_route('route-for-raw-save-bypass')

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            RouteSchedule.objects.create(
                route=route,
                day_type='UNKNOWN',
                start_time='04:00:00',
                end_time='22:00:00',
            )


@pytest.mark.django_db
def test_route_schedule_rejects_end_time_before_start_time():
    route = make_route('route-for-inverted-schedule')

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            RouteSchedule.objects.create(
                route=route,
                day_type='L-V',
                start_time='22:00:00',
                end_time='04:00:00',
            )


@pytest.mark.django_db
def test_route_schedule_accepts_end_time_after_start_time():
    route = make_route('route-for-valid-schedule')

    schedule = RouteSchedule.objects.create(
        route=route,
        day_type='L-V',
        start_time='04:00:00',
        end_time='22:00:00',
    )

    assert schedule.end_time > schedule.start_time


@pytest.mark.django_db
def test_route_mode_service_tier_constraint_rejects_invalid_combination():
    """Only 7 (route_mode, service_tier) pairs occur in the real feed
    (Dev Notes' agency_id table) — a mismatched pair like a
    TransMiCable route claiming the troncal tier must be rejected.
    """
    corridor = make_corridor(name='Mismatched combination corridor')

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            make_route(
                'cable-with-troncal-tier',
                route_mode=Route.ROUTE_MODE_CABLE,
                service_tier=Route.SERVICE_TIER_TRUNK,
                corridor=corridor,
            )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'route_mode,service_tier',
    [
        (Route.ROUTE_MODE_TRUNK, Route.SERVICE_TIER_TRUNK),
        (Route.ROUTE_MODE_TRUNK, Route.SERVICE_TIER_FEEDER),
        (Route.ROUTE_MODE_TRUNK, Route.SERVICE_TIER_DUAL),
        (Route.ROUTE_MODE_ZONAL, Route.SERVICE_TIER_URBAN),
        (Route.ROUTE_MODE_ZONAL, Route.SERVICE_TIER_COMPLEMENTARY),
        (Route.ROUTE_MODE_ZONAL, Route.SERVICE_TIER_SPECIAL),
        (Route.ROUTE_MODE_CABLE, Route.SERVICE_TIER_CABLE),
    ],
)
def test_route_mode_tier_accepts_all_seven_valid_combinations(
    route_mode, service_tier
):
    corridor = None
    if service_tier == Route.SERVICE_TIER_TRUNK:
        corridor = make_corridor(
            name=f'Corridor for {route_mode}-{service_tier}'
        )

    route = make_route(
        f'route-for-{route_mode}-{service_tier}',
        route_mode=route_mode,
        service_tier=service_tier,
        corridor=corridor,
    )

    assert route.route_mode == route_mode
    assert route.service_tier == service_tier


@pytest.mark.django_db
def test_corridor_deletion_is_protected_when_referenced_by_a_troncal_route():
    """on_delete=PROTECT (not SET_NULL): route_corridor_required_for_
    troncal_only forbids a troncal route from ever having corridor=NULL,
    so SET_NULL would raise IntegrityError on delete instead of a clean,
    expected ProtectedError.
    """
    corridor = make_corridor(name='Corridor in use')
    make_route(
        'troncal-using-corridor',
        route_mode=Route.ROUTE_MODE_TRUNK,
        service_tier=Route.SERVICE_TIER_TRUNK,
        corridor=corridor,
    )

    with pytest.raises(ProtectedError):
        corridor.delete()
