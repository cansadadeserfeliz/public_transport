# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from crawler.items import RouteItem
from crawler.items import BusStationItem
from routes.models import Route
from routes.models import BusStation
from routes.models import RouteStations


class CrawlerPipeline:
    """Saves Item to the database."""

    def process_item(self, item, spider):
        if isinstance(item, RouteItem):
            code = item['code'].strip()
            route_type_map = {
                'Ruta fácil': Route.ROUTE_TYPE_BRT,
                'Servicio express': Route.ROUTE_TYPE_BRT,
                'Duales': Route.ROUTE_TYPE_BRT,
                'Urbanas': Route.ROUTE_TYPE_URBAN,
                'Alimentadoras': Route.ROUTE_TYPE_SHUTTLE,
                'Especiales': Route.ROUTE_TYPE_SPECIAL,
                'Complementarias': Route.ROUTE_TYPE_COMPLEMENTARY,
            }
            route_type = route_type_map.get(item['route_type'], '')

            if item['route_type'] and item['route_type'] not in route_type_map:
                print(f"route type: /{item['route_type']}/")

            if not item['color'] and route_type:
                colors_map = {
                    Route.ROUTE_TYPE_URBAN: '#00608B',
                    Route.ROUTE_TYPE_SHUTTLE: '#376530',
                    Route.ROUTE_TYPE_COMPLEMENTARY: '#D07400',
                    Route.ROUTE_TYPE_SPECIAL: '#6C102D',
                }
                item['color'] = colors_map.get(route_type, '')

            route_obj, created = Route.objects.update_or_create(
                code=code,
                name=item['name'].strip(),
                defaults=dict(
                    details_link=item['details_link'],
                    schedule=item['schedule'],
                    color=item['color'],
                    route_type=route_type,
                ),
            )

            save_status_str = 'created' if created else 'updated'
            spider.log(f'>>> Route {route_obj.code} was {save_status_str}')

            if 'route_1' in item:
                RouteStations.objects.filter(route=route_obj).delete()

                for i, station_item in enumerate(item['route_1'], start=1):
                    bus_station, _ = BusStation.objects.update_or_create(
                        transmilenio_id=station_item['transmilenio_id'],
                        defaults=dict(
                            code=station_item['code'],
                            name=station_item['name'],
                            link=station_item['link'],
                        ),
                    )
                    RouteStations.objects.create(
                        direction=RouteStations.DIRECTION_1,
                        position=i,
                        bus_station=bus_station,
                        route=route_obj,
                    )

            if 'route_2' in item:
                for i, station_item in enumerate(item['route_2'], start=1):
                    bus_station, _ = BusStation.objects.update_or_create(
                        transmilenio_id=station_item['transmilenio_id'],
                        defaults=dict(
                            code=station_item['code'],
                            name=station_item['name'],
                            link=station_item['link'],
                        ),
                    )
                    RouteStations.objects.create(
                        direction=RouteStations.DIRECTION_2,
                        position=i,
                        bus_station=bus_station,
                        route=route_obj,
                    )

            return route_obj
        elif isinstance(item, BusStationItem):
            if item['transmilenio_id']:
                BusStation.objects.update_or_create(
                    transmilenio_id=item['transmilenio_id'],
                    defaults=dict(
                        code=item['code'],
                        name=item['name'],
                        link=item['link'],
                        cenefa=item['cenefa'],
                    ),
                )
