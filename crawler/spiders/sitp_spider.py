import re
import urllib.parse
from typing import Union
import logging

import scrapy

from crawler.items import RouteItem
from crawler.items import BusStationItem
from crawler.utlis import parse_route_color
from crawler.utlis import parse_station_unique_id


class SitpSpider(scrapy.Spider):
    name = 'sitp'
    routes_pagination_start = 0
    routes_pagination_draw = 1
    routes_pagination_length = 20
    routes_url_params = {
        'lServicio': 'Rutas',
        'lTipo': 'busqueda',
        'lFuncion': 'lstRutasAjax',
        'draw': routes_pagination_draw,
        'columns[0][data]': 0,
        'columns[0][searchable]': True,
        'columns[0][orderable]': False,
        'columns[0][search][regex]': False,
        'start': routes_pagination_start,
        'length': routes_pagination_length,
        'search[regex]': False,
        '_': 1642795202244,
    }
    routes_base_url = 'https://www.transmilenio.gov.co/loader.php'

    start_urls = [
        f'{routes_base_url}?{urllib.parse.urlencode(routes_url_params)}'
    ]

    def get_next_routes_url(self, total_records: int) -> Union[str, None]:
        self.routes_pagination_start = (
            self.routes_pagination_start + self.routes_pagination_length
        )
        self.log(
            f'---> pagination start: {self.routes_pagination_start} '
            f'-> total_records: {total_records}'
        )
        if self.routes_pagination_start > total_records:
            return None

        self.routes_url_params['draw'] = self.routes_url_params['draw'] + 1
        self.routes_url_params['start'] = self.routes_pagination_start
        next_routes_url = (
            f'{self.routes_base_url}?'
            f'{urllib.parse.urlencode(self.routes_url_params)}'
        )
        return next_routes_url

    def parse(self, response):
        response_json = response.json()
        data = response_json['data']
        for item in data:
            route_item = RouteItem()
            selector = scrapy.Selector(text=item[0], type='html')

            route_item['code'] = selector.css(
                '.containerCodigo .codigoRuta::text'
            ).get()
            route_item['color'] = parse_route_color(
                selector.css('.containerCodigo .codigoRuta').attrib['style']
            )
            route_item['name'] = (
                selector.css('.containerInfoListRuta .rutaNombre::text')
                .get()
                .strip()
            )
            route_item['details_link'] = selector.css(
                '.containerInfoListRuta a'
            ).attrib['href']
            route_item['schedule'] = '; '.join(
                selector.css(
                    '.containerInfoListRuta .label-horario::text'
                ).getall()
            )
            route_item['route_type'] = ''
            yield route_item
            yield scrapy.Request(
                route_item['details_link'],
                callback=self.parse_route_detail_proxy_page,
                meta={'route_item': route_item},
            )

        next_page = self.get_next_routes_url(
            total_records=int(response_json['recordsFiltered']),
        )
        if next_page is not None:
            yield response.follow(
                next_page,
                self.parse,
            )

        self.log(
            f"draw: {response_json['draw']}, "
            f"recordsTotal: {response_json['recordsTotal']}, "
            f"recordsFiltered: {response_json['recordsFiltered']}"
        )

    def parse_route_detail_proxy_page(self, response):
        script_pattern = r'var detailUrl = \'(.*)\'\.replace.*;\n'
        details_url = (
            response.css('script:contains("detailUrl")::text')
            .re_first(script_pattern)
            .replace('&amp;', '&')
        )
        yield response.follow(
            details_url,
            self.parse_route_detail_page,
            meta={'route_item': response.meta['route_item']},
        )

    def parse_route_station(self, station_data):
        station_url = station_data.css('.estNombre a::attr(href)').get()

        transmilenio_id = None
        follow_link = ''
        if station_url:
            transmilenio_id = urllib.parse.parse_qs(
                urllib.parse.urlparse(station_url).query
            ).get('estacion')
            if transmilenio_id:
                transmilenio_id = int(transmilenio_id[0])
            if transmilenio_id:
                url_params = {
                    'lServicio': 'Rutas',
                    'lTipo': 'busqueda',
                    'lFuncion': 'paradas',
                    'paradero': int(transmilenio_id),
                }
                follow_link = (
                    f'{self.routes_base_url}?'
                    f'{urllib.parse.urlencode(url_params)}'
                )

        return {
            'name': station_data.css('.estNombre::text').get(),
            'code': station_data.css('.estDireccion::text').get(),
            'link': station_url or '',
            'follow_link': follow_link,
            'transmilenio_id': transmilenio_id,
        }

    def parse_station_detail_page(self, response):
        station_item = response.meta['station_item']
        cenefa_text = response.css('#resultadoBusqueda .focus::text').get()
        cenefa = parse_station_unique_id(cenefa_text)
        station_item.update(
            {
                'cenefa': cenefa,
            }
        )
        yield BusStationItem(**station_item)

    def parse_route_detail_page(self, response):
        route_item = response.meta['route_item']
        code = response.css('.codigoRuta::text').get()
        if route_item['code'] != code:
            self.log(
                f'Route code does not match: {route_item["code"]} != {code}',
                level=logging.ERROR,
            )
        route_item['route_type'] = response.css(
            '.nombretipoRutaInfo::text',
        ).get()

        # TODO: save response.css('.rutaEstacionesNombre::text').get()
        # Example: Metrovivienda - Casablanca Norte

        # TODO: save response.css('.fechas_pub_mod span::text').getall()
        # Example: ['&Uacuteltima actualización  :', '30/10/2019']

        directions = response.css('.checkSentido::text').getall()
        if directions:
            route_item['route_1'] = []
            for station in response.css(
                '.recorrido .recorrido1 .estacionRecorrido'
            ):
                station = self.parse_route_station(station)
                if station['follow_link']:
                    route_item['route_1'].append(station)
                    yield response.follow(
                        station['follow_link'],
                        self.parse_station_detail_page,
                        meta={'station_item': station},
                    )
            route_item['route_2'] = []
            for station in response.css(
                '.recorrido .recorrido2 .estacionRecorrido'
            ):
                station = self.parse_route_station(station)
                if station['follow_link']:
                    route_item['route_2'].append(station)
                    yield response.follow(
                        station['follow_link'],
                        self.parse_station_detail_page,
                        meta={'station_item': station},
                    )
        else:
            route_item['route_1'] = []
            for station in response.css('.recorrido .recorrido1'):
                station = self.parse_route_station(station)
                if station['follow_link']:
                    route_item['route_1'].append(station)
                    yield response.follow(
                        station['follow_link'],
                        self.parse_station_detail_page,
                        meta={'station_item': station},
                    )
        yield route_item
