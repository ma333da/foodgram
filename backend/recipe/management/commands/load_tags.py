import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipe.models import Tag

DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')


class Command(BaseCommand):
    help = 'loading ingredients from data in json'

    def add_arguments(self, parser):
        parser.add_argument('filename', default='tags.json', nargs='?',
                            type=str)

    def handle(self, *args, **options):
        with open(
                os.path.join(
                    DATA_ROOT,
                    options['filename']), 'r', encoding='utf-8') as f:
            data = json.load(f)
            bulk_data = [
                Tag(
                    name=tag['name'],
                    slug=tag['slug']
                ) for tag in data
            ]
            Tag.objects.bulk_create(bulk_data)
