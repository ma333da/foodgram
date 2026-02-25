import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

DATA_ROOT = settings.BASE_DIR / 'data'


class BaseDataImportCommand(BaseCommand):
    model = None
    default_filename = None

    def add_arguments(self, parser):
        parser.add_argument(
            'filename', default=self.default_filename, nargs='?', type=str
        )

    def handle(self, *args, **options):
        filename = options['filename']
        try:
            with open(Path(DATA_ROOT) / filename, 'r', encoding='utf-8') as f:
                create_objects = self.model.objects.bulk_create(
                    list(map(lambda x: self.model(**x), json.load(f))),
                    ignore_conflicts=True,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Данныe из файла {filename} успешно импортированы.'
                        f'Импортировано - {len(create_objects)} шт.'
                    )
                )
        except Exception as e:
            raise CommandError(f'Произошла ошибка: {e} в файле {filename}.')
