import json
from pathlib import Path
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand, CommandError

DATA_ROOT = settings.BASE_DIR / 'data'


class BaseDataImportCommand(BaseCommand):
    model = None
    default_filename = None
    field_map = None

    def add_arguments(self, parser):
        parser.add_argument(
            'filename', default=self.default_filename, nargs='?', type=str
        )

    def handle(self, *args, **options):
        filename = options['filename']
        try:
            with open(
                Path(DATA_ROOT) / filename, 'r', encoding='utf-8'
            ) as f:
                bulk_data = [
                    self.model(**item) # type: ignore
                    for item in json.load(f)
                ]
                self.model.objects.bulk_create(bulk_data)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Данный из файла {filename}\
                            успешно импортированы.\
                            Строки импортированы\
                            в количестве - {len(bulk_data)} шт.'
                    )
                )
        except FileNotFoundError:
            raise CommandError(
                f'Файл {options["filename"]} не найден по пути {DATA_ROOT}.'
            )
        except FieldDoesNotExist as e: 
            raise CommandError( 
                f'Поле не найдено в модели: {str(e)}'
            )
        except Exception as e:
            raise CommandError(f'Произошла ошибка: {str(e)}')