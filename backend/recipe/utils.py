from datetime import date

from django.http import FileResponse

date = date.today().isoformat


def generate_text(shop_list):
    lines = []
    for ing in shop_list:
        name = ing['ingredient__name']
        measurement_unit = ing['ingredient__measurement_unit']
        amount = ing['ingredient_total']
        lines.append(f'{name} ({measurement_unit}) - {amount}')
    content = '\n'.join(lines)
    return content


def convert_txt(shop_list):
    file_name = 'cart.txt'
    content = generate_text(shop_list)
    content_type = 'text/plain'
    response = FileResponse(
        content,
        content_type=content_type,
        filename=file_name
    )
    return response
