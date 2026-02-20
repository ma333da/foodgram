from django.template.loader import render_to_string
from django.http import FileResponse
from datetime import date


def generate_text(shop_list, recipes):
    context = {
        'date': date.today().isoformat(),
        'shop_list': shop_list,
        'recipes': recipes
    }

    return FileResponse(
        render_to_string('shopping_list.txt', context),
        content_type='text/plain',
        filename='cart.txt'
    )
