from django.template.loader import render_to_string
from django.http import FileResponse
from datetime import date


def generate_text(shop_list, recipes):
    context = {
        'date': date.today().isoformat(),
        'shop_list': [
            {
                'name': ing['ingredient__name'],
                'measurement_unit': ing['ingredient__measurement_unit'],
                'amount': ing['ingredient_total']
            }
            for ing in shop_list
        ],
        'recipes': recipes
    }
    rendered_template = render_to_string('shopping_list.txt', context)

    return FileResponse(
        rendered_template,
        content_type='text/plain',
        filename='cart.txt'
    )
