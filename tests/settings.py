import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

INSTALLED_APPS = [
    "includecontents",
    "django.contrib.staticfiles",
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

# Static files configuration for tests
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'tests' / 'static',
]

STATICFILES_FINDERS = [
    'includecontents.icons.finders.IconSpriteFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Icons configuration for tests  
INCLUDECONTENTS_ICONS = {
    'icons': [
        ('home', 'mdi:home'),  # Map 'home' component to 'mdi:home' icon
        ('user', 'tabler:user'),  # Map 'user' component to 'tabler:user' icon
        ('custom-home', 'mdi:home'),  # Tuple format
        ('local-svg', 'icons/custom-home.svg'),  # Local SVG file with custom name
        ('my-star', 'icons/custom-star.svg'),  # Local SVG with custom name
    ],
    'dev_mode': True,
    'cache_timeout': 3600,
    'storage': 'includecontents.icons.storages.MemoryIconStorage',
}
