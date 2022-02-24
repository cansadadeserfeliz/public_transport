# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from routes.models import Route


class CrawlerPipeline:
    """Saves Item to the database."""

    def process_item(self, item, spider):
        code = item['code'].strip()
        colors_to_route_type = {
            '#00608B': Route.ROUTE_TYPE_URBAN,
            '#00398B': Route.ROUTE_TYPE_BRT,
            '#376530': Route.ROUTE_TYPE_SHUTTLE,
            '#95B734': Route.ROUTE_TYPE_BRT,
            '#EABF3B': Route.ROUTE_TYPE_BRT,
            '#7B6CA7': Route.ROUTE_TYPE_BRT,
            '#9C6C0C': Route.ROUTE_TYPE_BRT,
            '#BB0615': Route.ROUTE_TYPE_BRT,
            '#3D9CD7': Route.ROUTE_TYPE_BRT,
            '#D88C00': Route.ROUTE_TYPE_BRT,
            '#D07400': Route.ROUTE_TYPE_COMPLEMENTARY,
            '#D0A2AA': Route.ROUTE_TYPE_BRT,
            '#CAB07C': Route.ROUTE_TYPE_BRT,
            '#00949C': Route.ROUTE_TYPE_BRT,
            '#8A0079': Route.ROUTE_TYPE_BRT,
            '#6C102D': Route.ROUTE_TYPE_SPECIAL,
        }
        route_type = colors_to_route_type.get(item['color'], '')
        if not route_type and item['code'] in [
            '6-18',
            '10-10',
            '10-11',
            '10-12',
            '14-6',
            '18-7',
            '18-9',
            '18-11',
            '18-12.8',
            '18-13',
            '18-14',
            'T08',
        ]:
            route_type = Route.ROUTE_TYPE_SPECIAL

        obj, created = Route.objects.update_or_create(
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
        spider.log(f'=== Route {obj.code} was {save_status_str}')
        return obj
