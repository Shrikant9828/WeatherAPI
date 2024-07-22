from django.core.management.base import BaseCommand
from weather_api.dump import dump_wx_data, dump_statistics


class Command(BaseCommand):
    help = "Create database tables and ingest data"

    def handle(self, *args, **kwargs):
        dump_wx_data()
        dump_statistics()
