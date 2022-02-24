# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from routes.models import Route


class CrawlerPipeline:
    """Saves Item to the database."""

    def process_item(self, item, spider):
        obj, created = Route.objects.update_or_create(
            code=item['code'],
            defaults=dict(
                name=item['name'],
                details_link=item['details_link'],
                schedule=item['schedule'],
            ),
        )

        save_status_str = 'created' if created else 'updated'
        spider.log(f'=== Route {obj.code} was {save_status_str}')
        return obj
