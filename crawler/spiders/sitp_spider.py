import scrapy


class SitpSpider(scrapy.Spider):
    name = 'sitp'

    start_urls = [
        'https://www.transmilenio.gov.co/loader.php?'
        'lServicio=Rutas&lTipo=busqueda&lFuncion=lstRutasAjax'
        '&draw=1&columns%5B0%5D%5Bdata%5D=0'
        '&columns%5B0%5D%5Bsearchable%5D=true'
        '&columns%5B0%5D%5Borderable%5D=false'
        '&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false'
        '&start=40&length=20&search%5Bregex%5D=false&_=1642795202244',
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
            selector = scrapy.Selector(text=item[0], type='html')
            route_data = {
                'code': selector.css(
                    '.containerCodigo .codigoRuta::text'
                ).get(),
                'name': selector.css(
                    '.containerInfoListRuta .rutaNombre::text'
                )
                .get()
                .strip(),
                'url': selector.css('.containerInfoListRuta a').attrib['href'],
                'schedule': selector.css(
                    '.containerInfoListRuta .label-horario::text'
                ).getall(),
            }
            yield route_data

        self.log(
            f"draw: {response_json['draw']}, "
            f"recordsTotal: {response_json['recordsTotal']}, "
            f"recordsFiltered: {response_json['recordsFiltered']}"
        )
