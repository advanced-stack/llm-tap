# Petri Net Serializable Specification

This document defines the JSON-based format for specifying Colored Petri Nets in a way that decouples their definition from their execution, allowing for delegation to a third-party workflow engine.

## 1. Overall Structure

A Petri net is represented as a JSON object with the following top-level keys:

- `name`: (string) The name of the Petri net.
- `places`: (array) An array of Place objects (see section 2).
- `transitions`: (array) An array of Transition objects (see section 3).
- `initial_marking`: (optional, object) Defines the initial tokens in places.
    - Keys are place names.
    - Values are arrays of token values (see section 4 on Tokens).

**Example:**

```json
{
  "name": "SimpleOrderWorkflow",
  "places": [
    // ... place definitions
  ],
  "transitions": [
    // ... transition definitions
  ],
  "initial_marking": {
    "NewOrders": [
      { "order_id": "ORD001", "item": "Laptop", "quantity": 1 },
      { "order_id": "ORD002", "item": "Mouse", "quantity": 2 }
    ]
  }
}
```

## 2. Places

A Place object defines a location in the Petri net that can hold tokens.

- `name`: (string, required) The unique name of the place.
- `description`: (string, optional) A human-readable description.
- `capacity`: (integer, optional) Maximum number of tokens the place can hold (not enforced by spec, but for engine). Default is unbounded.

**Example:**

```json
{
  "name": "NewOrders",
  "description": "Incoming customer orders"
}
```

## 3. Transitions

A Transition object defines an event or task that can occur.

- `name`: (string, required) The unique name of the transition.
- `description`: (string, optional) A human-readable description.
- `inputs`: (array, required) An array of Input Arc objects.
- `outputs`: (array, required) An array of Output Arc objects.
- `guard`: (optional) A Guard object defining conditions for firing (see section 5). If omitted, the transition is always enabled if input tokens are available as per arcs.
- `actions`: (array, required) An array of Action objects defining what happens when the transition fires (see section 6).

### 3.1. Input Arc Object

Defines an input arc from a place to the transition.

- `place`: (string, required) The name of the input place.
- `consumption_policy`: (object, optional) Defines which tokens are consumed.
    - `type`: (string) e.g., "match_value", "any". Default: "any" (consumes one arbitrary token).
    - `value_filter`: (object, if type is "match_value") A filter to select specific tokens.
        - Example: `{ "attribute": "status", "equals": "pending" }`
    - `count`: (integer, optional) Number of tokens to consume. Default: 1.

**Example Input Arc:**

```json
{
  "place": "NewOrders",
  "consumption_policy": {
    "type": "match_value",
    "value_filter": { "attribute": "processed", "equals": false },
    "count": 1
  },
  "variable_name": "order_to_process" // Name to refer to the matched token(s) in actions/guards
}
```

### 3.2. Output Arc Object

Defines an output arc from the transition to a place.

- `place`: (string, required) The name of the output place.
- `production_details`: (object, required) Defines the token(s) to be produced.
    - `value`: (any JSON-compatible type or object) The direct value of the token to produce.
    - `copy_from_input`: (string, optional) Name of an input variable (from `variable_name` in an input arc) to copy the value from.
    - `modifications`: (array of objects, optional, if `copy_from_input` is used) Modifications to apply to the copied token.
        - `attribute`: (string) Attribute to modify.
        - `set_value`: (any) Value to set.
    - `count`: (integer, optional) Number of identical tokens to produce. Default: 1.

**Example Output Arc:**

```json
{
  "place": "ProcessedOrders",
  "production_details": {
    "copy_from_input": "order_to_process",
    "modifications": [
      { "attribute": "processed", "set_value": true }
    ]
  }
}
```

## 4. Tokens

Tokens are represented by their values, which can be any JSON-compatible data type (strings, numbers, booleans, objects, arrays). The "color" of a token is its data payload.

**Example Token Value (as part of an initial marking or production):**

```json
{ "order_id": "ORD001", "item": "Laptop", "quantity": 1, "processed": false }
```

## 5. Guards

A Guard object defines the conditions that must be met (in addition to token availability on input arcs) for a transition to fire.

- `condition`: (object, required) The condition to evaluate.
    - `type`: (string) e.g., "token_match", "expression".
    - **For `token_match`:**
        - `input_variable`: (string) The `variable_name` of an input arc.
        - `attribute`: (string) The attribute of the token to check.
        - `operator`: (string) e.g., "equals", "not_equals", "greater_than", "exists".
        - `value`: (any) The value to compare against.
    - **For `expression` (more advanced, future):**
        - `dsl_string`: (string) A string representing the condition in a defined DSL.

**Example Guard:**

```json
{
  "condition": {
    "type": "token_match",
    "input_variable": "order_to_process", // from an input arc's variable_name
    "attribute": "quantity",
    "operator": "greater_than",
    "value": 0
  }
}
```
If a guard is omitted, it's considered always true, provided input arc conditions are met.

## 6. Actions

Actions define the operations performed when a transition fires, primarily concerning token consumption and production. The input and output arcs define the core of token movement. Actions here can be used for more complex operations if needed, but for now, most logic is in the arc definitions.

This section might be expanded if more complex operations beyond simple token production (defined in output arcs) are needed, such as conditional production or complex token transformations not covered by `modifications`.

For the initial version, the `inputs` and `outputs` array on the transition largely define the actions of token consumption and production.

**Example (Conceptual - most of this is handled by input/output arc definitions now):**

The `action_process_order` from the Python example would be represented by:
1. An input arc from "NewOrders" that matches an unprocessed order and names it `order_to_process`.
2. An output arc to "ProcessedOrders" that copies `order_to_process` and modifies its `processed` attribute to `true`.

If more complex, imperative-style actions are needed later, their structure would be defined here. For instance:
```json
// Future consideration for more complex actions:
// "actions": [
//   {
//     "type": "log_message",
//     "message": "Processing order {order_to_process.order_id}"
//   },
//   {
//     "type": "external_call",
//     "service_url": "http://api.example.com/process",
//     "payload_from_input": "order_to_process"
//   }
// ]
```
For now, we assume the primary actions are token consumption (defined by input arcs) and production (defined by output arcs).

This declarative approach ensures that the Petri net's logic is transparent and can be interpreted by a separate execution engine.
