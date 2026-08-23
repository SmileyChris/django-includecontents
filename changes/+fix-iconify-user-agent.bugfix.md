Send a `django-includecontents` User-Agent when fetching from the Iconify API. The default `Python-urllib` agent was rejected with a 403, which broke icon sprite generation during `collectstatic`.
