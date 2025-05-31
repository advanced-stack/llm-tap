# examples/simple_workflow.py
from dataclasses import dataclass
from typing import Dict, List

# Adjust import path if your package structure is different when running examples
# For a package 'llm_tap', this would typically be:
# from llm_tap.petri_nets import Token, Place, Transition, PetriNet, InputTokenMap, ActionOutput
# For local testing, you might need to adjust sys.path or run as a module.
# Assuming llm_tap is installed or PYTHONPATH is set:
from llm_tap.petri_nets import Token, Place, Transition, PetriNet, InputTokenMap, ActionOutput

# --- Define a custom data structure for tokens (our "Color") ---
@dataclass
class Order:
    order_id: str
    item: str
    quantity: int
    processed: bool = False
    shipped: bool = False

# --- Define Places ---
p_new_orders = Place(name="New Orders")
p_processed_orders = Place(name="Processed Orders")
p_shipped_orders = Place(name="Shipped Orders")
p_failed_processing = Place(name="Failed Processing")

# --- Define Transition Logic: Guards and Actions ---

# Guard for t_process_order: checks for an unprocessed order
def guard_process_order(inputs: InputTokenMap) -> bool:
    new_orders = inputs.get("New Orders", [])
    return any(isinstance(token.value, Order) and not token.value.processed for token in new_orders)

# Action for t_process_order: marks an order as processed
def action_process_order(inputs: InputTokenMap) -> ActionOutput:
    consumed_tokens: Dict[str, List[Token]] = {"New Orders": []}
    produced_tokens: Dict[str, List[Token]] = {"Processed Orders": []}

    order_token_to_process = None
    for token in inputs.get("New Orders", []):
        if isinstance(token.value, Order) and not token.value.processed:
            order_token_to_process = token
            break # Process one at a time

    if order_token_to_process:
        consumed_tokens["New Orders"].append(order_token_to_process)

        original_order: Order = order_token_to_process.value
        processed_order_data = Order(
            order_id=original_order.order_id,
            item=original_order.item,
            quantity=original_order.quantity,
            processed=True # Mark as processed
        )
        produced_tokens["Processed Orders"].append(Token(value=processed_order_data))
        print(f"Processing order: {original_order.order_id}")

    return consumed_tokens, produced_tokens

# Guard for t_ship_order: checks for a processed, unshipped order
def guard_ship_order(inputs: InputTokenMap) -> bool:
    processed_orders = inputs.get("Processed Orders", [])
    return any(isinstance(token.value, Order) and token.value.processed and not token.value.shipped for token in processed_orders)

# Action for t_ship_order: marks an order as shipped
def action_ship_order(inputs: InputTokenMap) -> ActionOutput:
    consumed_tokens: Dict[str, List[Token]] = {"Processed Orders": []}
    produced_tokens: Dict[str, List[Token]] = {"Shipped Orders": []}

    order_token_to_ship = None
    for token in inputs.get("Processed Orders", []):
        if isinstance(token.value, Order) and token.value.processed and not token.value.shipped:
            order_token_to_ship = token
            break # Ship one at a time

    if order_token_to_ship:
        consumed_tokens["Processed Orders"].append(order_token_to_ship)

        original_order: Order = order_token_to_ship.value
        shipped_order_data = Order(
            order_id=original_order.order_id,
            item=original_order.item,
            quantity=original_order.quantity,
            processed=True,
            shipped=True # Mark as shipped
        )
        produced_tokens["Shipped Orders"].append(Token(value=shipped_order_data))
        print(f"Shipping order: {original_order.order_id}")

    return consumed_tokens, produced_tokens

# --- Define Transitions ---
t_process_order = Transition(
    name="Process Order",
    guard=guard_process_order,
    action=action_process_order,
    input_place_names=["New Orders"],
    output_place_names=["Processed Orders", "Failed Processing"] # Failed path not implemented in action for simplicity
)

t_ship_order = Transition(
    name="Ship Order",
    guard=guard_ship_order,
    action=action_ship_order,
    input_place_names=["Processed Orders"],
    output_place_names=["Shipped Orders"]
)

# --- Create and Configure Petri Net ---
def main():
    order_workflow_net = PetriNet(name="Order Fulfillment Workflow")

    # Add places
    order_workflow_net.add_place(p_new_orders)
    order_workflow_net.add_place(p_processed_orders)
    order_workflow_net.add_place(p_shipped_orders)
    order_workflow_net.add_place(p_failed_processing)

    # Add transitions
    order_workflow_net.add_transition(t_process_order)
    order_workflow_net.add_transition(t_ship_order)

    # Add initial tokens (initial marking)
    order1 = Order(order_id="ORD001", item="Laptop", quantity=1)
    order2 = Order(order_id="ORD002", item="Mouse", quantity=2)

    order_workflow_net.add_token("New Orders", Token(value=order1))
    order_workflow_net.add_token("New Orders", Token(value=order2))

    print("Initial Marking:")
    for name, place_tokens in order_workflow_net.get_marking().items():
        print(f"  {name}: {[(t.order_id if isinstance(t,Order) else t) for t in place_tokens]}")
    print("-" * 30)

    # Run the simulation
    steps = order_workflow_net.run(max_steps=10) # Max steps to prevent infinite loops in case of errors

    print("-" * 30)
    print(f"Simulation finished after {steps} steps.")
    print("Final Marking:")
    for name, place_tokens in order_workflow_net.get_marking().items():
        print(f"  {name}: {[(t.order_id if isinstance(t,Order) else t) for t in place_tokens]}")

    print("-" * 30)
    print("Shipped Orders Contents:")
    for token_val in order_workflow_net.places["Shipped Orders"].tokens:
        if isinstance(token_val.value, Order):
            print(f"  Order ID: {token_val.value.order_id}, Item: {token_val.value.item}, Shipped: {token_val.value.shipped}")


if __name__ == "__main__":
    # This is a common pattern if you need to adjust Python's import path
    # when running scripts directly from a subdirectory of a package.
    # import sys
    # import os
    # # Assuming the script is in 'examples' and 'src' is at the same level as 'examples'
    # # and your package 'llm_tap' is inside 'src'.
    # project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # src_path = os.path.join(project_root, 'src')
    # if src_path not in sys.path:
    #    sys.path.insert(0, src_path)
    # Now the import `from llm_tap.petri_nets import ...` should work.
    main()
