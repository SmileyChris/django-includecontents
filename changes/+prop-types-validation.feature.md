Add type-safe component props validation system with Django validators

- New `prop_types` module with component-focused types (Text, Integer, Email, Choice, etc.)
- Support for Python-defined props classes using dataclasses and type hints
- Enhanced template props syntax with type specifications: `{# props name:text email:email age:int(min=18) #}`
- Automatic validation at render time using Django's validator framework
- Full backward compatibility with existing props syntax
- IDE support through type hints when using Python props classes
- Custom validation through `clean()` methods on props classes