import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

DATA_ROOT = settings.BASE_DIR / "data"


class BaseDataImportCommand(BaseCommand):
    model = None
    default_filename = None

    def add_arguments(self, parser):
        parser.add_argument(
            "filename", default=self.default_filename, nargs="?", type=str
        )

    def handle(self, *args, **options):
        filename = options["filename"]
        try:
            with open(Path(DATA_ROOT) / filename, "r", encoding="utf-8") as f:
                bulk_data = [
                    self.model(**item)  # type: ignore
                    for item in json.load(f)
                ]
                self.model.objects.bulk_create(
                    bulk_data, ignore_conflicts=True
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"""Данныe из файла {filename} успешно импортированы.
                        Импортировано - {len(set(bulk_data))} шт."""
                    )
                )
        except Exception as e:
            raise CommandError(f"Произошла ошибка: {e} в файле {filename}.")
