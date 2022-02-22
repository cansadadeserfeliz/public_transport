# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy_djangoitem import DjangoItem

from routes.models import Route


class RouteItem(DjangoItem):
    django_model = Route
