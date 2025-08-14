"""
Tests for Django-specific prop types (ModelInstance and QuerySet).
"""

import pytest
from dataclasses import dataclass
from django.template import TemplateSyntaxError
from django.conf import settings

from includecontents.prop_types import ModelInstance, QuerySet
from includecontents.props import validate_props, parse_type_spec


# Only run these tests if auth is installed
pytestmark = pytest.mark.skipif(
    'django.contrib.auth' not in settings.INSTALLED_APPS,
    reason="auth app not installed"
)


class TestModelInstanceType:
    """Test ModelInstance prop type."""
    
    @pytest.mark.django_db
    def test_model_instance_validation(self):
        """Test that ModelInstance validates model instances."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='testuser')
        
        @dataclass
        class UserProps:
            user: ModelInstance('auth.User')
        
        # Valid user instance
        result = validate_props(UserProps, {'user': user})
        assert result['user'] == user
        
        # Invalid type
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(UserProps, {'user': 'not a user'})
        assert 'Expected instance of' in str(exc_info.value)
    
    @pytest.mark.django_db
    def test_model_instance_with_class(self):
        """Test ModelInstance with direct model class."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='testuser2')
        
        @dataclass
        class UserProps:
            user: ModelInstance(User)
        
        # Valid user instance
        result = validate_props(UserProps, {'user': user})
        assert result['user'] == user
    
    def test_model_instance_none_allowed(self):
        """Test that None is allowed for optional ModelInstance."""
        from typing import Optional
        
        @dataclass
        class OptionalUserProps:
            user: Optional[ModelInstance('auth.User')] = None
        
        # None should be valid
        result = validate_props(OptionalUserProps, {})
        assert result['user'] is None


class TestQuerySetType:
    """Test QuerySet prop type."""
    
    @pytest.mark.django_db
    def test_queryset_validation(self):
        """Test that QuerySet validates Django QuerySets."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        User.objects.create_user(username='user1')
        User.objects.create_user(username='user2')
        users_qs = User.objects.all()
        
        @dataclass
        class UsersProps:
            users: QuerySet()
        
        # Valid QuerySet
        result = validate_props(UsersProps, {'users': users_qs})
        assert result['users'] == users_qs
        
        # Invalid type (not a QuerySet)
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(UsersProps, {'users': [1, 2, 3]})
        assert 'Expected QuerySet' in str(exc_info.value)
    
    @pytest.mark.django_db
    def test_queryset_with_model(self):
        """Test QuerySet with specific model validation."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users_qs = User.objects.all()
        
        @dataclass
        class UserQueryProps:
            users: QuerySet('auth.User')
        
        # Valid QuerySet of correct model
        result = validate_props(UserQueryProps, {'users': users_qs})
        assert result['users'] == users_qs
        
        # Test with wrong model would require another model to test against
        # For now, just ensure the validator is created correctly
        validator = QuerySet('auth.User')
        assert hasattr(validator, '__metadata__')


class TestParseTypeSpecForDjango:
    """Test parsing Django-specific type specifications."""
    
    def test_parse_model_type(self):
        """Test parsing model type spec."""
        # Simple model type
        model_type = parse_type_spec('model(auth.User)')
        assert hasattr(model_type, '__metadata__')
        
        # Model type without parens should use base ModelInstance
        model_type = parse_type_spec('model')
        assert model_type == ModelInstance
    
    def test_parse_queryset_type(self):
        """Test parsing queryset type spec."""
        # QuerySet with model
        qs_type = parse_type_spec('queryset(blog.Article)')
        assert hasattr(qs_type, '__metadata__')
        
        # QuerySet without model
        qs_type = parse_type_spec('queryset()')
        assert hasattr(qs_type, '__metadata__')
        
        # QuerySet without parens
        qs_type = parse_type_spec('queryset')
        assert qs_type == QuerySet


class TestDjangoPropsIntegration:
    """Integration tests for Django-specific props."""
    
    @pytest.mark.django_db
    def test_complex_django_props(self):
        """Test a complex props class with Django types."""
        from django.db.models import Q
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Create test data
        admin_user = User.objects.create_user(
            username='admin',
            is_staff=True
        )
        regular_user = User.objects.create_user(username='regular')
        
        @dataclass
        class AdminPanelProps:
            current_user: ModelInstance(User)
            users_to_manage: QuerySet(User)
            is_superuser: bool = False
            
            def clean(self):
                """Ensure only staff can manage users."""
                if not self.current_user.is_staff and self.users_to_manage.exists():
                    from django.core.exceptions import ValidationError
                    raise ValidationError("Only staff can manage users")
        
        # Valid case - staff user
        result = validate_props(AdminPanelProps, {
            'current_user': admin_user,
            'users_to_manage': User.objects.filter(is_staff=False),
        })
        assert result['current_user'] == admin_user
        
        # Invalid case - non-staff trying to manage users
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(AdminPanelProps, {
                'current_user': regular_user,
                'users_to_manage': User.objects.all(),
            })
        assert 'Only staff can manage users' in str(exc_info.value)