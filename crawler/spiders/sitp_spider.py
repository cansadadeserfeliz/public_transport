import urllib.parse
from typing import Union

import scrapy

from crawler.items import RouteItem
from crawler.utlis import parse_route_color


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

        """
        <div class="containerCodigo" style="border-left: none;">
           <div data-ss="tr"
              class="codigoRuta "
              style="border-bottom: 10px solid ;">12</div>
        </div>
        <div class="containerInfoListRuta">
           <a title="Fontibón San Pablo - Porciúncula" target="_blank"
              class="rutaNombre "
              href="https://www.transmilenio.gov.co/Rutas/servicio_troncal/
              12_fontibn_san_pablo_porcincula">
            Fontibón San Pablo - Porciúncula
           </a>
           <br>
           <p title="Lunes a S&aacute;bado 04:00 AM - 11:00 PM"
            class="label label-horario">
                L-S            | 04:00 AM            - 11:00 PM
           </p>
           &nbsp;
           <p title="Domingo y Festivo 05:00 AM - 10:00 PM"
            class="label label-horario">
                D-F            | 05:00 AM            - 10:00 PM
           </p>
           &nbsp;
        </div>
        """
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
            yield route_item

        next_page = self.get_next_routes_url(
            total_records=int(response_json['recordsFiltered']),
        )
        if next_page is not None:
            yield response.follow(next_page, self.parse)

        self.log(
            f"draw: {response_json['draw']}, "
            f"recordsTotal: {response_json['recordsTotal']}, "
            f"recordsFiltered: {response_json['recordsFiltered']}"
        )
