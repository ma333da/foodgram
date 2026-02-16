from recipe.models import Tag

from .load_data_base import BaseDataImportCommand


class Command(BaseDataImportCommand):
    help = 'loading ingredients from data in json'
    model = Tag
    default_filename = 'tags.json'
