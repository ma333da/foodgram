## Автор

Владимир Симоньянц [ma333da](https://ma333da@yandex.ru)

## Техно стек
[![Python](https://img.shields.io/badge/-Python-464646?style=flat&logo=Python&logoColor=56C0C0&color=008080)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat&logo=Django&logoColor=56C0C0&color=008080)](https://www.djangoproject.com/)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat&logo=NGINX&logoColor=56C0C0&color=008080)](https://nginx.org/ru/)


## Команды запуска

- Клонируем репозиторий

```bash
git clone https://github.com/ma333da/foodgramt.git
```

- Запускаем docker compose:

```bash
cd ../infra
docker-compose up -d --build
```

- Выполняем миграции:

```bash
docker-compose exec backend python manage.py migrate
```

- Создаем суперпользователя:

```bash
docker-compose exec backend python manage.py createsuperuser
```

- Загружаем статику:

```bash
docker-compose exec backend python manage.py collectstatic --no-input
```

- Заполняем базу тестовыми данными:

```bash
docker-compose exec backend python manage.py load_ingredients
docker-compose exec backend python manage.py load_tags   
```


## Как запустить проекта локально

- Клонируем репозиторий

```bash
git clone https://github.com/ma333da/foodgramt.git
```

- Уставливаем python=3.9 и создаем виртуальное окружение

```bash
cd ./foodgram/backend
python3 -m venv foodgram
```

- Активируем виртуальное окружение

```bash
source /venv/bin/activate
```

- Устанавливаем зависимости из файла requirements.txt

```bash
python -m pip install --upgrade pip
```
```bash
pip install -r requirements.txt
```
- Создаем файл .env в папке проекта:
```.env
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
DEBUG=True
```

### Выполняем миграции:
```bash
python manage.py migrate
```

- В папке с файлом manage.py выполняем команду:
```bash
python manage.py runserver
```

- Созданем нового супер пользователя 
```bash
python manage.py createsuperuser
```

### Загружаем статику:
```bash
python manage.py collectstatic --no-input
```
### Заполняем базу тестовыми данными: 
```bash
python manage.py load_ingredients
python manage.py load_tags
```

## Основные ссылки: 
[Главная](https://ma333da.hopto.org)
[Админка](https://ma333da.hopto.org/admin/)
[Доки](https://ma333da.hopto.org/api/docs/)

