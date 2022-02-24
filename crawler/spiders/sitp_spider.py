import urllib.parse

import scrapy

from crawler.items import RouteItem


class SitpSpider(scrapy.Spider):
    name = 'sitp'
    routes_url_params = urllib.parse.urlencode(
        {
            'lServicio': 'Rutas',
            'lTipo': 'busqueda',
            'lFuncion': 'lstRutasAjax',
            'draw': 1,
            'columns[0][data]': 0,
            'columns[0][searchable]': True,
            'columns[0][orderable]': False,
            'columns[0][search][regex]': False,
            'start': 0,
            'length': 20,
            'search[regex]': False,
            '_': 1642795202244,
        }
    )

    start_urls = [
        'https://www.transmilenio.gov.co/loader.php?%s' % routes_url_params
    ]

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

        self.log(
            f"draw: {response_json['draw']}, "
            f"recordsTotal: {response_json['recordsTotal']}, "
            f"recordsFiltered: {response_json['recordsFiltered']}"
        )
