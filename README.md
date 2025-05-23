# LLM Trigger-Action Programs

`llm-tap` is a lightweight and extensible library for building Trigger-Action programs with Large Language Models (LLMs).

## Quickstart

Let's take an example to generate a workflow based on the following user query:

"When the electricity price is below $0.4/ kWh and my Tesla is plugged, turn on charging."

### OpenAI

```python
import os
from llm_tap import llm
from llm_tap.models import Workflow

system_prompt = """You are an automation assistant.

- Design a workflow to answer user's query for an automation.
- Be sure to consider all branches when evaluating conditionals.
- Ensure safe defaults.

"""
prompt = "When the electricity price is below $0.4/ kWh and my Tesla is plugged, turn on charging."

with llm.HTTP(
    base_url="https://api.openai.com/v1/chat/completions",
    api_key=os.getenv('OPENAI_API_KEY'),
    model="gpt-4.1-nano",
) as parser:
    workflow = parser.parse(data_class=Workflow, prompt=prompt, system_prompt=system_prompt)
    print(workflow)
```

----

When called, this displays:
```python
Workflow(
    name="Electricity Price and Tesla Charging Workflow",
    description="Automates Tesla charging based on electricity prices.",
    triggers=[Trigger(description="Electricity price updates")],
    nodes=[
        Node(
            name="Check Electricity Price and Tesla Plug Status",
            condition_sets=[
                ConditionSet(
                    conditions=[
                        Condition(
                            description="Electricity price is below $0.4/kWh"
                        )
                    ],
                    operator="AND",
                ),
                ConditionSet(
                    conditions=[Condition(description="Tesla is plugged in")],
                    operator="AND",
                ),
            ],
            branches=[
                Branch(
                    conditions_value=True,
                    actions=[Action(description="Turn on Tesla charging")],
                ),
                Branch(
                    conditions_value=False,
                    actions=[Action(description="Do nothing")],
                ),
            ],
        )
    ],
)

```

### GGUF Open weights models with llama.cpp

```python
import os
from llm_tap import llm
from llm_tap.models import Workflow

system_prompt = """You are an automation assistant.

- Design a workflow to answer user's query for an automation.
- Be sure to consider all branches when evaluating conditionals.
- Ensure safe defaults.

"""
prompt = "When the electricity price is below $0.4/ kWh and my Tesla is plugged, turn on charging."


#: model should be the path to a GGUF model
model="~/.cache/py-llm-core/models/qwen2.5-1.5b"
# model="~/.cache/py-llm-core/models/llama-3.2-3b"
# model="~/.cache/py-llm-core/models/llama-3.1-8b"
# model="~/.cache/py-llm-core/models/qwen3-4b"
# model="~/.cache/py-llm-core/models/mistral-7b"

with llm.LLamaCPP(model=model) as parser:
    workflow = parser.parse(data_class=Workflow, prompt=prompt)
    print(workflow)
```

----

When called, this displays:
```python
Workflow(
    name="Turn on charging",
    description="Turn on charging when the electricity price is below $0.4/ kWh and my Tesla is plugged.",
    triggers=[
        Trigger(
            description="Electricity price is below $0.4/ kWh and my Tesla is plugged."
        )
    ],
    nodes=[
        Node(
            name="Turn on charging",
            condition_sets=[
                ConditionSet(
                    conditions=[
                        Condition(
                            description="Electricity price is below $0.4/ kWh"
                        ),
                        Condition(description="My Tesla is plugged"),
                    ],
                    operator="AND",
                )
            ],
            branches=[
                Branch(
                    conditions_value=True,
                    actions=[Action(description="Turn on charging")],
                )
            ],
        )
    ],
)

```

## Documentation - Tutorial

Currently work in progress here: https://advanced-stack.com/resources/how-to-build-workflows-trigger-action-program-with-llms.html
