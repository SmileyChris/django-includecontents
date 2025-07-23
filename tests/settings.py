INSTALLED_APPS = [
    "includecontents",
]

TEMPLATES = [
    {
        "BACKEND": "includecontents.django.DjangoTemplates",
        "DIRS": ["tests/templates"],
        "OPTIONS": {},
    }
]

# Required Django settings
SECRET_KEY = 'test-secret-key'
USE_TZ = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
