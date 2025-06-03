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

[![](https://mermaid.ink/img/pako:eNp1U1Fv2jAQ_ivW9TVlIZhi3K0SWzvtISvbYC8jU2SSa7Ca2JHjqGPAf5-TtBOB1i_n-87fd5_P8g4SnSJweMj1U7IRxpLwR6SIW1W9zowoN2Sha5Ng1aHN-qaf0MTN6czFuMzrLK5QVdrEq37tgvrXR-ULOrx-vzbvbhJhWlqGKScf5_Pw95m6Lkqhtqte1nIxx8QamUi7jUsXkZPP4Xy2fJZAlZ76l-rxDfN9u521Z-uoxDo_sXeuvTRCVdJKrY7ms6yNirXqZKXKVg1AtCIvwOv3IOHdYkGWX2b3xB9QMru_JUdzInfff85C17DGUze9GZHLy5v9mfb-zFSP-tpTtkJHBt6SOEU7Xn-K5ENrfN_vFynwIDMyBW5d1YMCTSGaFHaNdgR2gwVGwN02FeYxgkgdHMfd85fWxQvN6DrbAH8QeeWyukyFxVsp3AsV_1HjpoXmk66VBR6MJq0I8B38AT72B2zqB4z5k_GUBSygHmyBT8eDgI2GE8Yo9a_80dXBg79tW3fe5eMgoHREAzZlQw8wlVabr91vaj_V4R-KQCHw?type=png)](https://mermaid.live/edit#pako:eNp1U1Fv2jAQ_ivW9TVlIZhi3K0SWzvtISvbYC8jU2SSa7Ca2JHjqGPAf5-TtBOB1i_n-87fd5_P8g4SnSJweMj1U7IRxpLwR6SIW1W9zowoN2Sha5Ng1aHN-qaf0MTN6czFuMzrLK5QVdrEq37tgvrXR-ULOrx-vzbvbhJhWlqGKScf5_Pw95m6Lkqhtqte1nIxx8QamUi7jUsXkZPP4Xy2fJZAlZ76l-rxDfN9u521Z-uoxDo_sXeuvTRCVdJKrY7ms6yNirXqZKXKVg1AtCIvwOv3IOHdYkGWX2b3xB9QMru_JUdzInfff85C17DGUze9GZHLy5v9mfb-zFSP-tpTtkJHBt6SOEU7Xn-K5ENrfN_vFynwIDMyBW5d1YMCTSGaFHaNdgR2gwVGwN02FeYxgkgdHMfd85fWxQvN6DrbAH8QeeWyukyFxVsp3AsV_1HjpoXmk66VBR6MJq0I8B38AT72B2zqB4z5k_GUBSygHmyBT8eDgI2GE8Yo9a_80dXBg79tW3fe5eMgoHREAzZlQw8wlVabr91vaj_V4R-KQCHw)

## Additional resources

Currently work in progress here: https://advanced-stack.com/resources/how-to-build-workflows-trigger-action-program-with-llms.html
