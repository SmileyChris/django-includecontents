"""Tests for MultiChoice prop type functionality."""

import pytest
from dataclasses import dataclass
from django.template import Template, Context
from django.test import TestCase

from includecontents.shared.typed_props import component
from includecontents.shared.validation import validate_props
from includecontents.django.prop_types import MultiChoice


class TestMultiChoiceType(TestCase):
    """Test MultiChoice prop type functionality."""

    def test_multichoice_validation_success(self):
        """Test that MultiChoice validates correct values."""
        @component('components/button.html')
        @dataclass
        class ButtonProps:
            variant: MultiChoice['primary', 'secondary', 'large', 'small']

        # Test single value
        result = validate_props(ButtonProps, {'variant': 'primary'})
        self.assertEqual(result['variant'], 'primary')
        self.assertEqual(result['variantPrimary'], True)

        # Test multiple values
        result = validate_props(ButtonProps, {'variant': 'primary large'})
        self.assertEqual(result['variant'], 'primary large')
        self.assertEqual(result['variantPrimary'], True)
        self.assertEqual(result['variantLarge'], True)

    def test_multichoice_validation_failure(self):
        """Test that MultiChoice rejects invalid values."""
        @component('components/button.html')
        @dataclass
        class ButtonProps:
            variant: MultiChoice['primary', 'secondary', 'large', 'small']

        with pytest.raises(Exception) as exc_info:
            validate_props(ButtonProps, {'variant': 'invalid'})
        
        self.assertIn('Invalid choice "invalid"', str(exc_info.value))

    def test_multichoice_camelcase_flags(self):
        """Test camelCase flag generation for various value formats."""
        @component('components/button.html')
        @dataclass
        class ButtonProps:
            variant: MultiChoice['primary', 'secondary', 'dark-mode', 'extra-large']

        # Test hyphenated values get converted to camelCase
        result = validate_props(ButtonProps, {'variant': 'dark-mode extra-large'})
        self.assertEqual(result['variant'], 'dark-mode extra-large')
        self.assertEqual(result['variantDarkMode'], True)
        self.assertEqual(result['variantExtraLarge'], True)
        
        # Test that unselected values don't get flags
        self.assertNotIn('variantPrimary', result)
        self.assertNotIn('variantSecondary', result)

    def test_multichoice_with_defaults(self):
        """Test MultiChoice with default values."""
        @component('components/button.html')
        @dataclass
        class ButtonProps:
            variant: MultiChoice['primary', 'secondary', 'large', 'small'] = 'primary'

        # Test with provided value
        result = validate_props(ButtonProps, {'variant': 'secondary'})
        self.assertEqual(result['variant'], 'secondary')
        self.assertEqual(result['variantSecondary'], True)

        # Test with default value
        result = validate_props(ButtonProps, {})
        self.assertEqual(result['variant'], 'primary')
        self.assertEqual(result['variantPrimary'], True)

    def test_multichoice_empty_value(self):
        """Test MultiChoice with empty values."""
        @component('components/button.html')
        @dataclass
        class ButtonProps:
            variant: MultiChoice['primary', 'secondary'] = ''

        result = validate_props(ButtonProps, {})
        self.assertEqual(result['variant'], '')
        # Empty values should not generate any flags
        self.assertNotIn('variantPrimary', result)
        self.assertNotIn('variantSecondary', result)

    def test_multichoice_mixed_with_other_props(self):
        """Test MultiChoice mixed with other prop types."""
        @component('components/card.html')
        @dataclass
        class CardProps:
            title: str
            variant: MultiChoice['primary', 'secondary']
            active: bool = False

        result = validate_props(CardProps, {
            'title': 'Test Card',
            'variant': 'primary',
            'active': True
        })
        
        self.assertEqual(result['title'], 'Test Card')
        self.assertEqual(result['variant'], 'primary')
        self.assertEqual(result['variantPrimary'], True)
        self.assertEqual(result['active'], True)

    def test_multichoice_space_handling(self):
        """Test that MultiChoice properly handles spaces in values."""
        @component('components/button.html')
        @dataclass
        class ButtonProps:
            variant: MultiChoice['primary', 'secondary', 'large']

        # Test multiple spaces
        result = validate_props(ButtonProps, {'variant': '  primary   large  '})
        self.assertEqual(result['variant'], '  primary   large  ')
        self.assertEqual(result['variantPrimary'], True)
        self.assertEqual(result['variantLarge'], True)

    def test_multichoice_collision_avoidance(self):
        """Test that MultiChoice flags don't collide with explicit props."""
        @component('components/button.html')
        @dataclass
        class ButtonProps:
            variant: MultiChoice['primary', 'secondary']
            # This would collide if user defined variantPrimary explicitly
            variant_primary_override: bool = False

        result = validate_props(ButtonProps, {
            'variant': 'primary',
            'variant_primary_override': True
        })
        
        # Both should coexist
        self.assertEqual(result['variant'], 'primary')
        self.assertEqual(result['variantPrimary'], True)
        self.assertEqual(result['variant_primary_override'], True)


class TestMultiChoiceTemplateIntegration(TestCase):
    """Test MultiChoice integration with templates."""

    def test_multichoice_in_template_context(self):
        """Test that MultiChoice flags are available in template context."""
        @component('components/button.html')
        @dataclass
        class ButtonProps:
            variant: MultiChoice['primary', 'secondary', 'large']

        # This would be set up in the template tag, but we'll simulate
        props_data = validate_props(ButtonProps, {'variant': 'primary large'})
        
        # Create a template that uses the flags
        template = Template("""
        {% if variantPrimary %}primary-class {% endif %}
        {% if variantLarge %}large-class {% endif %}
        {% if variantSecondary %}secondary-class {% endif %}
        """)
        
        rendered = template.render(Context(props_data))
        # Remove extra whitespace and normalize
        rendered = ' '.join(rendered.split())
        self.assertEqual(rendered, 'primary-class large-class')

    def test_multichoice_backward_compatibility(self):
        """Test that MultiChoice behaves similarly to legacy enums."""
        # This is conceptually how the legacy enum system worked:
        # variant="primary large" would set:
        # - variant = "primary large" 
        # - variantPrimary = True
        # - variantLarge = True
        
        @component('components/button.html')
        @dataclass  
        class ButtonProps:
            variant: MultiChoice['primary', 'secondary', 'large', 'small']

        result = validate_props(ButtonProps, {'variant': 'primary large'})
        
        # Check the main prop
        self.assertEqual(result['variant'], 'primary large')
        
        # Check the generated flags (like legacy enum behavior)
        self.assertEqual(result['variantPrimary'], True)
        self.assertEqual(result['variantLarge'], True)
        
        # Unselected values should not have flags (Django treats missing as False)
        self.assertNotIn('variantSecondary', result)
        self.assertNotIn('variantSmall', result)