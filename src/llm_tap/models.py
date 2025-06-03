# -*- coding: utf-8 -*-

"""
Defines the abstract models to describe Colored Petri Nets
"""

from dataclasses import dataclass, field


@dataclass
class ValueType:
    type: str


BOOL = ValueType("BOOL")
FLOAT = ValueType("FLOAT")
INT = ValueType("INT")
STR = ValueType("STR")

supported_types = (BOOL, FLOAT, INT, STR)


@dataclass
class TokenType:
    key: str
    type: ValueType = field(metadata={"choices": supported_types})


@dataclass
class TokenValue:
    type: TokenType
    value: str


@dataclass
class ConditionOperator:
    operator: str


AND = ConditionOperator("AND")
ANY = ConditionOperator("ANY")


@dataclass
class Operator:
    operator: str


BOOL_AND = Operator("and")
BOOL_OR = Operator("or")
EQUAL = Operator("==")
LT = Operator("<")
GT = Operator(">")
LTE = Operator("<=")
GTE = Operator(">=")

operators = (BOOL_AND, BOOL_OR, EQUAL, LT, GT, LTE, GTE)


@dataclass
class Place:
    name: str
    description: str
    token_type: TokenType


@dataclass
class InputArc:
    place: str
    transition: str
    token_key: str


@dataclass
class OutputArc:
    transition: str
    place: str
    output_token: TokenValue


@dataclass
class Condition:
    name: str
    input_arc: InputArc
    operator: Operator = field(metadata={"choices": operators})
    value: TokenValue


@dataclass
class ConditionSet:
    conditions: list[Condition]
    operator: ConditionOperator = field(metadata={"choices": (AND, ANY)})


@dataclass
class Guard:
    condition_sets: list[ConditionSet]


@dataclass
class Transition:
    name: str
    description: str
    inputs: list[InputArc]
    outputs: list[OutputArc]
    guard: Guard


@dataclass
class Workflow:
    name: str
    places: list[Place]
    transitions: list[Transition]
