import os
import json

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from routes.models import BusStation


class Command(BaseCommand):
    help = 'Loads additional info for bus stations from transmilenio.gov.co'

    def handle(self, *args, **options):
        f = open(
            os.path.join(
                settings.BASE_DIR, 'data/Paraderos_Zonales_del_SITP.geojson'
            )
        )
        data = json.load(f)
        for feature in data['features']:
            properties = feature['properties']

            try:
                bus_station = BusStation.objects.get(
                    cenefa=properties['cenefa']
                )
            except BusStation.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'{properties["cenefa"]} not found')
                )
                continue
            bus_station.cenefa = properties['cenefa']
            bus_station.name = properties['nombre']
            bus_station.audio = properties['audio']
            bus_station.longitude = properties['longitud']
            bus_station.latitude = properties['latitud']
            bus_station.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'{properties["direccion_bandera"]} updated'
                )
            )
        self.stdout.write(
            self.style.SUCCESS('Successfully loaded bus stations')
        )
