from recipe.models import Ingredient

from .load_data_base import BaseDataImportCommand


class Command(BaseDataImportCommand):
    help = 'loading ingredients from data in json'
    model = Ingredient
    default_filename = 'ingredients.json'
