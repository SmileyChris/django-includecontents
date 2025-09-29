"""Test that object attributes are passed as objects, not strings."""

from django.template import Context

from includecontents.django.base import Template


class MockDeck:
    """Mock deck object for testing."""

    def __init__(self, name, cards):
        self.name = name
        self.cards = cards

    def __str__(self):
        return f"Deck: {self.name}"

    def card_count(self):
        return len(self.cards)


def test_object_passed_as_attribute():
    """Test that deck="{{ deck }}" passes the actual object."""
    template = Template('<include:test-object-deck deck="{{ deck }}" />')

    deck = MockDeck("Standard", ["Ace", "King", "Queen", "Jack"])
    result = template.render(Context({"deck": deck}))

    assert "Standard" in result
    assert "Cards: 4" in result
    assert "Ace" in result
    assert "King" in result
    assert "Queen" in result
    assert "Jack" in result
    # Should NOT contain the string representation
    assert "Deck: Standard" not in result


def test_object_with_filters():
    """Test that objects work with filters like deck="{{ deck|default:empty_deck }}"."""
    template = Template(
        '<include:test-object-deck-filter deck="{{ deck|default:empty_deck }}" />'
    )

    empty_deck = MockDeck("Empty", [])

    # Test with None - should use default
    result = template.render(Context({"deck": None, "empty_deck": empty_deck}))
    assert "Empty has 0 cards" in result

    # Test with actual deck - should use it
    real_deck = MockDeck("Full", ["A", "B", "C"])
    result = template.render(Context({"deck": real_deck, "empty_deck": empty_deck}))
    assert "Full has 3 cards" in result


def test_mixed_content_still_renders_as_string():
    """Test that mixed content like 'Deck: {{ deck }}' still renders as string."""
    template = Template('<include:test-object-text text="Deck: {{ deck }}" />')

    deck = MockDeck("My Deck", ["Card1", "Card2"])
    result = template.render(Context({"deck": deck}))

    # Mixed content should render the object as string
    assert "Deck: My Deck" in result


def test_multiple_objects_in_attributes():
    """Test passing multiple objects as separate attributes."""
    template = Template(
        '<include:test-object-game player1_deck="{{ p1_deck }}" player2_deck="{{ p2_deck }}" />'
    )

    p1_deck = MockDeck("Red Deck", ["R1", "R2", "R3"])
    p2_deck = MockDeck("Blue Deck", ["B1", "B2"])

    result = template.render(Context({"p1_deck": p1_deck, "p2_deck": p2_deck}))

    assert "Player 1: Red Deck" in result
    assert "Cards: 3" in result
    assert "Player 2: Blue Deck" in result
    assert "Cards: 2" in result


def test_object_in_attrs_collection():
    """Test that objects passed to undefined attributes work correctly."""
    # First test - component with props defined but empty
    template = Template('<include:test-object-flexible data-deck="{{ deck }}" />')

    deck = MockDeck("Test Deck", ["A", "B"])
    result = template.render(Context({"deck": deck}))

    # The object should be available in attrs and accessible as an object
    assert "Has deck: Test Deck" in result
    # When rendered as HTML attributes, objects are converted to strings - this is expected
    assert 'data-deck="Deck: Test Deck"' in result
