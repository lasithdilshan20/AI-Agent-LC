"""
LLM-Powered Utility Agent

This script implements an end-to-end LLM-powered agent using the OpenAI Assistants API.
The agent can look up weather information for cities and get stock prices for ticker symbols.
"""

import os
import sys
import requests
import json
from typing import Callable, TypeVar, cast, get_type_hints
from dotenv import load_dotenv
from openai import OpenAI

# Define a type variable for the return type of the function
T = TypeVar('T')

# Define function_tool decorator
def function_tool(func: Callable[..., T]) -> Callable[..., T]:
    """
    A decorator that marks a function as a tool for the OpenAI Assistant.
    This is a simplified version that just returns the function as-is.
    The actual tool definition will be created separately.
    """
    return func

# Load environment variables from .env file
load_dotenv()

# Check if OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY environment variable not set.")
    print("Please set it in your .env file or environment variables.")
    sys.exit(1)

# Initialize OpenAI client
client = OpenAI()

@function_tool
def get_weather(city: str) -> str:
    """
    Get the current weather for a specified city.

    Args:
        city: The name of the city to get weather information for

    Returns:
        A string containing the current weather information
    """
    try:
        # Using OpenWeatherMap free API
        api_key = "da0f9c8d90bde7e619c3ec47766a42f4"  # Free API key for demo purposes
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()
        weather_description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        return (
            f"Weather in {city}: {weather_description}. "
            f"Temperature: {temperature}°C, "
            f"Humidity: {humidity}%, "
            f"Wind Speed: {wind_speed} m/s"
        )
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {str(e)}"
    except (KeyError, IndexError) as e:
        return f"Error parsing weather data: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@function_tool
def get_stock_price(ticker: str) -> str:
    """
    Get the current stock price for a specified ticker symbol.

    Args:
        ticker: The stock ticker symbol (e.g., AAPL for Apple)

    Returns:
        A string containing the current stock price information
    """
    try:
        # Using Alpha Vantage free API
        api_key = "DEMO_KEY"  # Using demo key for Alpha Vantage
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={api_key}"

        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()

        # Check if we got valid data
        if "Global Quote" not in data or not data["Global Quote"]:
            return f"Could not find stock information for ticker: {ticker}"

        quote = data["Global Quote"]
        price = quote.get("05. price", "N/A")
        change = quote.get("09. change", "N/A")
        change_percent = quote.get("10. change percent", "N/A")

        return (
            f"Stock information for {ticker}: "
            f"Current Price: ${price}, "
            f"Change: {change} ({change_percent})"
        )
    except requests.exceptions.RequestException as e:
        return f"Error fetching stock data: {str(e)}"
    except KeyError as e:
        return f"Error parsing stock data: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def main():
    """
    Main function to set up and run the agent.
    """
    # Create function definitions for the OpenAI Assistant
    weather_tool = {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a specified city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city to get weather information for"
                    }
                },
                "required": ["city"]
            }
        }
    }

    stock_tool = {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get the current stock price for a specified ticker symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "The stock ticker symbol (e.g., AAPL for Apple)"
                    }
                },
                "required": ["ticker"]
            }
        }
    }

    # Create an assistant with the tools
    assistant = client.beta.assistants.create(
        name="UtilityAgent",
        description="An agent that can look up weather information and stock prices.",
        instructions="""
        You are a helpful assistant that can look up weather information for cities and stock prices for ticker symbols.

        - When asked about weather in a city, call the get_weather function with the city name.
          - If the city name appears to be misspelled, suggest the correct spelling and respond with "I think you meant [correct city]. Please try asking about that city instead."
          - Only call the function with valid city names.
        - When asked about a stock price, call the get_stock_price function with the ticker symbol.
          - Only call the function with valid ticker symbols.
        - For general questions like "How are you?", "Hello", etc., respond with "I'm a utility agent that can help you with weather and stock prices. How can I assist you today?"
        - For any other queries, respond with "I'm sorry, I can only look up weather and stock prices. Please ask me about the weather in a city or the price of a stock."

        Always be polite and concise in your responses. Do not call functions with invalid inputs.
        """,
        model="gpt-3.5-turbo",
        tools=[weather_tool, stock_tool]
    )

    # Create a thread for the conversation
    thread = client.beta.threads.create()

    print("Welcome to the Utility Agent!")
    print("You can ask about weather (e.g., 'What's the weather in London?')")
    print("Or stock prices (e.g., 'What's the current price of AAPL?')")
    print("Type 'exit' to quit.")
    print("-" * 50)

    # Main interaction loop
    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            # Add the user message to the thread
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_input
            )

            # Run the assistant on the thread
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id
            )

            # Wait for the run to complete with a timeout
            max_attempts = 30  # 30 seconds timeout
            attempts = 0
            while attempts < max_attempts:
                attempts += 1
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )

                if run_status.status == "completed":
                    break
                elif run_status.status == "requires_action":
                    # Handle tool calls
                    tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = []

                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        if function_name == "get_weather":
                            output = get_weather(function_args["city"])
                        elif function_name == "get_stock_price":
                            output = get_stock_price(function_args["ticker"])
                        else:
                            output = f"Error: Unknown function {function_name}"

                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": output
                        })

                    # Submit the tool outputs
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                elif run_status.status in ["failed", "cancelled", "expired"]:
                    error_message = f"Run {run_status.status}"
                    if hasattr(run_status, 'last_error') and run_status.last_error:
                        error_message += f": {run_status.last_error}"
                    print(f"\nError: {error_message}")

                    # Add a fallback response so the conversation can continue
                    client.beta.threads.messages.create(
                        thread_id=thread.id,
                        role="assistant",
                        content="I'm sorry, I encountered an error processing your request. For weather queries, please provide a valid city name (e.g., 'What's the weather in London?'). For stock queries, please provide a valid ticker symbol (e.g., 'What's the price of AAPL?'). I can only help with weather and stock information."
                    )
                    break

                # Wait a moment before checking again
                import time
                time.sleep(1)

            # Handle timeout case
            if attempts >= max_attempts:
                print("\nError: Request timed out after 30 seconds")

                # Add a timeout message to the thread
                client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="assistant",
                    content="I'm sorry, but your request is taking longer than expected to process. Please try again with a simpler query or check your internet connection."
                )

            # Get the assistant's response
            messages = client.beta.threads.messages.list(
                thread_id=thread.id
            )

            # Print the latest assistant message
            assistant_message_found = False
            for message in messages.data:
                if message.role == "assistant":
                    try:
                        print(f"\nAgent: {message.content[0].text.value}")
                        assistant_message_found = True
                        break
                    except (IndexError, AttributeError) as e:
                        print(f"\nError retrieving assistant message: {str(e)}")
                        break

            # If no assistant message was found, provide a fallback
            if not assistant_message_found:
                print("\nAgent: I'm sorry, I couldn't generate a proper response. Please try again with a different query.")

        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Please try again.")

if __name__ == "__main__":
    main()
