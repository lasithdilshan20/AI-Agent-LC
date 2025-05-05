# LLM-Powered Utility Agent

This project implements an end-to-end LLM-powered agent using the OpenAI Agents SDK. The agent can look up weather information for cities and get stock prices for ticker symbols.

## Setup Instructions

### 1. Create and activate a virtual environment

#### On Windows:
```
python -m venv venv
venv\Scripts\activate
```

#### On macOS/Linux:
```
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Set up your OpenAI API key

Create a `.env` file in the project root directory based on the provided `.env.example` file:
```
cp .env.example .env
```

Edit the `.env` file and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

### 4. Run the agent
```
python main.py
```

## Usage

Once the agent is running, you can ask it about:
- Weather information for a city (e.g., "What's the weather in London?")
- Stock prices for ticker symbols (e.g., "What's the current price of AAPL?")

Type "exit" to quit the application.
