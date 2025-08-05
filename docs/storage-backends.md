# Storage Backends

The icons system supports pluggable storage backends for maximum deployment flexibility.

## Available Backends

### DjangoFileIconStorage (Default)
Integrates with Django's static file system.

```python
INCLUDECONTENTS_ICONS = {
    'storage': 'includecontents.icons.storages.DjangoFileIconStorage',
    'storage_options': {
        'location': 'icons/',  # Path within static storage
    }
}
```

**Best for**: Production deployments, works with your existing static file setup.

### MemoryIconStorage
Stores sprites in memory for fast development.

```python
INCLUDECONTENTS_ICONS = {
    'storage': 'includecontents.icons.storages.MemoryIconStorage',
}
```

**Best for**: Development, testing, temporary storage.

### FileSystemIconStorage
Direct file system storage with custom paths.

```python
INCLUDECONTENTS_ICONS = {
    'storage': 'includecontents.icons.storages.FileSystemIconStorage',
    'storage_options': {
        'location': '/var/www/static/icons',
        'base_url': 'https://cdn.example.com/icons/',
    }
}
```

**Best for**: Custom deployment scenarios with specific file paths.

## Cloud Storage Examples

### AWS S3
```python
INCLUDECONTENTS_ICONS = {
    'storage': 'includecontents.icons.storages.DjangoFileIconStorage',
    'storage_options': {
        'storage': 'storages.backends.s3boto3.S3Boto3Storage',
        'location': 'icons/',
    }
}
```

### Google Cloud Storage
```python
INCLUDECONTENTS_ICONS = {
    'storage': 'includecontents.icons.storages.DjangoFileIconStorage',
    'storage_options': {
        'storage': 'storages.backends.gcloud.GoogleCloudStorage',
        'location': 'icons/',
    }
}
```

## Environment-Specific Configuration

```python
import os

# Choose storage based on environment
if os.environ.get('ICON_STORAGE') == 'memory':
    ICON_STORAGE_CONFIG = {
        'storage': 'includecontents.icons.storages.MemoryIconStorage',
    }
elif os.environ.get('ICON_STORAGE') == 's3':
    ICON_STORAGE_CONFIG = {
        'storage': 'includecontents.icons.storages.DjangoFileIconStorage',
        'storage_options': {
            'storage': 'storages.backends.s3boto3.S3Boto3Storage',
            'location': 'icons/',
        }
    }
else:
    ICON_STORAGE_CONFIG = {}  # Use defaults

INCLUDECONTENTS_ICONS = {
    'icons': ['mdi:home', 'tabler:user'],
    **ICON_STORAGE_CONFIG,
}
```

## Custom Storage Backend

Create your own storage backend by extending `BaseIconStorage`:

```python
from includecontents.icons.storages import BaseIconStorage

class RedisIconStorage(BaseIconStorage):
    def __init__(self, redis_client=None):
        import redis
        self.client = redis_client or redis.Redis()
    
    def save(self, name: str, content: str) -> str:
        self.client.set(f"icons:{name}", content)
        return name
    
    def open(self, name: str) -> Optional[str]:
        content = self.client.get(f"icons:{name}")
        return content.decode('utf-8') if content else None
    
    def exists(self, name: str) -> bool:
        return bool(self.client.exists(f"icons:{name}"))
    
    def url(self, name: str) -> Optional[str]:
        return None  # Redis doesn't provide URLs
    
    def delete(self, name: str) -> bool:
        return bool(self.client.delete(f"icons:{name}"))
```

Use it in settings:
```python
INCLUDECONTENTS_ICONS = {
    'storage': 'myapp.storages.RedisIconStorage',
    'storage_options': {
        'redis_client': redis.Redis(host='localhost', port=6379)
    }
}
```