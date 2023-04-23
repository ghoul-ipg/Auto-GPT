from __future__ import annotations

import time

import openai
from colorama import Fore, Style
from openai.error import APIError, RateLimitError

from environments import OPEN_API_KEY, SMART_LLM_MODEL
from utils import get_logger

logger = get_logger(__name__)



openai.api_key = OPEN_API_KEY


def call_ai_function(
    function: str, args: list, description: str, model: str | None = None
) -> str:
    """Call an AI function

    This is a magic function that can do anything with no-code. See
    https://github.com/Torantulino/AI-Functions for more info.

    Args:
        function (str): The function to call
        args (list): The arguments to pass to the function
        description (str): The description of the function
        model (str, optional): The model to use. Defaults to None.

    Returns:
        str: The response from the function
    """
    if model is None:
        model = SMART_LLM_MODEL
    # For each arg, if any are None, convert to "None":
    args = [str(arg) if arg is not None else "None" for arg in args]
    # parse args to comma separated string
    args = ", ".join(args)
    messages = [
        {
            "role": "system",
            "content": f"You are now the following python function: ```# {description}"
            f"\n{function}```\n\nOnly respond with your `return` value.",
        },
        {"role": "user", "content": args},
    ]

    return create_chat_completion(model=model, messages=messages, temperature=0)


# Overly simple abstraction until we create something better
# simple retry mechanism when getting a rate error or a bad gateway
def create_chat_completion(
    messages: list,  # type: ignore
    model: str | None = None,
    temperature: float = 0,
    max_tokens: int | None = None,
) -> str:
    """Create a chat completion using the OpenAI API

    Args:
        messages (list[dict[str, str]]): The messages to send to the chat completion
        model (str, optional): The model to use. Defaults to None.
        temperature (float, optional): The temperature to use. Defaults to 0.9.
        max_tokens (int, optional): The max tokens to use. Defaults to None.

    Returns:
        str: The response from the chat completion
    """
    response = None
    num_retries = 10
    logger.debug(
        Fore.GREEN
        + f"Creating chat completion with model {model}, temperature {temperature},"
          f" max_tokens {max_tokens}" + Fore.RESET
    )
    for attempt in range(num_retries):
        backoff = 2 ** (attempt + 2)
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            break
        except RateLimitError:
            logger.debug(
                Fore.RED + "Error: " +
                f"Reached rate limit, passing..." + Fore.RESET,
            )
        except APIError as e:
            logger.exception(e)
            if e.http_status == 502:
                pass
            else:
                raise
            if attempt == num_retries - 1:
                raise
            logger.error("Error: API Bad gateway. Waiting {backoff} seconds...")
        time.sleep(backoff)
    if response is None:
        logger.error(
            "FAILED TO GET RESPONSE FROM OPENAI" +
            Fore.RED + "Auto-GPT has failed to get a response from OpenAI's services. "
            + f"Try running Auto-GPT again, and if the problem the persists try running it with `{Fore.CYAN}--debug{Fore.RESET}`.",
        )
        raise RuntimeError(f"Failed to get response after {num_retries} retries")
    return response.choices[0].message["content"]


def create_embedding_with_ada(text) -> list:
    """Create an embedding with text-ada-002 using the OpenAI SDK"""
    num_retries = 10
    for attempt in range(num_retries):
        backoff = 2 ** (attempt + 2)
        try:
            return openai.Embedding.create(
                input=[text], model="text-embedding-ada-002"
            )["data"][0]["embedding"]
        except RateLimitError:
            pass
        except APIError as e:
            if e.http_status == 502:
                pass
            else:
                raise
            if attempt == num_retries - 1:
                raise
        logger.debug(
            Fore.RED + "Error: " +
            f"API Bad gateway. Waiting {backoff} seconds..." + Fore.RESET,
        )
        time.sleep(backoff)
