# -*- coding: utf-8 -*-

"""
Defines the abstract models to describe Colored Petri Nets
"""

import uuid
from dataclasses import dataclass, field


SOURCE = "source"
SINK = "sink"

_place_id_registry = {}
_place_id_to_place = {}
_place_registry = {}
_token_type_registry = {}


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


@dataclass(frozen=True)
class InputArc:
    place: str = field(
        metadata={"choices": lambda: places_with_ids(is_source)}
    )


@dataclass(frozen=True)
class OutputArc:
    place: str = field(metadata={"choices": lambda: places_with_ids(is_sink)})
    token_produced: TokenValue


@dataclass(frozen=True)
class Condition:
    place_id: str = field(metadata={"choices": lambda: places_ids(is_source)})
    operator: str = field(metadata={"choices": supported_operands})
    value: TokenValue


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

    def print(self):
        def place_details(place_id):
            place = _place_id_to_place[place_id]
            return str(place)

        def condition_details(condition):
            place_desc = place_details(condition.place_id)
            return (
                f"{place_desc} ({condition.operator} {condition.value.value})"
            )

        transition = self.transition
        guard = transition.guard
        output = transition.output

        print("Workflow Details:")
        print("Transition:")
        print("  Guard:")
        print(f"    Conditions: ({guard.conditions_operator})")
        for condition in guard.conditions:
            print(f"      - {condition_details(condition)}")
        print("  Output:")
        print(f"    Place: {output.place}")
        print(
            f"    Token Produced: {output.token_produced.value} [{output.token_produced.type.type}]"
        )
