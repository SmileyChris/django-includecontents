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
