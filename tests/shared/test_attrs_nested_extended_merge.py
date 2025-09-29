"""Test for nested extended attributes merging in __call__ method."""

from includecontents.shared.attrs import BaseAttrs


class TestAttrs(BaseAttrs):
    """Concrete test implementation of BaseAttrs."""

    __test__ = False

    pass


class TestNestedExtendedAttrsMerging:
    """Test that nested extended attributes are properly preserved during __call__ merging."""

    def test_nested_extended_attrs_preserved_with_fallbacks(self):
        """Test that title.class:text-red is preserved when fallbacks contain class attributes."""
        # Create attrs with nested extended attribute
        attrs = TestAttrs()
        attrs["title.class:text-red"] = True

        # Verify the nested structure is created correctly
        assert "title" in attrs._nested_attrs
        assert attrs._nested_attrs["title"]._conditional_modifiers == {
            "class": {"text-red": True}
        }
        assert str(attrs.title) == 'class="text-red"'

        # Apply fallbacks that contain class-related attributes (like {% attrs class="card" class:lg=True %})
        result = attrs(**{"class": "card", "class:lg": True})

        # The nested extended attributes should be preserved
        assert "title" in result._nested_attrs
        assert result._nested_attrs["title"]._conditional_modifiers == {
            "class": {"text-red": True}
        }
        assert str(result.title) == 'class="text-red"'

        # The fallbacks should also be applied at root level
        assert "card" in str(result)  # from class="card"
        assert "lg" in str(result)  # from class:lg=True

    def test_nested_extended_attrs_with_conflicting_fallbacks(self):
        """Test nested extended attrs are preserved even with conflicting fallback names."""
        attrs = TestAttrs()
        attrs["title.class:active"] = True
        attrs["title.data-id"] = "nested-value"

        # Apply fallbacks that have similar attribute names
        result = attrs(
            **{"class": "root-class", "class:hover": False, "data-id": "root-value"}
        )

        # Nested attributes should be preserved
        assert result._nested_attrs["title"]._conditional_modifiers == {
            "class": {"active": True}
        }
        assert result._nested_attrs["title"]["data-id"] == "nested-value"

        # Root attributes should get fallbacks
        assert result["class"] == "root-class"
        assert result["data-id"] == "root-value"
        assert result._conditional_modifiers == {"class": {"hover": False}}

    def test_multiple_nested_extended_attrs(self):
        """Test multiple nested attributes with extended properties."""
        attrs = TestAttrs()
        attrs["title.class:primary"] = True
        attrs["title.class:large"] = False
        attrs["button.class:disabled"] = True
        attrs["input.data-validate"] = "required"

        result = attrs(**{"class": "wrapper"})

        # All nested extended attrs should be preserved
        assert result._nested_attrs["title"]._conditional_modifiers == {
            "class": {"primary": True, "large": False}
        }
        assert result._nested_attrs["button"]._conditional_modifiers == {
            "class": {"disabled": True}
        }
        assert result._nested_attrs["input"]["data-validate"] == "required"

        # Root class should have fallback
        assert result["class"] == "wrapper"

    def test_empty_fallbacks_preserve_nested_extended(self):
        """Test that nested extended attrs are preserved even with no fallbacks."""
        attrs = TestAttrs()
        attrs["form.class:invalid"] = True

        result = attrs()  # No fallbacks

        assert result._nested_attrs["form"]._conditional_modifiers == {
            "class": {"invalid": True}
        }
        assert str(result.form) == 'class="invalid"'

    def test_fallbacks_only_no_nested_attrs(self):
        """Test that fallbacks work correctly when there are no nested attrs."""
        attrs = TestAttrs()

        result = attrs(**{"class": "simple", "class:active": True})

        assert result["class"] == "simple"
        assert result._conditional_modifiers == {"class": {"active": True}}
        assert len(result._nested_attrs) == 0
