Add Django template tag support in component attributes. Component attributes now fully support Django template syntax including `{% url %}`, `{{ variables }}`, `{% if %}` conditionals, and all other template tags.

```html
<include:ui-button 
  variant="primary" 
  href="{% url 'settings' %}" 
  class="btn {% if large %}btn-lg{% endif %}"
>
  Save Settings
</include:ui-button>
```