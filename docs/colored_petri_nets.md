# Using the Colored Petri Net Library for Workflow Management

This document describes how to use the Colored Petri Net (CPN) library to model and execute workflows. CPNs extend traditional Petri nets by allowing tokens to have data, referred to as "colors." This enables more expressive and compact modeling of complex systems.

## Core Concepts

The library is built around a few core concepts:

*   **Color:** Represents the data or type associated with a token. In this library, a color can be any Python data type or object. This allows for rich information to be carried by tokens.
*   **Token:** An instance of a color that resides in a Place. Each token has a specific value (its color).
*   **Place:** A container for tokens. Places can be typed, meaning they might only accept tokens of certain colors or structures. They can also have capacities.
*   **Transition:** Represents an event, action, or task in the workflow. A transition can "fire" (execute) if certain conditions are met.
    *   **Guard Condition:** A function associated with a transition that evaluates the available tokens in its input places. The transition is enabled only if the guard condition returns true. This allows for data-dependent routing and decisions.
    *   **Action Function:** A function executed when a transition fires. It typically consumes tokens from input places and produces new tokens (potentially with new/modified colors) in output places.
*   **Arc:** A directed connection between a Place and a Transition, or a Transition and a Place.
    *   **Input Arc:** Connects a Place to a Transition. It defines which tokens (and how many, of which colors) are potentially consumed by the transition.
    *   **Output Arc:** Connects a Transition to a Place. It defines which tokens (and how many, of which colors) are produced by the transition when it fires. Arc expressions can define how many tokens of specific colors are moved.
*   **PetriNet:** The overall model, containing a collection of Places, Transitions, and Arcs. It provides the engine for simulating the workflow by firing transitions.

## Defining a Workflow with Colored Petri Nets

To model a workflow, you will define these components using the provided data classes.

### 1. Define Colors and Tokens

Colors are implicitly defined by the data you assign to tokens. A `Token` will be a dataclass holding a `value` (its color).

```python
# Example (conceptual - actual class names might vary slightly)
# from llm_tap.petri_nets import Token

# Token carrying an integer
token1 = Token(value=10)

# Token carrying a string
token2 = Token(value="order_id_123")

# Token carrying a custom object
class OrderDetails:
    def __init__(self, product_id, quantity):
        self.product_id = product_id
        self.quantity = quantity

token3 = Token(value=OrderDetails(product_id="P100", quantity=2))
```

### 2. Define Places

A `Place` will be a dataclass that holds a list of tokens. You might specify a name for clarity.

```python
# from llm_tap.petri_nets import Place

# Place to hold new orders
new_orders_place = Place(name="New Orders")

# Place to hold processed orders
processed_orders_place = Place(name="Processed Orders")
```

### 3. Define Transitions

A `Transition` will be the core of your workflow logic.

```python
# from llm_tap.petri_nets import Transition, Arc

# --- Example: Transition to process an order ---

# Guard function: checks if there's an order token in the input place
def can_process_order(tokens_map):
    # tokens_map is a dict like {'input_place_name': [Token, ...]}
    new_orders = tokens_map.get("New Orders", [])
    return any(isinstance(token.value, OrderDetails) for token in new_orders)

# Action function: processes the order and creates a new token
def process_order_action(tokens_map):
    # Consume one OrderDetails token
    # Produce a confirmation token (e.g., a string)
    order_token_to_process = None
    for token in tokens_map["New Orders"]:
        if isinstance(token.value, OrderDetails):
            order_token_to_process = token
            break

    # This function would return a map like:
    # {'output_place_name': [Token(value="confirmation_ABC")]}
    # and also specify which tokens were consumed from input places.
    # The exact signature will be defined by the library.

    if order_token_to_process:
        # Simulate processing
        processed_data = f"Processed order: {order_token_to_process.value.product_id}"
        # Define consumed tokens (from which input place)
        consumed = {"New Orders": [order_token_to_process]}
        # Define produced tokens (to which output place)
        produced = {"Processed Orders": [Token(value=processed_data)]}
        return consumed, produced
    return {}, {}


process_order_transition = Transition(
    name="Process Order",
    guard=can_process_order,
    action=process_order_action
)
```

### 4. Define Arcs

Arcs connect Places and Transitions. The library will provide a way to define these connections, possibly when creating the `PetriNet` instance or by adding arcs to transitions/places.

*   **Input Arc Example:** An arc from `new_orders_place` to `process_order_transition`. It might specify that the transition expects one token of type `OrderDetails`.
*   **Output Arc Example:** An arc from `process_order_transition` to `processed_orders_place`. It specifies that the transition produces a confirmation token.

The `Transition`'s action function will implicitly define the token flow for arcs, by specifying which tokens are consumed from which input places and which tokens are produced for which output places.

### 5. Create and Initialize the PetriNet

The `PetriNet` class will hold all your defined places, transitions, and their connections.

```python
# from llm_tap.petri_nets import PetriNet, Token, Place, Transition

# (Define places and transitions as above)

# Create the PetriNet
workflow_net = PetriNet(name="Order Processing Workflow")

# Add places
workflow_net.add_place(new_orders_place)
workflow_net.add_place(processed_orders_place)

# Add transition
workflow_net.add_transition(process_order_transition)

# Define connections (arcs)
# The exact API for this will be part of the library.
# For instance, transitions might store their input/output place names,
# and the PetriNet resolves these names to actual Place objects.
process_order_transition.add_input_place_name("New Orders")
process_order_transition.add_output_place_name("Processed Orders")


# Add initial tokens (marking)
initial_order = OrderDetails(product_id="P101", quantity=1)
workflow_net.add_token("New Orders", Token(value=initial_order))
workflow_net.add_token("New Orders", Token(value=OrderDetails(product_id="P102", quantity=5)))

```

## Executing the Workflow

The `PetriNet` instance will provide methods to simulate the workflow:

1.  **Check Enabled Transitions:** Identify all transitions whose guard conditions are currently met.
    ```python
    enabled_transitions = workflow_net.get_enabled_transitions()
    ```

2.  **Fire a Transition:** Execute an enabled transition. This will:
    *   Call the transition's action function.
    *   Consume tokens from its input places (as defined by the action function).
    *   Produce tokens in its output places (as defined by the action function).
    ```python
    if enabled_transitions:
        workflow_net.fire_transition(enabled_transitions[0])
    ```

3.  **Run Simulation:** Execute transitions iteratively until no more transitions are enabled or a specific condition is met.
    ```python
    workflow_net.run() # Runs until quiescent state
    ```

## Example: Simple Document Approval Workflow

Let's model a workflow where a document needs approval.

*   **Places:**
    *   `DraftDocuments`: Holds documents pending review. Token color: `{ 'doc_id': string, 'content': string }`
    *   `PendingApproval`: Holds documents reviewed and awaiting final approval. Token color: `{ 'doc_id': string, 'content': string, 'reviewed_by': string }`
    *   `ApprovedDocuments`: Holds approved documents. Token color: `{ 'doc_id': string, 'approved_by': string }`
    *   `RejectedDocuments`: Holds rejected documents. Token color: `{ 'doc_id': string, 'rejected_by': string }`

*   **Transitions:**
    *   `SubmitForReview`:
        *   Input: `DraftDocuments`
        *   Output: `PendingApproval`
        *   Action: Moves document token, adds reviewer info (e.g. reviewer chosen by a simple rule or passed as data).
    *   `ApproveDocument`:
        *   Input: `PendingApproval`
        *   Guard: Checks if the document has been reviewed (e.g., `token.value['reviewed_by'] is not None`).
        *   Output: `ApprovedDocuments`
        *   Action: Moves document token, adds approver info.
    *   `RejectDocument`:
        *   Input: `PendingApproval`
        *   Guard: (Similar to Approve, or perhaps a different condition)
        *   Output: `RejectedDocuments`
        *   Action: Moves document token, adds rejector info.

This CPN model allows tracking the state of each document (its color) as it moves through the workflow, with transitions controlling the logic and data transformation.

## Further Considerations (Advanced)

*   **Arc Expressions:** For more complex scenarios, arcs could have expressions determining how many tokens of a specific color are needed or produced. (e.g., "take 2 tokens of color 'X' if available"). The current design leans on the transition's action function for this logic.
*   **Time:** Timed Petri nets could be an extension, where transitions take time to fire.
*   **Hierarchy:** Complex workflows can be built by composing Petri nets.

This library aims to provide a flexible and powerful way to model and execute data-centric workflows using the Colored Petri Net formalism.
