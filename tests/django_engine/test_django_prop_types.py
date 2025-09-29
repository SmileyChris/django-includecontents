"""
Tests for Django-specific prop types (ModelInstance and QuerySet).
"""

import pytest
from dataclasses import dataclass
from django.template import TemplateSyntaxError
from django.conf import settings

from includecontents.django.prop_types import Model, QuerySet, User
from includecontents.shared.validation import validate_props
from includecontents.shared.template_parser import parse_type_spec


# Only run these tests if auth is installed
pytestmark = pytest.mark.skipif(
    'django.contrib.auth' not in settings.INSTALLED_APPS,
    reason="auth app not installed"
)


class TestModelType:
    """Test Model prop type."""
    
    @pytest.mark.django_db
    def test_model_validation(self):
        """Test that Model validates model instances."""
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        user = UserModel.objects.create_user(username='testuser')
        
        @dataclass
        class UserProps:
            user: Model['auth.User']
        
        # Valid user instance
        result = validate_props(UserProps, {'user': user})
        assert result['user'] == user
        
        # Invalid type
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(UserProps, {'user': 'not a user'})
        assert 'Expected instance of' in str(exc_info.value)
    
    @pytest.mark.django_db
    def test_model_with_class(self):
        """Test Model with direct model class."""
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        user = UserModel.objects.create_user(username='testuser2')
        
        @dataclass
        class UserProps:
            user: Model[UserModel]
        
        # Valid user instance
        result = validate_props(UserProps, {'user': user})
        assert result['user'] == user
    
    def test_model_none_allowed(self):
        """Test that None is allowed for optional Model."""
        from typing import Optional
        
        @dataclass
        class OptionalUserProps:
            user: Optional[Model['auth.User']] = None
        
        # None should be valid
        result = validate_props(OptionalUserProps, {})
        assert result['user'] is None
    
    @pytest.mark.django_db
    def test_bare_model_type(self):
        """Test bare Model type for any Django model."""
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        user = UserModel.objects.create_user(username='testuser3')
        
        @dataclass
        class AnyModelProps:
            item: Model  # Any Django model (no parentheses needed)
        
        # Valid model instance
        result = validate_props(AnyModelProps, {'item': user})
        assert result['item'] == user
    
    @pytest.mark.django_db  
    def test_model_with_contenttype(self):
        """Test Model type with ContentType (non-User model)."""
        from django.contrib.contenttypes.models import ContentType
        
        # Get or create a ContentType instance
        ct = ContentType.objects.get_for_model(ContentType)
        
        @dataclass
        class ContentTypeProps:
            content: Model['contenttypes.ContentType']
        
        # Valid ContentType instance
        result = validate_props(ContentTypeProps, {'content': ct})
        assert result['content'] == ct
        
        # Test with Model class directly
        @dataclass
        class ContentTypeProps2:
            content: Model[ContentType]
        
        result = validate_props(ContentTypeProps2, {'content': ct})
        assert result['content'] == ct
        
        # Invalid type should fail
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(ContentTypeProps, {'content': 'not a model'})
        assert 'Expected instance of ContentType' in str(exc_info.value)


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
            users: QuerySet
        
        # Valid QuerySet
        result = validate_props(UsersProps, {'users': users_qs})
        assert result['users'] == users_qs
        
        # Invalid type (not a QuerySet)
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(UsersProps, {'users': [1, 2, 3]})
        assert 'Expected a QuerySet' in str(exc_info.value)
    
    @pytest.mark.django_db
    def test_queryset_with_model(self):
        """Test QuerySet with specific model validation."""
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        users_qs = UserModel.objects.all()
        
        @dataclass
        class UserQueryProps:
            users: QuerySet['auth.User']
        
        # Valid QuerySet of correct model
        result = validate_props(UserQueryProps, {'users': users_qs})
        assert result['users'] == users_qs
        
        # Test with wrong model would require another model to test against
        # For now, just ensure the validator is created correctly
        validator = QuerySet['auth.User']
        assert hasattr(validator, '__metadata__')
    
    @pytest.mark.django_db
    def test_queryset_with_contenttype(self):
        """Test QuerySet with ContentType model (non-User)."""
        from django.contrib.contenttypes.models import ContentType
        
        ct_qs = ContentType.objects.all()
        
        @dataclass
        class ContentTypeQueryProps:
            types: QuerySet['contenttypes.ContentType']
        
        # Valid QuerySet of ContentType
        result = validate_props(ContentTypeQueryProps, {'types': ct_qs})
        assert result['types'] == ct_qs
        
        # Test with class directly
        @dataclass
        class ContentTypeQueryProps2:
            types: QuerySet[ContentType]
        
        result = validate_props(ContentTypeQueryProps2, {'types': ct_qs})
        assert result['types'] == ct_qs
        
        # Wrong model QuerySet should fail
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        users_qs = UserModel.objects.all()
        
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(ContentTypeQueryProps, {'types': users_qs})
        assert 'Expected QuerySet of ContentType' in str(exc_info.value)


class TestParseTypeSpecForDjango:
    """Test parsing Django-specific type specifications."""
    
    def test_parse_model_type(self):
        """Test parsing model type spec."""
        # Model type with parameter
        model_type = parse_type_spec('model(auth.User)')
        assert hasattr(model_type, '__metadata__')
        
        # Model type without parens should use base Model
        model_type = parse_type_spec('model')
        # Should be an instance of Model()
        assert hasattr(model_type, '__metadata__')
    
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
        # Should be an instance of QuerySet()
        assert hasattr(qs_type, '__metadata__')
    
    def test_parse_user_type(self):
        """Test parsing user type spec."""
        # User type (special case)
        user_type = parse_type_spec('user')
        # Should be an instance of User()
        assert hasattr(user_type, '__metadata__')


class TestUserType:
    """Test the special User type."""
    
    @pytest.mark.django_db
    def test_user_type_validation(self):
        """Test that User type validates the project's user model."""
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        user = UserModel.objects.create_user(username='testuser')
        
        @dataclass
        class UserProps:
            current_user: User
        
        # Valid user instance
        result = validate_props(UserProps, {'current_user': user})
        assert result['current_user'] == user
        
        # Invalid type
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(UserProps, {'current_user': 'not a user'})
        assert 'Expected instance of' in str(exc_info.value)
    
    def test_user_type_optional(self):
        """Test optional User type."""
        from typing import Optional
        
        @dataclass
        class OptionalUserProps:
            user: Optional[User] = None
        
        # None should be valid
        result = validate_props(OptionalUserProps, {})
        assert result['user'] is None


class TestDjangoPropsIntegration:
    """Integration tests for Django-specific props."""
    
    @pytest.mark.django_db
    def test_complex_django_props(self):
        """Test a complex props class with Django types."""
        from django.db.models import Q
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        
        # Create test data
        admin_user = UserModel.objects.create_user(
            username='admin',
            is_staff=True
        )
        regular_user = UserModel.objects.create_user(username='regular')
        
        @dataclass
        class AdminPanelProps:
            current_user: Model[UserModel]
            users_to_manage: QuerySet[UserModel]
            is_superuser: bool = False
            
            def clean(self):
                """Ensure only staff can manage users."""
                if not self.current_user.is_staff and self.users_to_manage.exists():
                    from django.core.exceptions import ValidationError
                    raise ValidationError("Only staff can manage users")
        
        # Valid case - staff user
        result = validate_props(AdminPanelProps, {
            'current_user': admin_user,
            'users_to_manage': UserModel.objects.filter(is_staff=False),
        })
        assert result['current_user'] == admin_user
        
        # Invalid case - non-staff trying to manage users
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(AdminPanelProps, {
                'current_user': regular_user,
                'users_to_manage': UserModel.objects.all(),
            })
        assert 'Only staff can manage users' in str(exc_info.value)