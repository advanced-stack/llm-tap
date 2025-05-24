# -*- coding: utf-8 -*-
from enum import Enum
from dataclasses import dataclass


@dataclass
class Trigger:
    description: str


@dataclass
class Condition:
    description: str


@dataclass
class ConditionSet:
    class Operator(Enum):
        AND = "AND"
        OR = "OR"

    conditions: list[Condition]
    operator: Operator


@dataclass
class Action:
    description: str


@dataclass
class Branch:
    conditions_value: bool
    actions: list[Action]


@dataclass
class Rule:
    name: str
    condition_sets: list[ConditionSet]
    branches: list[Branch]


@dataclass
class Workflow:
    name: str
    description: str
    triggers: list[Trigger]
    rules: list[Rule]
