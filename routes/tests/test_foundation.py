"""Foundation smoke tests for the Django 5.2 + PostGIS upgrade.

Proves GDAL/GEOS are reachable from the app process and that Django
is configured against the postgis database engine, not SQLite.
"""

import django
from django.conf import settings
from django.contrib.gis.geos import Point


def test_geos_point_construction():
    """GEOS bindings (GDAL/GEOS system packages) are importable."""
    point = Point(-74.05, 4.65)

    assert point.x == -74.05
    assert point.y == 4.65


def test_database_engine_is_postgis():
    """The default database uses GeoDjango's PostGIS backend."""
    engine = settings.DATABASES['default']['ENGINE']

    assert engine == 'django.contrib.gis.db.backends.postgis'


def test_django_version_is_5_2():
    """Confirms the Django 5.2 LTS upgrade landed."""
    assert django.VERSION[:2] == (5, 2)
