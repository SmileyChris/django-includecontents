HTML-based components now have access to all context variables provided by context processors, not just the request object and CSRF token

This ensures consistent behavior between HTML components and regular Django templates.