# LLM TAP (Trigger-Action Programs)

`llm-tap` is a lightweight and extensible library to generate workflows using Large Language Models (LLMs). `llm-tap` provides mechanisms and data structures to generate workflows and constraints for any existing workflow engine.

`llm-tap` is *not* a workflow library but should be used to design a workflow generator with LLMs.

## Installation

Installation shall be done from source to build a local package. This requirement is tied to a customized version of `llama-cpp-python`.

```
https://github.com/advanced-stack/llama-cpp-python.git
Branch: feature/ranking
```

To build a package:

```
git clone https://github.com/advanced-stack/llm-tap.git

cd llm-tap
make setup
make build  # build a redistribuable package for llm-tap in ./dist/
```


Then you can pip install in your project:

```
pip install /path/to/llm-tap/dist/llm_tap-0.2.0.tar.gz
```


## Example project using llm-tap

See [https://github.com/NuCoreAI/ai-workflow/](https://github.com/NuCoreAI/ai-workflow/)



## Additional resources

Currently work in progress here: https://advanced-stack.com/resources/how-to-build-workflows-trigger-action-program-with-llms.html
