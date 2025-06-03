# -*- coding: utf-8 -*-

"""
Defines the abstract models to describe Colored Petri Nets
"""

from dataclasses import dataclass, field


_place_registry = {}


def register_place(place):
    _place_registry[place.name] = place


def get_places():
    return tuple(_place_registry.values())


_token_type_registry = {}


def register_token_type(token_type):
    _token_type_registry[token_type.name] = token_type


def get_token_names():
    return tuple(_token_type_registry.keys())


supported_types = (
    "BOOL",
    "FLOAT",
    "INT",
    "STR",
)

conditions_op = (
    "AND",
    "OR",
)

place_types = (
    "source",
    "sink",
)

supported_operands = (
    "AND",
    "OR",
    "EQUAL",
    "LESS THAN",
    "GREATER THAN",
    "LESS THAN OR EQUAL",
    "GREATER THAN OR EQUAL",
)


@dataclass(frozen=True)
class TokenType:
    name: str
    type: str = field(metadata={"choices": supported_types})


@dataclass(frozen=True)
class TokenValue:
    type: TokenType
    value: str


@dataclass(frozen=True)
class Place:
    name: str
    description: str
    type: str = field(metadata={"choices": place_types})
    token_type: TokenType


@dataclass(frozen=True)
class InputArc:
    place: Place = field(metadata={"choices": get_places})
    token_name: str = field(metadata={"choices": get_token_names})
    transition: str


@dataclass(frozen=True)
class OutputArc:
    place: Place = field(metadata={"choices": get_places})
    produce_token: TokenValue
    transition: str


@dataclass(frozen=True)
class Condition:
    operator: str = field(metadata={"choices": supported_operands})
    value: TokenValue


@dataclass(frozen=True)
class Guard:
    name: str
    conditions: list[Condition]
    conditions_operator: str = field(metadata={"choices": conditions_op})


@dataclass(frozen=True)
class Transition:
    name: str
    state_change: str
    inputs: list[InputArc]
    outputs: list[OutputArc]
    guard: list[Guard]


@dataclass(frozen=True)
class Workflow:
    name: str
    query: str
    transitions: list[Transition]


instructions = """Task: Convert a plain-language description of
a real-life workflow into a concise Colored Petri Net (CPN)
specification.

# Understand the Input

1. Expect free-form text describing:

- Events / activities (e.g., "validate order", "send email")
- Data items / conditions (e.g., sensor, status flags)
- Rules / constraints (e.g., "if value < 12 and opened then …")

2. Ignore irrelevant narrative; focus only on facts that influence
control or data flow.


# Extract Core Elements

For every fact you identify, assign one—and only one—of the following roles:

- Role: Recognition cue in text
- Token & Value: A piece of data that changes or is queried.
- Place: A persistent state, buffer, or resource.
- Transition: An action/event that changes state.
- Arc: The directional link between a place and a transition.
- Guard: A Boolean condition gating a transition.


# Color Sets (Token Types)

Every distinct data item is described as a token type with a descriptive
name and a type.

# Places

Places have a type:

- source: The place holds tokens
- sink: The place receive tokens and consume them immediately

A sink can only be connected to one single transition to avoid conflicts.

1. For each meaningful state or resource holder in the workflow, create a
place:

- place <Name> : <ColorSet>

2. Use the same color set in multiple places if the data values are identical
but the business meaning differs (e.g., PendingOrders vs. ApprovedOrders)


# Create Transitions

Transitions shall describe state changes: They consume tokens in input
places and produce tokens in output places.

1. One transition per business rule or external event.
2. Transitions create tokens in output places
3. As transitions describe state changes, they shall be named
using a mutation verb (i.e.: Change, Update, Adjust, Set, Toggle)
4. Use the following syntax template:


```
transition <Name as a state mutation>
    goal: <Objective description>
    change: <State changes description>
    --
    in:    <InputPlace1>[<Input token name1>],
    in:    <InputPlace2>[<Input token name2>]
    guard: <Boolean expression over name1, name2>
    out:   <OutputPlace>[Set <Output token name3> to <Value>]
end transition
```

# Attach Arcs and Guards

For each transition:

1. Input arcs: list every place whose tokens are required.
2. Output arcs: specify the tokens produced.
3. Guard: translate textual rules into Boolean expressions using the bound
variables (name1, name2).

# Output Format

Return a single, syntactically valid block combining:

1. Break down of the specifications
2. Color-set declarations
3. Place declarations
4. Guards definitions
5. Transition definitions (with arcs and guards)


# Validation Checklist (Before Responding)

- Every transition's input variables are defined in its input arcs.
- Guards reference only those variables.
- Each output token matches the color set of its target place.
- No place is left untyped.
- The model satisfies any mandatory constraints stated in the prompt.

End of instructions
"""
