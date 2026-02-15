from .load_data_base import BaseDataImportCommand
from recipe.models import Tag


class Command(BaseDataImportCommand):
    help = 'loading ingredients from data in json'
    model = Tag
    default_filename = 'tags.json'
    field_map = {'name': 'name', 'slug': 'slug'}
