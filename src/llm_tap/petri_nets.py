# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Any, List, Dict, Callable, Optional, TypeVar, Generic

# Import new spec classes
from .pn_spec import (
    SpecPetriNet, SpecPlace, SpecTransition, SpecInputArc, SpecOutputArc,
    SpecInputArcConsumptionPolicy, SpecOutputArcProductionDetails,
    SpecGuard, SpecGuardCondition, TokenValue, SpecInitialMarking
)

# Color can be any Python data type. We can use a TypeVar for generics.
Color = TypeVar('Color')

@dataclass
class Token(Generic[Color]):
    """
    Represents a token with a specific value (its color).
    The 'color' is the actual data payload of the token.
    """
    value: Color

    def __hash__(self):
        # Attempt to hash based on value if possible, otherwise use id.
        # This is important if Tokens are stored in sets or dict keys directly.
        try:
            return hash((type(self.value), self.value))
        except TypeError:
            # If value is unhashable (e.g., a list), fall back to object id.
            # This means different Token objects with same unhashable value
            # will be treated as distinct, which is often desired.
            return id(self)

    def __eq__(self, other):
        if not isinstance(other, Token):
            return NotImplemented
        return self.value == other.value

@dataclass
class Place:
    """
    A container for tokens. Places can have a name for identification.
    It holds a list of Token objects.
    """
    name: str
    tokens: List[Token] = field(default_factory=list)
    # Removed: capacity, accepted token types/colors - these are now in SpecPlace if needed

    def add_token(self, token: Token):
        self.tokens.append(token)

    def remove_token(self, token: Token):
        try:
            self.tokens.remove(token)
        except ValueError:
            raise ValueError(f"Token {token} not found in place {self.name}")

    def has_token_of_value(self, value: Any) -> bool:
        """Checks if a token with the given value exists in the place."""
        return any(token.value == value for token in self.tokens)

    def get_tokens_by_value(self, value: Any) -> List[Token]:
        """Returns all tokens that have the specified value."""
        return [token for token in self.tokens if token.value == value]

    def get_tokens_by_type(self, token_type: type) -> List[Token]:
        """Returns all tokens whose value is an instance of token_type."""
        return [token for token in self.tokens if isinstance(token.value, token_type)]

    def to_spec_place(self) -> SpecPlace:
        # Description and capacity can be added here if Place objects store them
        return SpecPlace(name=self.name)


# Arc class is removed as its functionality is integrated into SpecInputArc/SpecOutputArc
# and transitions directly link to place names.

# Type aliases InputTokenMap and ActionOutput are removed as they were for the old execution model.

@dataclass
class Transition:
    name: str
    # Guard and action are significantly changed.
    # These fields are now primarily for programmatic definition if desired,
    # but their direct translation to SpecGuard/SpecAction is limited.
    # For to_spec_transition, we primarily use input/output_place_names.
    guard_callable: Optional[Callable[[Dict[str, List[Token]]], bool]] = field(default=None, repr=False)
    action_callable: Optional[Callable[[Dict[str, List[Token]]], tuple[Dict[str, List[Token]], Dict[str, List[Token]]]]] = field(default=None, repr=False)

    input_place_names: List[str] = field(default_factory=list)
    output_place_names: List[str] = field(default_factory=list)

    # Methods is_enabled and fire are removed (part of old execution model)

    def add_input_place_name(self, place_name: str):
        if place_name not in self.input_place_names:
            self.input_place_names.append(place_name)

    def add_output_place_name(self, place_name: str):
        if place_name not in self.output_place_names:
            self.output_place_names.append(place_name)

    def to_spec_transition(self) -> SpecTransition:
        spec_inputs = []
        for place_name in self.input_place_names:
            # Default consumption: one "any" token, named after the place
            spec_inputs.append(
                SpecInputArc(
                    place=place_name,
                    consumption_policy=SpecInputArcConsumptionPolicy(type="any", count=1),
                    variable_name=f"{place_name}_input_token" # Default variable name
                )
            )

        spec_outputs = []
        for place_name in self.output_place_names:
            # Default production: one placeholder token
            spec_outputs.append(
                SpecOutputArc(
                    place=place_name,
                    production_details=SpecOutputArcProductionDetails(
                        value={"placeholder_value": f"token_produced_for_{place_name}"},
                        count=1
                    )
                )
            )

        # Guard translation:
        # Automatic translation of guard_callable to SpecGuard is complex and out of scope.
        # A transition in the spec without a guard implies it's enabled if inputs are met.
        # If the original guard_callable was None (always true), this is fine.
        # If it had logic, that logic is NOT translated here.
        # Users would need to build SpecGuard manually for the SpecTransition.
        spec_guard_obj = None # No guard by default in the spec

        # Action translation:
        # The action_callable's detailed logic (token manipulation, value changes)
        # is NOT automatically translated into detailed SpecOutputArc production_details modifications.
        # The SpecOutputArcs created above are placeholders.
        # Users would need to refine these SpecOutputArcs manually or when creating SpecTransition directly.

        return SpecTransition(
            name=self.name,
            description=None, # Can be added if Transition objects store descriptions
            inputs=spec_inputs,
            outputs=spec_outputs,
            guard=spec_guard_obj
        )


@dataclass
class PetriNet:
    name: str
    places: Dict[str, Place] = field(default_factory=dict)
    transitions: Dict[str, Transition] = field(default_factory=dict)
    # Removed: arcs: List[Arc] = field(default_factory=list)

    def add_place(self, place: Place):
        if place.name in self.places:
            raise ValueError(f"Place with name {place.name} already exists.")
        self.places[place.name] = place

    def add_transition(self, transition: Transition):
        if transition.name in self.transitions:
            raise ValueError(f"Transition with name {transition.name} already exists.")
        # Ensure input/output places are known (optional strictness)
        # for place_name in transition.input_place_names:
        #     if place_name not in self.places:
        #         raise ValueError(f"Input place {place_name} for transition {transition.name} not found in PetriNet.")
        # for place_name in transition.output_place_names:
        #     if place_name not in self.places:
        #         raise ValueError(f"Output place {place_name} for transition {transition.name} not found in PetriNet.")
        self.transitions[transition.name] = transition

    # Removed: add_arc and add_arc_by_names as Arc class is removed.
    # Transitions now directly reference place names.

    def add_token(self, place_name: str, token: Token):
        if place_name not in self.places:
            raise ValueError(f"Place {place_name} not found.")
        self.places[place_name].add_token(token)

    # Removed: _get_input_token_map_for_transition, get_enabled_transitions, fire_transition, run
    # These were part of the old execution model.

    def get_marking(self) -> Dict[str, List[Any]]:
        """Returns the current marking of the Petri net (PYTHON token values in each place)."""
        return {name: [token.value for token in place.tokens] for name, place in self.places.items()}

    def to_specification(self) -> SpecPetriNet:
        spec_places = [p.to_spec_place() for p in self.places.values()]

        # Pass all_places to allow transitions to look up place details if needed
        # (though current to_spec_transition doesn't use it)
        spec_transitions = [t.to_spec_transition() for t in self.transitions.values()]

        initial_marking_spec: SpecInitialMarking = {}
        for place_name, place_obj in self.places.items():
            if place_obj.tokens:
                # Storing the direct value of the token, which should be JSON-serializable
                initial_marking_spec[place_name] = [token.value for token in place_obj.tokens]

        # Ensure initial_marking is None if empty, for cleaner JSON
        final_initial_marking = initial_marking_spec if initial_marking_spec else None

        return SpecPetriNet(
            name=self.name,
            places=spec_places,
            transitions=spec_transitions,
            initial_marking=final_initial_marking
        )
