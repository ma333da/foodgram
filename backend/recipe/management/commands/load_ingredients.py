from .load_data_base import BaseDataImportCommand
from recipe.models import Ingredient


class Command(BaseDataImportCommand):
    help = 'loading ingredients from data in json'
    model = Ingredient
    default_filename = 'ingredients.json'
    field_map = {'name': 'name', 'measurement_unit': 'measurement_unit'}
