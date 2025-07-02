import pytest
from django.template import Context
from includecontents.django import DjangoTemplates


def test_nested_content_blocks_with_same_name():
    """Test that nested components can use content blocks with the same name without conflict."""
    
    engine = DjangoTemplates({
        'NAME': 'test',
        'DIRS': ["tests/templates/"],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [],
        }
    })
    
    # Create nested components that both use 'info' content blocks
    template = engine.from_string("""
<include:container>
    <h2>Container Title</h2>
    <include:item>
        <content:info>First info block</content:info>
    </include:item>
    <include:item>
        <content:info>Second info block</content:info>
    </include:item>
</include:container>
""")
    
    context = {}
    # This should not raise a "Duplicate name for 'contents' tag: 'info'" error
    result = template.render(context)
    
    # Verify both info blocks are rendered correctly
    assert "First info block" in result
    assert "Second info block" in result