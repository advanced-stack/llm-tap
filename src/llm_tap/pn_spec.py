# src/llm_tap/pn_spec.py
# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict, Union

# Section 4: Tokens
# Tokens are raw JSON-compatible data. We can use `Any` or a more specific type if known.
TokenValue = Any

# Section 2: Places
@dataclass
class SpecPlace:
    name: str
    description: Optional[str] = None
    capacity: Optional[int] = None

# Section 5: Guards
@dataclass
class SpecGuardCondition:
    type: str  # e.g., "token_match", "expression"
    # For "token_match"
    input_variable: Optional[str] = None
    attribute: Optional[str] = None
    operator: Optional[str] = None # e.g., "equals", "not_equals", "greater_than", "exists"
    value: TokenValue = None
    # For "expression" (future)
    dsl_string: Optional[str] = None

@dataclass
class SpecGuard:
    condition: SpecGuardCondition

# Section 6: Actions (Simplified as per spec, primary actions are via arcs)
# This class is a placeholder if more complex actions are defined later.
# For now, actions are mostly implicit in input/output arc definitions.
@dataclass
class SpecAction:
    type: str # e.g., "log_message", "external_call" (future considerations)
    # Specific fields for each action type would go here
    message: Optional[str] = None # For "log_message"
    service_url: Optional[str] = None # For "external_call"
    payload_from_input: Optional[str] = None # For "external_call"


# Section 3.1: Input Arc Object
@dataclass
class SpecInputArcConsumptionPolicy:
    type: str = "any"  # "match_value", "any"
    value_filter: Optional[Dict[str, Any]] = None # e.g., { "attribute": "status", "equals": "pending" }
    count: int = 1

@dataclass
class SpecInputArc:
    place: str
    consumption_policy: SpecInputArcConsumptionPolicy = field(default_factory=SpecInputArcConsumptionPolicy)
    variable_name: Optional[str] = None # Name to refer to matched token(s)

# Section 3.2: Output Arc Object
@dataclass
class SpecOutputArcModification:
    attribute: str
    set_value: TokenValue

@dataclass
class SpecOutputArcProductionDetails:
    value: Optional[TokenValue] = None
    copy_from_input: Optional[str] = None
    modifications: List[SpecOutputArcModification] = field(default_factory=list)
    count: int = 1

@dataclass
class SpecOutputArc:
    place: str
    production_details: SpecOutputArcProductionDetails

# Section 3: Transitions
@dataclass
class SpecTransition:
    name: str
    description: Optional[str] = None
    inputs: List[SpecInputArc] = field(default_factory=list)
    outputs: List[SpecOutputArc] = field(default_factory=list)
    guard: Optional[SpecGuard] = None
    # As per the spec, explicit 'actions' array is for future complex actions.
    # The primary consumption/production logic is in inputs/outputs.
    actions: List[SpecAction] = field(default_factory=list)


# Section 1: Overall Structure
# Using a type alias for initial marking for simplicity, as it's a dict.
SpecInitialMarking = Dict[str, List[TokenValue]]

@dataclass
class SpecPetriNet:
    name: str
    places: List[SpecPlace] = field(default_factory=list)
    transitions: List[SpecTransition] = field(default_factory=list)
    initial_marking: Optional[SpecInitialMarking] = None

    def to_json_dict(self) -> Dict[str, Any]:
        """Converts the SpecPetriNet to a dictionary suitable for JSON serialization."""
        # dataclasses.asdict works well but we might need custom handling
        # if we have non-standard types or want to exclude Nones more granularly.
        # For now, a basic conversion will do.

        def dict_factory(data):
            # Exclude fields with None values from the output dictionary
            return {k: v for k, v in data if v is not None}

        import dataclasses
        return dataclasses.asdict(self, dict_factory=dict_factory)
