# LLM TAP (Trigger-Action Programs)

`llm-tap` is a lightweight and extensible library to generate workflows using Large Language Models (LLMs). `llm-tap` provides mechanisms and data structures to generate workflows and constraints for any existing workflow engine.

`llm-tap` is *not* a workflow library but a workflow generator.

## Quickstart

Let's take an example to generate a workflow based on the following user query:

> *When the electricity price is below $0.4/ kWh and my Tesla is plugged, turn on charging.*

To generate a workflow, `llm-tap` uses Colored Petri Nets to describe the different components.


```python
from llm_tap import llm
from llm_tap.models import (
    Workflow,
    Place,
    TokenType,
    instructions,
    register_place,
    register_token_type,
    get_places,
)

remaining_range = TokenType(name="remaining_range", type="INT")
charger_enabled = TokenType(name="charger_enabled", type="BOOL")
car_plugged = TokenType(name="car_plugged", type="BOOL")
electricity_price = TokenType(name="electricity_price", type="FLOAT")


register_token_type(remaining_range)
register_token_type(charger_enabled)
register_token_type(car_plugged)
register_token_type(electricity_price)

register_place(
    Place(
        name="Power company",
        description="Provides current electricity price",
        type="source",
        token_type=electricity_price,
    )
)

register_place(
    Place(
        name="Power charger (plug sensor)",
        description="Provides the status of the plug",
        type="source",
        token_type=car_plugged,
    )
)

register_place(
    Place(
        name="Power charger",
        description="Charge electric vehicles",
        type="sink",
        token_type=charger_enabled,
    )
)

register_place(
    Place(
        name="EV monitoring system (range)",
        description="Provides the remaining range in miles",
        type="source",
        token_type=remaining_range,
    )
)

system_prompt = instructions
prompt = """When the electricity price is below $0.4/kWh and my Tesla
is plugged, turn on charging."""

model = "~/.cache/py-llm-core/models/llama-3.1-8b"

with llm.LLamaCPP(model=model, n_ctx=8_000) as parser:
    workflow = parser.parse(
        data_class=Workflow,
        prompt=prompt,
        system_prompt=system_prompt,
    )
    print(workflow)
```



This prints the following result:

```python
Workflow(
    name="Workflow",
    query="When the electricity price is below $0.4/kWh and my Tesla is plugged, turn on charging.",
    transitions=[
        Transition(
            name="Turn on charging",
            state_change="Change",
            inputs=[
                InputArc(
                    place=Place(
                        name="Power company",
                        description="Provides current electricity price",
                        type="source",
                        token_type=TokenType(
                            name="electricity_price", type="FLOAT"
                        ),
                    ),
                    token_name="electricity_price",
                    transition="Turn on charging",
                ),
                InputArc(
                    place=Place(
                        name="Power charger (plug sensor)",
                        description="Provides the status of the plug",
                        type="source",
                        token_type=TokenType(name="car_plugged", type="BOOL"),
                    ),
                    token_name="car_plugged",
                    transition="Turn on charging",
                ),
            ],
            outputs=[
                OutputArc(
                    place=Place(
                        name="Power charger",
                        description="Charge electric vehicles",
                        type="sink",
                        token_type=TokenType(
                            name="charger_enabled", type="BOOL"
                        ),
                    ),
                    produce_token=TokenValue(
                        type=TokenType(name="charger_enabled", type="BOOL"),
                        value="True",
                    ),
                    transition="Turn on charging",
                )
            ],
            guard=[
                Guard(
                    name="Turn on charging",
                    conditions=[
                        Condition(
                            operator="LESS THAN",
                            value=TokenValue(
                                type=TokenType(
                                    name="electricity_price", type="FLOAT"
                                ),
                                value="0.4",
                            ),
                        ),
                        Condition(
                            operator="EQUAL",
                            value=TokenValue(
                                type=TokenType(
                                    name="car_plugged", type="BOOL"
                                ),
                                value="True",
                            ),
                        ),
                    ],
                    conditions_operator="AND",
                )
            ],
        )
    ],
)

```

Then we can generate a mermaid graph:

```python
from llm_tap.to_mermaid import workflow_to_mermaid

print(workflow_to_mermaid)
```

```plain
flowchart LR
    subgraph Sources
        Power_charger__plug_sensor_[Power_charger_#40;plug_sensor#41;<br/>car_plugged: BOOL]
        Power_company[Power_company<br/>electricity_price: FLOAT]
    end
    subgraph Sink
        Power_charger[Power_charger<br/>charger_enabled: BOOL]
    end
    subgraph Transitions
        Turn_on_charging[Turn on charging<br/>electricity_price LESS THAN 0.4 AND car_plugged EQUAL True]
    end
    Power_company -->|electricity_price| Turn_on_charging
    Power_charger__plug_sensor_ -->|car_plugged| Turn_on_charging
    Turn_on_charging -->|charger_enabled = True| Power_charger
```

[![](https://mermaid.ink/img/pako:eNp1U9FumzAU_RXr9pVmQCB13K1StnbaA2u2JntZmJADjrEGNjJGbZbk32egrULS-sXcc33OPT4WO0hVxoDAplCPaU61QdFDLJFddbPmmlY5WqhGp6zu0Xb9UI9MJ-1pbvekKhqe1EzWSierYe8icK-P2heBd_1xrT_cpFR3NM4ygj7P59GfM3VVVlRuV4Oq47KCpUaLVJhtUtmdEfQ1ms-WzxJMZqf-hfz7jvmh3d7as3Um6bo4sXeuvdRU1sIIJY_yWTZaJkr2skLyVQsgJdEL8PY9UHS3WKDlt9k9ckcBmt3foqOc0N3PX7PIDmzYqZtBRujy8mZ_pr0_MzWgvvWUndCRgfckTtGeN0wRfeqM74fzYgkOcC0yIMZ2HSiZLmlbwq7VjsHkrGQxEPtZCJ6bGGJ5sCR70d9KlS88rRqeA9nQorZVU2XUsFtB7ROVr6i2cTH9RTXSAPEn404EyA6egITuCE9dH2P3KpxiH_uBA1sg03Dk47F3hXEQuBN3PDk48K8ba8_bOvR9D3uh50790AGWCaP09_53SpXcCA6H_w-BIzU?type=png)](https://mermaid.live/edit#pako:eNp1U9FumzAU_RXr9pVmQCB13K1StnbaA2u2JntZmJADjrEGNjJGbZbk32egrULS-sXcc33OPT4WO0hVxoDAplCPaU61QdFDLJFddbPmmlY5WqhGp6zu0Xb9UI9MJ-1pbvekKhqe1EzWSierYe8icK-P2heBd_1xrT_cpFR3NM4ygj7P59GfM3VVVlRuV4Oq47KCpUaLVJhtUtmdEfQ1ms-WzxJMZqf-hfz7jvmh3d7as3Um6bo4sXeuvdRU1sIIJY_yWTZaJkr2skLyVQsgJdEL8PY9UHS3WKDlt9k9ckcBmt3foqOc0N3PX7PIDmzYqZtBRujy8mZ_pr0_MzWgvvWUndCRgfckTtGeN0wRfeqM74fzYgkOcC0yIMZ2HSiZLmlbwq7VjsHkrGQxEPtZCJ6bGGJ5sCR70d9KlS88rRqeA9nQorZVU2XUsFtB7ROVr6i2cTH9RTXSAPEn404EyA6egITuCE9dH2P3KpxiH_uBA1sg03Dk47F3hXEQuBN3PDk48K8ba8_bOvR9D3uh50790AGWCaP09_53SpXcCA6H_w-BIzU)

## Additional resources

Currently work in progress here: https://advanced-stack.com/resources/how-to-build-workflows-trigger-action-program-with-llms.html
