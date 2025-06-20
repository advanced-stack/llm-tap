import pytest
from dataclasses import dataclass, field, MISSING
from enum import Enum, StrEnum
import typing

from llm_tap.llm import (
    to_json_schema,
    from_dict,
    serialize,
    convert_field,  # For more direct tests if needed
    class_names_mapping, # For clearing state
)

# Helper function to clear registries for test isolation
def setup_function():
    class_names_mapping.clear()

def teardown_function():
    class_names_mapping.clear()

# --- Test Data ---

class SimpleEnum(Enum):
    A = "Value A"
    B = "Value B"

class SimpleStrEnum(StrEnum):
    X = "Value X"
    Y = "Value Y"

@dataclass(frozen=True)
class SimpleItem:
    '''A simple item for testing.'''
    id: int
    name: str

@dataclass
class NestedData:
    '''More complex nested data.'''
    item: SimpleItem
    count: int
    is_active: bool = True
    tags: list[str] = field(default_factory=list)
    maybe_num: typing.Optional[float] = None

@dataclass
class ChoiceA:
    '''First choice for a union type.'''
    value_a: str

@dataclass
class ChoiceB:
    '''Second choice for a union type.'''
    value_b: int

@dataclass
class UnionContainer:
    '''Contains a union of ChoiceA or ChoiceB.'''
    choice_field: typing.Union[ChoiceA, ChoiceB]

@dataclass
class EnumContainer:
    '''Contains an enum field.'''
    my_enum: SimpleEnum
    my_str_enum: SimpleStrEnum


# --- Tests for to_json_schema ---

def test_to_json_schema_simple_item():
    setup_function()
    schema = to_json_schema(SimpleItem)
    assert schema["type"] == "object"
    assert schema["title"] == "SimpleItem"
    assert schema["description"] == "A simple item for testing."
    assert "id" in schema["properties"]
    assert schema["properties"]["id"]["type"] == "integer"
    assert "name" in schema["properties"]
    assert schema["properties"]["name"]["type"] == "string"
    assert schema["required"] == ["id", "name"]
    teardown_function()

def test_to_json_schema_nested_data():
    setup_function()
    schema = to_json_schema(NestedData)
    assert schema["title"] == "NestedData"
    assert "item" in schema["properties"]
    assert schema["properties"]["item"]["title"] == "SimpleItem" # Check for nested schema
    assert "count" in schema["properties"]
    assert schema["properties"]["count"]["type"] == "integer"
    assert "is_active" in schema["properties"]
    assert schema["properties"]["is_active"]["type"] == "boolean"
    assert "tags" in schema["properties"]
    assert schema["properties"]["tags"]["type"] == "array"
    assert schema["properties"]["tags"]["items"]["type"] == "string"
    assert "maybe_num" in schema["properties"]
    # Optional[float] becomes anyOf [number, null type] or similar in JSON schema terms,
    # or it might just be number and not required.
    # The current implementation seems to make it "number" but not required.
    assert schema["properties"]["maybe_num"]["type"] == "number"
    assert "maybe_num" not in schema["required"] # Because it has a default (None)
    assert sorted(schema["required"]) == sorted(["item", "count"]) # is_active has default
    teardown_function()

def test_to_json_schema_with_enum():
    setup_function()
    schema = to_json_schema(EnumContainer)
    assert "my_enum" in schema["properties"]
    assert schema["properties"]["my_enum"]["type"] == "string"
    assert sorted(schema["properties"]["my_enum"]["enum"]) == sorted(["A", "B"])
    assert "my_str_enum" in schema["properties"]
    assert schema["properties"]["my_str_enum"]["type"] == "string"
    assert sorted(schema["properties"]["my_str_enum"]["enum"]) == sorted(["X", "Y"])
    teardown_function()

def test_to_json_schema_union_type():
    setup_function()
    schema = to_json_schema(UnionContainer)
    assert "choice_field" in schema["properties"]
    choice_props = schema["properties"]["choice_field"]
    assert "anyOf" in choice_props
    assert len(choice_props["anyOf"]) == 2

    # Check for the generated Choice dataclasses (ChoiceChoiceA, ChoiceChoiceB)
    choice_a_schema = next(s for s in choice_props["anyOf"] if s["properties"]["name"]["enum"] == ["ChoiceA"])
    choice_b_schema = next(s for s in choice_props["anyOf"] if s["properties"]["name"]["enum"] == ["ChoiceB"])

    assert choice_a_schema["properties"]["arguments"]["title"] == "ChoiceA"
    assert choice_b_schema["properties"]["arguments"]["title"] == "ChoiceB"
    teardown_function()


# --- Tests for from_dict ---

def test_from_dict_simple_item():
    setup_function()
    to_json_schema(SimpleItem) # Populate class_names_mapping
    data = {"id": 1, "name": "Test"}
    instance = from_dict(SimpleItem, data)
    assert isinstance(instance, SimpleItem)
    assert instance.id == 1
    assert instance.name == "Test"
    teardown_function()

def test_from_dict_nested_data():
    setup_function()
    to_json_schema(NestedData) # Populates mappings for NestedData and SimpleItem
    to_json_schema(SimpleItem)
    data = {
        "item": {"id": 10, "name": "SubItem"},
        "count": 5,
        "is_active": False,
        "tags": ["tag1", "tag2"],
        "maybe_num": 3.14
    }
    instance = from_dict(NestedData, data)
    assert isinstance(instance, NestedData)
    assert isinstance(instance.item, SimpleItem)
    assert instance.item.id == 10
    assert instance.item.name == "SubItem"
    assert instance.count == 5
    assert instance.is_active is False
    assert instance.tags == ["tag1", "tag2"]
    assert instance.maybe_num == 3.14
    teardown_function()

def test_from_dict_nested_data_with_defaults():
    setup_function()
    to_json_schema(NestedData)
    to_json_schema(SimpleItem)
    data = {
        "item": {"id": 10, "name": "SubItem"},
        "count": 5,
        # is_active, tags, maybe_num use defaults
    }
    instance = from_dict(NestedData, data)
    assert isinstance(instance, NestedData)
    assert instance.is_active is True # Default
    assert instance.tags == []       # Default factory
    assert instance.maybe_num is None # Default
    teardown_function()

def test_from_dict_with_enum():
    setup_function()
    to_json_schema(EnumContainer) # Populates mapping
    to_json_schema(SimpleEnum) # Not directly used by from_dict but good for consistency
    to_json_schema(SimpleStrEnum)

    data = {"my_enum": "A", "my_str_enum": "X"}
    instance = from_dict(EnumContainer, data)
    assert isinstance(instance, EnumContainer)
    assert instance.my_enum == SimpleEnum.A
    assert instance.my_str_enum == SimpleStrEnum.X
    teardown_function()

def test_from_dict_union_type_choice_a():
    setup_function()
    to_json_schema(UnionContainer) # Populates mappings
    to_json_schema(ChoiceA)
    to_json_schema(ChoiceB)

    # This structure matches how the Union is represented after to_json_schema
    # which involves wrapper dataclasses like "ChoiceChoiceA"
    data = {"choice_field": {"name": "ChoiceA", "arguments": {"value_a": "hello"}}}
    instance = from_dict(UnionContainer, data)
    assert isinstance(instance, UnionContainer)
    assert isinstance(instance.choice_field, ChoiceA)
    assert instance.choice_field.value_a == "hello"
    teardown_function()

def test_from_dict_union_type_choice_b():
    setup_function()
    to_json_schema(UnionContainer)
    to_json_schema(ChoiceA)
    to_json_schema(ChoiceB)
    data = {"choice_field": {"name": "ChoiceB", "arguments": {"value_b": 123}}}
    instance = from_dict(UnionContainer, data)
    assert isinstance(instance, UnionContainer)
    assert isinstance(instance.choice_field, ChoiceB)
    assert instance.choice_field.value_b == 123
    teardown_function()

# --- Tests for serialize ---

def test_serialize_simple_types():
    assert serialize(10) == 10
    assert serialize("test") == "test"
    assert serialize(True) is True
    assert serialize(3.14) == 3.14

def test_serialize_enum():
    assert serialize(SimpleEnum.A) == "Value A"
    assert serialize(SimpleStrEnum.X) == "Value X"

def test_serialize_list_of_simple():
    assert serialize([1, "a", True]) == [1, "a", True]

def test_serialize_list_of_enums():
    assert serialize([SimpleEnum.A, SimpleEnum.B]) == ["Value A", "Value B"]

def test_serialize_dict_simple():
    assert serialize({"a": 1, "b": "two"}) == {"a": 1, "b": "two"}

def test_serialize_dataclass():
    setup_function()
    item = SimpleItem(id=1, name="Test")
    expected = {"id": 1, "name": "Test"}
    assert serialize(item) == expected
    teardown_function()

def test_serialize_nested_dataclass():
    setup_function()
    nested = NestedData(item=SimpleItem(id=2, name="Sub"), count=3)
    # Defaults will be included because asdict() is used
    expected = {
        "item": {"id": 2, "name": "Sub"},
        "count": 3,
        "is_active": True,
        "tags": [],
        "maybe_num": None
    }
    assert serialize(nested) == expected
    teardown_function()

def test_serialize_list_of_dataclasses():
    setup_function()
    items = [SimpleItem(id=1, name="A"), SimpleItem(id=2, name="B")]
    expected = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
    assert serialize(items) == expected
    teardown_function()

# Placeholder for potential direct convert_field tests if complex scenarios arise
# that are not well-covered by to_json_schema tests.
# For now, convert_field is implicitly tested via to_json_schema.

# Ensure pytest is available or add `pip install pytest` to setup.
