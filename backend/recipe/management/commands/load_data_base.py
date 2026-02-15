import json
from pathlib import Path

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand, CommandError

DATA_ROOT = Path(settings.BASE_DIR) / 'data'


class BaseDataImportCommand(BaseCommand):
    model = None
    default_filename = None
    field_map = None

    def add_arguments(self, parser):
        parser.add_argument(
            'filename', default=self.default_filename, nargs='?', type=str
        )

    def handle(self, *args, **options):
        try:
            with open(
                Path(DATA_ROOT) / options['filename'], 'r', encoding='utf-8'
            ) as f:
                bulk_data = [
                    self.model(
                        **{
                            field_name: item[field_source]
                            for (
                                field_name, field_source
                            ) in self.field_map.items()
                        }
                    )  # type: ignore
                    for item in json.load(f)
                ]
                self.model.objects.bulk_create(bulk_data)
        except FieldDoesNotExist:
            raise CommandError(
                f'Файл {options["filename"]} не найден по пути {DATA_ROOT}.'
            )
