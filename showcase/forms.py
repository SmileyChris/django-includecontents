from django import forms
from typing import Any, Dict

from .models import ComponentInfo, PropDefinition


class PropEditorForm(forms.Form):
    """Dynamic form for editing component props."""

    def __init__(self, component: ComponentInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.component = component

        # Create form fields for each prop
        for prop_name, prop_def in component.props.items():
            field = self._create_field_for_prop(prop_def)
            if field:
                self.fields[prop_name] = field

    def _create_field_for_prop(self, prop_def: PropDefinition) -> forms.Field:
        """Create appropriate form field for a prop definition."""
        field_kwargs = {
            "label": prop_def.name.replace("_", " ").title(),
            "required": prop_def.required,
            "help_text": prop_def.description,
        }

        if prop_def.default is not None:
            field_kwargs["initial"] = prop_def.default

        data_required = str(prop_def.required).lower()

        if prop_def.type == "boolean":
            return forms.BooleanField(
                **field_kwargs,
                widget=forms.CheckboxInput(
                    attrs={
                        "class": "form-checkbox",
                        "data-prop": prop_def.name,
                        "data-required": data_required,
                    }
                ),
            )

        elif prop_def.type == "number":
            return forms.IntegerField(
                **field_kwargs,
                widget=forms.NumberInput(
                    attrs={
                        "class": "form-input",
                        "data-prop": prop_def.name,
                        "data-required": data_required,
                    }
                ),
            )

        elif prop_def.type == "enum" or prop_def.is_enum:
            choices = [(val, val or "(empty)") for val in prop_def.allowed_values]
            return forms.ChoiceField(
                choices=choices,
                **field_kwargs,
                widget=forms.Select(
                    attrs={
                        "class": "form-select",
                        "data-prop": prop_def.name,
                        "data-required": data_required,
                    }
                ),
            )

        else:
            # Default to text field
            return forms.CharField(
                **field_kwargs,
                widget=forms.TextInput(
                    attrs={
                        "class": "form-input",
                        "data-prop": prop_def.name,
                        "data-required": data_required,
                    }
                ),
            )
