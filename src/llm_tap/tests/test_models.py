import pytest
from llm_tap.models import (
    TokenType,
    Place,
    register_token_type,
    get_token_names,
    register_place,
    get_places,
    is_source,
    is_sink,
    places_str,
    _place_registry,  # For clearing state between tests
    _token_type_registry, # For clearing state between tests
    SOURCE,
    SINK,
)

# Helper function to clear registries for test isolation
def setup_function():
    _place_registry.clear()
    _token_type_registry.clear()

def teardown_function():
    _place_registry.clear()
    _token_type_registry.clear()

# --- Test Data ---
TT_INT = TokenType(name="MyInt", type="INT")
TT_BOOL = TokenType(name="MyBool", type="BOOL")
TT_FLOAT = TokenType(name="MyFloat", type="FLOAT")

PLACE_A_SRC = Place(name="PlaceA", description="Source A", type=SOURCE, token_type=TT_INT)
PLACE_B_SINK = Place(name="PlaceB", description="Sink B", type=SINK, token_type=TT_BOOL)
PLACE_C_SRC = Place(name="PlaceC", description="Source C", type=SOURCE, token_type=TT_FLOAT)
PLACE_D_SINK_INT = Place(name="PlaceD", description="Sink D", type=SINK, token_type=TT_INT)


# --- Tests for TokenType registration ---
def test_register_token_type():
    setup_function()
    register_token_type(PLACE_A_SRC, TT_INT)
    # Key is (place_name, token_type_name)
    assert ((PLACE_A_SRC.name, TT_INT.name) in _token_type_registry)
    assert _token_type_registry[(PLACE_A_SRC.name, TT_INT.name)] == TT_INT
    teardown_function()

def test_get_token_names_empty():
    setup_function()
    assert get_token_names() == ()
    teardown_function()

def test_get_token_names_single():
    setup_function()
    register_token_type(PLACE_A_SRC, TT_INT) # register_token_type is called by register_place implicitly
    # Manually register another one to be sure
    # register_token_type(PLACE_B_SINK, TT_BOOL) # This will be registered via PlaceB
    # Actually, get_token_names gets from _token_type_registry which is keyed by (place.name, place.token_type.name)
    # So we need to register places to populate it correctly for this test's intent
    register_place(PLACE_A_SRC)
    assert get_token_names() == (TT_INT.name,)
    teardown_function()

def test_get_token_names_multiple():
    setup_function()
    register_place(PLACE_A_SRC)
    register_place(PLACE_B_SINK)
    # Order might not be guaranteed, so check for presence and length
    names = get_token_names()
    assert len(names) == 2
    assert TT_INT.name in names
    assert TT_BOOL.name in names
    teardown_function()

def test_get_token_names_duplicates_through_places():
    setup_function()
    # Same token type, different places
    place_a_dup_token = Place(name="PlaceADup", description="Source ADup", type=SOURCE, token_type=TT_INT)
    register_place(PLACE_A_SRC)
    register_place(place_a_dup_token)
    names = get_token_names()
    # get_token_names extracts only the token type name from the (place_name, token_type_name) key
    # So if multiple places use the same token type, its name will appear multiple times if we don't unique it.
    # Current implementation of get_token_names: tuple(t[1] for t in _token_type_registry.keys())
    # This means it will list "MyInt" twice. This might be desired or not.
    # For now, testing current behavior.
    assert len(names) == 2
    assert names.count(TT_INT.name) == 2
    teardown_function()

# --- Tests for Place registration and retrieval ---
def test_register_place():
    setup_function()
    register_place(PLACE_A_SRC)
    key = (PLACE_A_SRC.name, PLACE_A_SRC.token_type.name)
    assert key in _place_registry
    assert _place_registry[key] == PLACE_A_SRC
    # Also check that token type was registered
    assert key in _token_type_registry
    assert _token_type_registry[key] == TT_INT
    teardown_function()

def test_get_places_empty():
    setup_function()
    assert get_places() == ()
    teardown_function()

def test_get_places_no_filters():
    setup_function()
    register_place(PLACE_A_SRC)
    register_place(PLACE_B_SINK)
    places = get_places()
    assert len(places) == 2
    assert PLACE_A_SRC in places
    assert PLACE_B_SINK in places
    teardown_function()

# --- Tests for Place filters ---
def test_is_source_filter():
    setup_function()
    register_place(PLACE_A_SRC)
    register_place(PLACE_B_SINK)
    source_places = get_places(is_source)
    assert len(source_places) == 1
    assert PLACE_A_SRC in source_places
    assert PLACE_B_SINK not in source_places
    teardown_function()

def test_is_sink_filter():
    setup_function()
    register_place(PLACE_A_SRC)
    register_place(PLACE_B_SINK)
    sink_places = get_places(is_sink)
    assert len(sink_places) == 1
    assert PLACE_B_SINK in sink_places
    assert PLACE_A_SRC not in sink_places
    teardown_function()

def test_get_places_multiple_filters():
    setup_function()
    register_place(PLACE_A_SRC) # Source, TT_INT
    register_place(PLACE_B_SINK) # Sink, TT_BOOL
    register_place(PLACE_C_SRC)  # Source, TT_FLOAT
    register_place(PLACE_D_SINK_INT) # Sink, TT_INT

    # Filter for source places using TT_INT
    def is_int_token(place):
        return place.token_type.name == TT_INT.name

    filtered = get_places(is_source, is_int_token)
    assert len(filtered) == 1
    assert PLACE_A_SRC in filtered
    teardown_function()

def test_get_places_no_match_filters():
    setup_function()
    register_place(PLACE_A_SRC) # Source, TT_INT
    def is_bool_token(place):
        return place.token_type.name == TT_BOOL.name
    filtered = get_places(is_sink, is_bool_token) # No sink with bool token registered
    assert len(filtered) == 0
    teardown_function()

# --- Test for places_str ---
def test_places_str_no_filters():
    setup_function()
    register_place(PLACE_A_SRC)
    register_place(PLACE_B_SINK)
    strs = places_str()
    assert len(strs) == 2
    assert str(PLACE_A_SRC) in strs
    assert str(PLACE_B_SINK) in strs
    teardown_function()

def test_places_str_with_filter():
    setup_function()
    register_place(PLACE_A_SRC)
    register_place(PLACE_B_SINK)
    strs = places_str(is_source)
    assert len(strs) == 1
    assert str(PLACE_A_SRC) in strs
    assert str(PLACE_B_SINK) not in strs
    teardown_function()

# It's good practice to have a requirements.txt for tests if pytest or other deps are needed
# For now, assuming pytest is available in the environment.
# If not, the subtask should include `pip install pytest`.
# For this task, we'll assume it's handled by the overall environment.
