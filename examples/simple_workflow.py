# examples/simple_workflow.py
from dataclasses import dataclass
import json # For pretty printing the spec

# Adjust import path if your package structure is different when running examples
from llm_tap.petri_nets import Token, Place, Transition, PetriNet
# Import the new SpecPetriNet for type hinting if needed, and its components
from llm_tap.pn_spec import SpecPetriNet

# --- Define a custom data structure for tokens (our "Color") ---
@dataclass
class Order:
    order_id: str
    item: str
    quantity: int
    processed: bool = False
    shipped: bool = False

# --- Define Places (using the existing Place class from petri_nets.py) ---
p_new_orders = Place(name="New Orders")
p_processed_orders = Place(name="Processed Orders")
p_shipped_orders = Place(name="Shipped Orders")
p_failed_processing = Place(name="Failed Processing") # Kept for structural representation

# --- Define Transitions (using the existing Transition class from petri_nets.py) ---
# The guard and action callables are no longer directly translated into the spec
# by the simplified to_spec_transition method. We define transitions by their
# name and the names of their input/output places.
# The generated spec will have basic input/output arcs.
# For more detailed spec behavior, one would manually create SpecTransition objects.

t_process_order = Transition(
    name="Process Order",
    # guard_callable and action_callable are not set, as their direct translation
    # to the spec is not supported by the simplified to_spec_transition.
    # Complex logic would require manual SpecGuard/SpecAction creation.
    input_place_names=["New Orders"],
    # The output_place_names will generate basic SpecOutputArcs.
    # The previous action logic (e.g. conditional output to "Failed Processing")
    # is not captured in this basic spec generation.
    output_place_names=["Processed Orders", "Failed Processing"]
)

t_ship_order = Transition(
    name="Ship Order",
    input_place_names=["Processed Orders"],
    output_place_names=["Shipped Orders"]
)

# --- Create and Configure Petri Net (using PetriNet class from petri_nets.py) ---
def main():
    order_workflow_net = PetriNet(name="Order Fulfillment Workflow Definition")

    # Add places
    order_workflow_net.add_place(p_new_orders)
    order_workflow_net.add_place(p_processed_orders)
    order_workflow_net.add_place(p_shipped_orders)
    order_workflow_net.add_place(p_failed_processing)

    # Add transitions
    order_workflow_net.add_transition(t_process_order)
    order_workflow_net.add_transition(t_ship_order)

    # Add initial tokens (initial marking)
    # These should be JSON-serializable values as per TokenValue.
    # Using vars() to convert dataclass to dict for straightforward serialization.
    order1_data = Order(order_id="ORD001", item="Laptop", quantity=1)
    order2_data = Order(order_id="ORD002", item="Mouse", quantity=2)

    # We add Token objects with these dictionary representations as values
    order_workflow_net.add_token("New Orders", Token(value=vars(order1_data)))
    order_workflow_net.add_token("New Orders", Token(value=vars(order2_data)))


    print("--- Petri Net Definition (Programmatic) ---")
    print(f"Net Name: {order_workflow_net.name}")
    print("Places:")
    for name in order_workflow_net.places:
        print(f"  - {name}")
    print("Transitions:")
    for name in order_workflow_net.transitions:
        print(f"  - {name} (Inputs: {order_workflow_net.transitions[name].input_place_names}, Outputs: {order_workflow_net.transitions[name].output_place_names})")
    print("Initial Marking (Python objects):")
    for name, place_tokens in order_workflow_net.get_marking().items():
        # Printing token values directly
        print(f"  {name}: {place_tokens}")
    print("-" * 40)

    # Generate the specification
    print("--- Generating Serializable Specification ---")
    petri_net_specification: SpecPetriNet = order_workflow_net.to_specification()

    # Convert the specification to a dictionary for pretty printing
    # (using the to_json_dict method from SpecPetriNet in pn_spec.py)
    spec_dict = petri_net_specification.to_json_dict()

    print("Specification (JSON format):")
    print(json.dumps(spec_dict, indent=2))
    print("-" * 40)

    # The example no longer runs the simulation as the PetriNet class
    # is now a definition builder, not an execution engine.
    # The generated spec_dict could be saved to a JSON file or sent to
    # a workflow engine that understands this Petri Net specification.

if __name__ == "__main__":
    main()
