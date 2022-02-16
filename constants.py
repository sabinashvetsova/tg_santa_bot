# список имен пользователей и тех, кто не должен им попасться
ALLOWED_USERS = [
    {
        'name': 'Name:::Surname',
        'deny': 'Name2:::Surname2'
    },
    {
        'name': 'Name2:::Surname2',
        'deny': 'Name:::Surname'
    },
    {
        'name': 'Name3:::Surname3',
        'deny': 'qweqwe'
    },
]

# токен бота
TOKEN = "gashffdgahsfdgfasghdf"

# имя того, кто будет запускать розыгрыш
ADMIN_NAME = "Name:::Surname"
