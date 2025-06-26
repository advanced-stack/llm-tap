# -*- coding: utf-8 -*-

"""
Defines the abstract models to describe Colored Petri Nets
"""

import uuid
import keyword
from dataclasses import dataclass, make_dataclass, field


SOURCE = "source"
SINK = "sink"

_place_id_registry = {}
_place_id_to_place = {}
_place_registry = {}
_token_type_registry = {}


def make_valid_identifier(s):
    # Replace invalid characters with underscores
    valid_identifier = "".join(char if char.isalnum() else "_" for char in s)

    # Ensure the identifier doesn't start with a digit
    if valid_identifier[0].isdigit():
        valid_identifier = "_" + valid_identifier

    # Check if the identifier is a Python keyword
    if keyword.iskeyword(valid_identifier):
        valid_identifier = valid_identifier + "_"

    return valid_identifier


def clear():
    _place_registry.clear()
    _token_type_registry.clear()
    _place_id_registry.clear()
    _place_id_to_place.clear()


def register_token_type(place, token_type):
    key = (place.name, place.token_type.name)
    _token_type_registry[key] = token_type


def get_token_names():
    return tuple(t[1] for t in _token_type_registry.keys())


def register_place(place):
    key = (place.name, place.token_type.name)

    if key not in _place_id_registry:
        _place_id_registry[key] = uuid.uuid4().hex[:4]
        _place_id_to_place[f"id:{_place_id_registry[key]}"] = place

    register_token_type(place, place.token_type)

    _place_registry[key] = place


def get_place_id(place):
    key = (place.name, place.token_type.name)
    return _place_id_registry.get(key, "unregistered")


def get_places(*filters):
    places = tuple(_place_registry.values())
    if not filters:
        return places
    filtered_places = filter(lambda p: all(f(p) for f in filters), places)
    filtered_places = list(filtered_places)
    return set(filtered_places)


def is_source(place):
    return place.type == SOURCE


def is_sink(place):
    return place.type == SINK


def places_str(*filters):
    return list(map(str, get_places(*filters)))


def places_with_ids(*filters):
    return [
        f"id:{get_place_id(place)} {place}" for place in get_places(*filters)
    ]


def places_ids(*filters):
    return [f"id:{get_place_id(place)}" for place in get_places(*filters)]


def tokens_for_places(*filters):
    places = get_places(*filters)
    for p in places:
        pass


supported_types = (
    "BOOL",
    "FLOAT",
    "INT",
    "STR",
)

token_types = (
    "DISCRETE",
    "STRING",
    "NUMERIC",
)

conditions_op = (
    "AND",
    "OR",
)

place_types = (
    SOURCE,
    SINK,
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
class ITokenValue:
    value: str


@dataclass(frozen=True)
class IPlaceState:
    place: str
    operator: str = field(metadata={"choices": supported_operands})
    value: ITokenValue


@dataclass(frozen=True)
class IPlaceChangeState:
    set_value: str
    to: ITokenValue


@dataclass(frozen=True)
class TokenType:
    name: str
    type: str = field(metadata={"choices": token_types})
    range: list = field(default_factory=list)
    sub_type: type = None

    def build_discrete_type(self):
        available_values = tuple(self.range)
        field_name = "value"
        field_type = type(available_values[0])
        field_default = field(metadata={"choices": available_values})

        cls = make_dataclass(
            self.name,
            [
                (field_name, field_type, field_default),
            ],
        )
        return cls

    def build_string_type(self):
        field_name = "value"
        field_type = str

        cls = make_dataclass(
            self.name,
            [
                (field_name, field_type),
            ],
        )
        return cls

    def build_numeric_type(self):
        doc_string = ""

        if self.range:
            min_value, max_value = self.range
            doc_string = f"range [{min_value}, {max_value}]"

        field_name = "value"
        field_type = self.sub_type

        cls = make_dataclass(
            make_valid_identifier(self.name),
            [
                (field_name, field_type),
            ],
        )
        if doc_string:
            cls.__doc__ = doc_string
        return cls

    def build_value_type(self):
        if self.type == "DISCRETE":
            return self.build_discrete_type()

        if self.type == "STRING":
            return self.build_string_type()

        if self.type == "NUMERIC":
            return self.build_numeric_type()


@dataclass(frozen=True)
class Place:
    name: str
    description: str
    type: str = field(metadata={"choices": place_types})
    token_type: TokenType

    def details(self):
        return "\n".join(
            (
                f"id:{get_place_id(self)}",
                str(self),
                self.description,
            )
        )

    def __str__(self):
        return f"{self.type}: {self.name} [{self.token_type.name}]"

    def build_place_state_type(self):
        PlaceState = make_dataclass(
            "PlaceState",
            [
                (
                    "place",
                    str,
                    field(
                        metadata={
                            "choices": [
                                f"{self.name} [{self.token_type.name}]"
                            ]
                        }
                    ),
                ),
                (
                    "operator",
                    str,
                    field(metadata={"choices": supported_operands}),
                ),
                ("value", self.token_type.build_value_type()),
            ],
        )
        return PlaceState

    def build_change_state_type(self):
        PlaceChangeState = make_dataclass(
            "PlaceChangeState",
            [
                (
                    "set_value",
                    str,
                    field(
                        metadata={
                            "choices": [
                                f"{self.name} [{self.token_type.name}]"
                            ]
                        }
                    ),
                ),
                ("to", self.token_type.build_value_type()),
            ],
        )
        return PlaceChangeState


@dataclass(frozen=True)
class InputArc:
    place: str = field(metadata={"choices": lambda: places_str(is_source)})


@dataclass(frozen=True)
class OutputArc:
    place: str = field(metadata={"choices": lambda: places_str(is_sink)})
    token_produced: IPlaceChangeState = field(
        metadata={
            "choices": lambda: [
                p.build_change_state_type() for p in get_places(is_sink)
            ]
        }
    )


@dataclass(frozen=True)
class Condition:
    """
    Condition are written < place > < operator > < value >
    """

    place_state: IPlaceState = field(
        metadata={
            "choices": lambda: [
                p.build_place_state_type() for p in get_places(is_source)
            ]
        }
    )


@dataclass(frozen=True)
class Guard:
    conditions: list[Condition]
    conditions_operator: str = field(metadata={"choices": conditions_op})


@dataclass(frozen=True)
class Transition:
    inputs: list[InputArc]
    guard: Guard
    output: OutputArc


@dataclass(frozen=True)
class Workflow:
    transition: Transition

    def __str__(self):
        transition = self.transition
        guard = transition.guard
        output = transition.output

        s = []

        s.append("Workflow Details:")
        s.append("Transition:")
        s.append("  Guard:")
        s.append(f"    Conditions: {guard.conditions_operator}")

        for c in guard.conditions:
            s.append(
                f"      - {c.place_state.place} "
                f"{c.place_state.operator} {c.place_state.value}"
            )

        s.append("  Output:")
        s.append(
            (
                f"    Set {output.token_produced.set_value}"
                f" to {output.token_produced.to.value}"
            )
        )

        return "\n".join(s)
