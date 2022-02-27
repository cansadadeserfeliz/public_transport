# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
import scrapy
from scrapy_djangoitem import DjangoItem

from routes.models import BusStation
from routes.models import Route


class BusStationItem(DjangoItem):
    django_model = BusStation
    follow_link = scrapy.Field()


class RouteItem(DjangoItem):
    django_model = Route
    route_1 = scrapy.Field()
    route_2 = scrapy.Field()
