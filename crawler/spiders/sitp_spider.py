import scrapy


class SitpSpider(scrapy.Spider):
    name = "sitp"

    def start_requests(self):
        urls = [
            "https://www.transmilenio.gov.co/loader.php?"
            "lServicio=Rutas&lTipo=busqueda&lFuncion=lstRutasAjax"
            "&draw=1&columns%5B0%5D%5Bdata%5D=0"
            "&columns%5B0%5D%5Bsearchable%5D=true"
            "&columns%5B0%5D%5Borderable%5D=false"
            "&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false"
            "&start=40&length=20&search%5Bregex%5D=false&_=1642795202244",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        print(response.body)
        self.log(f"")
