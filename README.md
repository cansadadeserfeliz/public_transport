# :oncoming_bus: Public transport

## :busstop: Installation

    $ pip install -r requirements.txt
    $ pre-commit install
    $ python manage.py migrate

## :bus: Run the spider

    scrapy crawl sitp

Load additional data for bus stations from geojson file:

    python manage.py load_bus_stations

## :roller_coaster: Run server

    python manage.py runserver

---

*Fuente: TRANSMILENIO S.A: www.transmilenio.gov.co*
