# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Any, List, Dict, Callable, Optional, TypeVar, Generic

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
    # Future extensions: capacity, accepted token types/colors

    def add_token(self, token: Token):
        self.tokens.append(token)

    def remove_token(self, token: Token):
        # Removing the specific token instance might be tricky if multiple
        # identical tokens exist and hashing/equality is based on value.
        # For now, assume we remove a token that equals the given token.
        # If specific instance removal is needed, this logic might need adjustment
        # or tokens might need unique IDs.
        try:
            self.tokens.remove(token)
        except ValueError:
            # Token not found, could raise an error or handle silently
            # For now, let's raise to make it explicit
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


# Forward declaration for Transition type hint in Arc
class Transition;

@dataclass
class Arc:
    """
    Represents a directed connection.
    In this initial generic version, arcs are primarily conceptual links.
    The logic of token consumption/production and quantity/type matching
    will be handled by the Transition's guard and action functions.

    - For an input arc (Place -> Transition): `source` is Place, `target` is Transition.
    - For an output arc (Transition -> Place): `source` is Transition, `target` is Place.
    """
    source_name: str  # Name of the source Place or Transition
    target_name: str  # Name of the target Place or Transition
    # Future extensions: weight (how many tokens), arc expression (specific token types)

# Type alias for the structure that guard and action functions will receive
# It maps input place names to a list of tokens available in that place.
InputTokenMap = Dict[str, List[Token]]

# Type alias for the structure that action functions should return
# The first dict maps place names to tokens to be consumed from them.
# The second dict maps place names to tokens to be produced into them.
ActionOutput = tuple[Dict[str, List[Token]], Dict[str, List[Token]]]

@dataclass
class Transition:
    """
    Represents an event or task in the workflow.
    A transition can fire if its guard condition is met.
    Firing a transition consumes tokens from input places and produces tokens in output places
    as defined by its action function.
    """
    name: str
    guard: Callable[[InputTokenMap], bool] = field(default=lambda inputs: True)
    action: Callable[[InputTokenMap], ActionOutput] = field(default=lambda inputs: ({}, {}))

    # Names of input and output places. The PetriNet engine will resolve these.
    input_place_names: List[str] = field(default_factory=list)
    output_place_names: List[str] = field(default_factory=list)

    def is_enabled(self, input_token_map: InputTokenMap) -> bool:
        """
        Checks if the transition is enabled based on its guard condition.
        The input_token_map is provided by the PetriNet engine.
        """
        try:
            return self.guard(input_token_map)
        except Exception as e:
            # Optionally log the error
            # print(f"Error in guard for transition {self.name}: {e}")
            return False

    def fire(self, input_token_map: InputTokenMap) -> ActionOutput:
        """
        Executes the transition's action.
        The input_token_map is provided by the PetriNet engine.
        Returns a tuple: (consumed_tokens_map, produced_tokens_map)
        consumed_tokens_map: {place_name: [Token, ...]}
        produced_tokens_map: {place_name: [Token, ...]}
        """
        try:
            return self.action(input_token_map)
        except Exception as e:
            # Optionally log the error
            # print(f"Error in action for transition {self.name}: {e}")
            # Return empty dicts to signify failure or no change
            return {}, {}

    def add_input_place_name(self, place_name: str):
        if place_name not in self.input_place_names:
            self.input_place_names.append(place_name)

    def add_output_place_name(self, place_name: str):
        if place_name not in self.output_place_names:
            self.output_place_names.append(place_name)


@dataclass
class PetriNet:
    """
    The main class for a Colored Petri Net.
    It holds the places, transitions, and provides methods to execute the net.
    """
    name: str
    places: Dict[str, Place] = field(default_factory=dict)
    transitions: Dict[str, Transition] = field(default_factory=dict)

    def add_place(self, place: Place):
        if place.name in self.places:
            raise ValueError(f"Place with name {place.name} already exists.")
        self.places[place.name] = place

    def add_transition(self, transition: Transition):
        if transition.name in self.transitions:
            raise ValueError(f"Transition with name {transition.name} already exists.")
        self.transitions[transition.name] = transition

    def add_token(self, place_name: str, token: Token):
        """Adds a token to the specified place."""
        if place_name not in self.places:
            raise ValueError(f"Place {place_name} not found.")
        self.places[place_name].add_token(token)

    def _get_input_token_map_for_transition(self, transition: Transition) -> InputTokenMap:
        """
        Constructs the InputTokenMap for a given transition, providing it with
        the tokens from its declared input places.
        """
        input_map: InputTokenMap = {}
        for place_name in transition.input_place_names:
            if place_name in self.places:
                # Provide a copy of the list of tokens to avoid direct modification
                # of place's tokens by guard or action functions before actual consumption.
                input_map[place_name] = list(self.places[place_name].tokens)
            else:
                # If an input place is declared but not in the net, provide empty list.
                # Alternatively, this could be an error condition.
                input_map[place_name] = []
        return input_map

    def get_enabled_transitions(self) -> List[Transition]:
        """
        Returns a list of all transitions that are currently enabled.
        A transition is enabled if all its input places are defined in the net,
        and its guard condition evaluates to True.
        """
        enabled = []
        for transition in self.transitions.values():
            # Check if all input places for the transition exist in the PetriNet
            all_input_places_exist = all(
                place_name in self.places for place_name in transition.input_place_names
            )
            if not all_input_places_exist:
                # print(f"Transition {transition.name} disabled: Not all input places are defined in the PetriNet.")
                continue

            input_token_map = self._get_input_token_map_for_transition(transition)
            if transition.is_enabled(input_token_map):
                enabled.append(transition)
        return enabled

    def fire_transition(self, transition_name: str) -> bool:
        """
        Fires a specific transition if it's enabled.
        Firing involves:
        1. Checking if the transition exists and is enabled.
        2. Executing its action function to get consumed and produced tokens.
        3. Removing consumed tokens from input places.
        4. Adding produced tokens to output places.
        Returns True if fired successfully, False otherwise.
        """
        if transition_name not in self.transitions:
            # print(f"Cannot fire: Transition {transition_name} not found.")
            return False

        transition = self.transitions[transition_name]

        # Check if all input places for the transition exist
        if not all(place_name in self.places for place_name in transition.input_place_names):
            # print(f"Transition {transition.name} cannot fire: Not all input places are defined in the PetriNet.")
            return False

        # Check if all output places for the transition exist (important for producing tokens)
        if not all(place_name in self.places for place_name in transition.output_place_names):
            # print(f"Transition {transition.name} cannot fire: Not all output places are defined in the PetriNet.")
            return False

        input_token_map = self._get_input_token_map_for_transition(transition)

        if not transition.is_enabled(input_token_map):
            # print(f"Transition {transition.name} is not enabled.")
            return False

        consumed_map, produced_map = transition.fire(input_token_map)

        # Validate that consumed tokens exist before removing
        for place_name, tokens_to_consume in consumed_map.items():
            if place_name not in self.places:
                # print(f"Error firing {transition.name}: Consuming from non-existent place {place_name}")
                return False # Abort firing
            place = self.places[place_name]
            for token_to_consume in tokens_to_consume:
                # Ensure the place actually has this token or an equivalent one
                # This check depends on Token.__eq__ and Place.tokens list contents
                if token_to_consume not in place.tokens:
                    # print(f"Error firing {transition.name}: Token {token_to_consume} not found in {place_name} for consumption.")
                    return False # Abort firing

        # Validate that produced tokens are going to valid places
        for place_name in produced_map.keys():
            if place_name not in self.places:
                 # print(f"Error firing {transition.name}: Producing to non-existent place {place_name}")
                return False # Abort firing
            if place_name not in transition.output_place_names:
                # print(f"Error firing {transition.name}: Place {place_name} is not a declared output for this transition.")
                return False # Abort firing


        # All checks passed, proceed with token manipulation
        # 1. Consume tokens
        for place_name, tokens_to_consume in consumed_map.items():
            place = self.places[place_name]
            for token_to_consume in tokens_to_consume:
                try:
                    place.remove_token(token_to_consume)
                except ValueError:
                    # This should ideally not happen if validation above is thorough
                    # and action function is well-behaved.
                    # print(f"Critical error: Failed to remove {token_to_consume} from {place_name} during firing of {transition.name}.")
                    # This might indicate a need for rollback or more complex state management.
                    # For now, we'll log and potentially leave the net in an inconsistent state.
                    # Re-add already removed tokens if possible? (complex)
                    return False # Abort, but state might be partially changed.

        # 2. Produce tokens
        for place_name, tokens_to_produce in produced_map.items():
            place = self.places[place_name]
            for token_to_produce in tokens_to_produce:
                place.add_token(token_to_produce)

        # print(f"Transition {transition.name} fired successfully.")
        return True

    def run(self, max_steps: Optional[int] = None) -> int:
        """
        Runs the Petri Net simulation by repeatedly firing enabled transitions.
        Stops when no transitions are enabled (quiescent state) or
        max_steps are reached.
        Returns the number of steps (firings) executed.
        """
        steps = 0
        while True:
            enabled_transitions = self.get_enabled_transitions()
            if not enabled_transitions:
                # print("No more enabled transitions. Simulation finished.")
                break

            # Simple strategy: fire the first enabled transition.
            # More complex strategies could be implemented (e.g., random choice, priority).
            transition_to_fire = enabled_transitions[0]

            fired = self.fire_transition(transition_to_fire.name)

            if fired:
                steps += 1
            else:
                # print(f"Failed to fire {transition_to_fire.name}, though it was reported as enabled. This might indicate an issue.")
                # Attempting to fire another enabled transition if available, or break.
                # For simplicity, if one fails (which shouldn't happen if is_enabled is consistent with fire conditions), we break.
                break


            if max_steps is not None and steps >= max_steps:
                # print(f"Reached maximum steps ({max_steps}). Simulation stopping.")
                break

        # print(f"Simulation ran for {steps} steps.")
        return steps

    def get_marking(self) -> Dict[str, List[Any]]:
        """Returns the current marking of the Petri net (tokens in each place)."""
        return {name: [token.value for token in place.tokens] for name, place in self.places.items()}
