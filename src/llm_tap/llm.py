# -*- coding: utf-8 -*-
import time
import os
import copy
import typing
import types
import json
import logging

from functools import lru_cache
from inspect import isclass
from enum import Enum, StrEnum
from textwrap import dedent

from dataclasses import (
    make_dataclass,
    dataclass,
    asdict,
    fields,
    is_dataclass,
    MISSING,
)

import requests
import llama_cpp
from contextlib import redirect_stdout, redirect_stderr


class_names_mapping = {}
logger = logging.getLogger(__name__)


def serialize(obj):
    if isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, list):
        return [serialize(i) for i in obj]
    elif isinstance(obj, tuple):
        return [serialize(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    elif is_dataclass(obj):
        return serialize(asdict(obj))
    else:
        return obj


@lru_cache
def convert_field(cls, field):
    class_name = cls.__name__
    field_type = field.type

    mapping = {
        int: {"type": "integer"},
        str: {"type": "string"},
        bool: {"type": "boolean"},
        float: {"type": "number"},
        complex: {"type": "string", "format": "complex-number"},
        bytes: {"type": "string", "contentEncoding": "base64"},
    }

    if field_type is type and callable in field.metadata:
        caller_fn = field.metadata.get(callable)

        if caller_fn is None:
            raise ValueError("No callable defined.")

        actual_type = caller_fn()

        if isinstance(actual_type, (list, tuple)):
            actual_type = actual_type[0]

        new_field = copy.copy(field)
        object.__setattr__(new_field, "type", actual_type)
        return convert_field(cls, new_field)

    elif "choices" in field.metadata:
        choices = field.metadata["choices"]

        if callable(choices):
            choices = choices()

        return {
            "oneOf": [to_const_json_schema(c) for c in choices],
            "description": f"One of: {choices}",
        }

    if field_type in mapping:
        return mapping[field_type]
    else:
        if is_dataclass(field_type):
            return to_json_schema(field_type)

        elif (
            hasattr(field_type, "__origin__")
            and field_type.__origin__ is typing.Union
        ) or isinstance(field_type, types.UnionType):
            available_types = field_type.__args__
            augmented_types = [
                make_dataclass(
                    f"Choice{_cls.__name__}",
                    [
                        (
                            "name",
                            StrEnum(f"Enum{_cls.__name__}", [_cls.__name__]),
                        ),
                        ("arguments", _cls),
                    ],
                )
                for _cls in available_types
            ]

            return {"anyOf": [to_json_schema(t) for t in augmented_types]}

        elif isinstance(field_type, types.GenericAlias):
            container_type = field_type.__origin__
            items_type = field_type.__args__

            if len(items_type) != 1:
                raise NotImplementedError(
                    f"Annotation not supported for {field_type}[{items_type}]"
                )

            items_type = items_type[0]

            if is_dataclass(items_type):
                items = to_json_schema(items_type)
            else:
                items = convert_field(cls, items_type)

            container_mapping = {
                list: {"type": "array", "items": items},
                tuple: {"type": "array", "items": items},
                dict: {"type": "object", "additionalProperties": items},
                set: {"type": "array", "uniqueItems": True, "items": items},
                frozenset: {
                    "type": "array",
                    "uniqueItems": True,
                    "items": items,
                },
            }
            return container_mapping[container_type]

        elif isclass(field_type) and issubclass(field_type, Enum):
            return {
                "type": "string",
                "enum": list(field_type.__members__.keys()),
            }

        elif type(field_type) is str:
            if field_type == class_name:
                return {"$ref": "#"}
            else:
                raise ValueError(f"Unknown field type: {field_type}")

        else:
            return {
                "type": "object",
            }


def to_const_json_schema(instance):
    """
    Recursively turns a dataclass instance into a JSON Schema dict with all attributes as const.
    """
    if is_dataclass(instance):
        class_names_mapping[instance.__class__.__name__] = instance.__class__
        properties = {"_type": {"const": type(instance).__name__}}
        required = ["_type"]
        for field in fields(instance):
            value = getattr(instance, field.name)
            properties[field.name] = to_const_json_schema(value)
            required.append(field.name)
        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }
    elif isinstance(instance, Enum):
        return {"const": instance.value}
    elif isinstance(instance, list):
        return {
            "type": "array",
            "items": [to_const_json_schema(v) for v in instance],
        }
    elif isinstance(instance, dict):
        # frozen dict: all keys/values as const
        return {
            "type": "object",
            "properties": {
                k: to_const_json_schema(v) for k, v in instance.items()
            },
            "required": list(instance.keys()),
        }
    else:
        return {"const": instance}


@lru_cache
def to_json_schema(data_class):
    properties = {}
    required_fields = []

    class_names_mapping[data_class.__name__] = data_class

    for f in fields(data_class):
        properties[f.name] = convert_field(data_class, f)

        no_default = f.default == MISSING
        no_default_factory = f.default_factory == MISSING
        required = no_default and no_default_factory

        if required:
            required_fields.append(f.name)

    data_class_name = data_class.__name__
    data_class_docstring = dedent(data_class.__doc__).strip()

    schema = {
        "type": "object",
        "title": data_class_name,
        "description": data_class_docstring,
        "properties": properties,
        "required": required_fields,
    }
    logger.debug(f"{data_class.__name__} => {schema}")
    return schema


def from_dict(cls, attrs):
    containers = (
        list,
        tuple,
        set,
        frozenset,
    )
    if isinstance(cls, str):
        cls = class_names_mapping.get(cls)
        if cls is None:
            raise ValueError(f"Unknown class name: {cls}")

    if isinstance(attrs, dict) and "_type" in attrs:
        logger.debug(f"Hydrating {attrs}...")
        type_ = attrs["_type"]
        concrete_cls = class_names_mapping[type_]
        attrs = dict(attrs)
        del attrs["_type"]
        return from_dict(concrete_cls, attrs)

    if is_dataclass(cls):
        field_types = {f.name: f.type for f in fields(cls)}
        return cls(
            **{k: from_dict(field_types[k], v) for k, v in attrs.items()}
        )

    elif (
        isinstance(cls, types.UnionType)
        or hasattr(cls, "__origin__")
        and cls.__origin__ is typing.Union
    ):
        try:
            target_cls = next(
                filter(
                    lambda target_cls: target_cls.__name__ == attrs["name"],
                    cls.__args__,
                )
            )
        except StopIteration:
            raise KeyError(f"Class {attrs['name']} not found")

        instance = target_cls(**attrs["arguments"])

        return instance

    elif hasattr(cls, "__origin__") and cls.__origin__ in containers:
        return cls.__origin__([from_dict(cls.__args__[0], v) for v in attrs])

    elif hasattr(cls, "__name__") and cls.__name__ == "list":
        return [from_dict(cls.__args__[0], v) for v in attrs]

    elif hasattr(cls, "__name__") and cls.__name__ == "set":
        return set([from_dict(cls.__args__[0], v) for v in attrs])

    elif isclass(cls) and issubclass(cls, Enum):
        return getattr(cls, attrs)

    else:
        return attrs


def as_tool(json_schema):
    return {
        "type": "function",
        "function": {
            "name": json_schema["title"],
            "description": json_schema["description"],
            "parameters": json_schema,
        },
    }


def as_tool_choice(json_schema):
    return {"type": "function", "function": {"name": json_schema["title"]}}


@lru_cache
def make_helper(data_class):
    class_name = f"name: {data_class.__name__}"
    class_description = f"description: {dedent(data_class.__doc__.strip())}"

    inputs_schema = []

    for f in fields(data_class):
        field_name = f.name
        field_type_name = getattr(
            f.type, "__name__", getattr(f.type, "_name", "")
        )
        is_required = f.default == MISSING and f.default_factory == MISSING
        requirement_status = "(required)" if is_required else ""
        field_representation = (
            f"{field_name} ({field_type_name}) {requirement_status}"
        )
        inputs_schema.append(field_representation)

    formatted_inputs_schema = "\n".join(inputs_schema)

    helper_description = "\n".join(
        (class_name, class_description, "inputs:", formatted_inputs_schema)
    )

    return helper_description


@lru_cache
def prepare(data_class=None, prompt="", system_prompt="", model=None):
    payload = {
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.0,
    }

    if data_class is not None:
        data_class_schema = to_json_schema(data_class)
        data_class_tool = as_tool(data_class_schema)
        data_class_tool_choice = as_tool_choice(data_class_schema)
        data_class_helper = make_helper(data_class)
        prompt = "\n\n".join((data_class_helper, prompt))

        payload.update(
            {
                "tools": [data_class_tool],
                "tool_choice": data_class_tool_choice,
                "parallel_tool_calls": False,
            }
        )

    if model is not None:
        payload.update({"model": model})

    return payload


def parse_response(attributes, data_class=None):
    logger.debug(f"LLM response: {attributes}")

    msg = attributes["choices"][0]["message"]

    if data_class and "tool_calls" in msg:
        tool_call = msg["tool_calls"][0]
        arguments_json = tool_call["function"]["arguments"]
        arguments_dict = json.loads(arguments_json)

        instance = from_dict(data_class, arguments_dict)
        return instance

    return msg["content"]


@dataclass
class HTTP:
    """
    OpenAI API Compatible adapter using `requests` library.
    """

    base_url: str = os.getenv("ENDPOINT")
    api_key: str = os.getenv("API_KEY")
    model: str = os.getenv("DEFAULT_MODEL")

    def __post_init__(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "api-key": f"{self.api_key}",
        }
        self.session = requests.Session()
        self.session.headers.update(headers)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def generate(self, prompt="", system_prompt="You are a helpful assistant"):
        payload = prepare(None, prompt, system_prompt)
        response = self.session.post(self.base_url, json=payload)

        try:
            response.raise_for_status()
        except Exception as e:
            if response.status_code == 429:
                time.sleep(10)
                return self.generate(prompt, system_prompt)
            print(response.json())
            raise e
        attributes = response.json()

        return parse_response(attributes)

    def parse(self, data_class, prompt="", system_prompt="Answer in JSON"):
        payload = prepare(data_class, prompt, system_prompt, self.model)
        response = self.session.post(self.base_url, json=payload)
        try:
            response.raise_for_status()
        except Exception as e:
            if response.status_code == 429:
                time.sleep(10)
                return self.parse(data_class, prompt)
            print(response.json())
            raise e
        attributes = response.json()
        return parse_response(attributes, data_class)


@dataclass
class LLamaCPP:
    """
    llama.cpp wrapper using llama-cpp-python
    """

    model: str = "/path/to/any/gguf/model"
    n_ctx: int = 4_000
    n_gpu_layers: int = 100
    n_threads: int = 1

    def __post_init__(self):
        self.model_path = os.path.expanduser(self.model)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def generate(self, prompt="", system_prompt="You are a helpful assistant"):
        payload = prepare(None, prompt, system_prompt)

        with open(os.devnull, "w") as fnull:
            with redirect_stdout(fnull), redirect_stderr(fnull):
                self._llm = llama_cpp.Llama(
                    self.model_path,
                    n_ctx=self.n_ctx,
                    n_gpu_layers=self.n_gpu_layers,
                    n_threads=self.n_threads,
                    verbose=False,
                )

                response = self._llm.create_chat_completion(
                    messages=payload["messages"],
                )
                del self._llm
        return parse_response(response)

    def parse(self, data_class, prompt="", system_prompt="Answer in JSON"):
        payload = prepare(data_class, prompt, system_prompt)

        with open(os.devnull, "w") as fnull:
            with redirect_stdout(fnull), redirect_stderr(fnull):
                self._llm = llama_cpp.Llama(
                    self.model_path,
                    n_ctx=self.n_ctx,
                    n_gpu_layers=self.n_gpu_layers,
                    n_threads=self.n_threads,
                    verbose=False,
                )

                response = self._llm.create_chat_completion(
                    messages=payload["messages"],
                    temperature=payload["temperature"],
                    tools=payload["tools"],
                    tool_choice=payload["tool_choice"],
                )
                del self._llm
        return parse_response(response, data_class)
