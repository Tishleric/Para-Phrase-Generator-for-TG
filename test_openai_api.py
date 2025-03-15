import os
from dotenv import load_dotenv
import json
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get API key from .env
api_key = os.environ.get("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

def test_chat_completion():
    """Test basic chat completion API."""
    print("Testing Chat Completion API...")
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, how are you?"}]
        )
        print(f"SUCCESS: Received response from {response.model}")
        print(f"Message: {response.choices[0].message.content}")
        print()
    except Exception as e:
        print(f"ERROR: Chat completion failed: {str(e)}")
        print()

def test_tools_with_chat():
    """Test using tools with chat completions API."""
    print("Testing Chat Completions with tools...")
    try:
        # Define available tools
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the current weather in a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
        
        # Make the API call
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "What's the weather like in Paris?"}],
            tools=tools
        )
        
        print(f"SUCCESS: Chat completions with tools working")
        
        # Check if the model wants to call a tool
        if response.choices[0].message.tool_calls:
            tool_calls = response.choices[0].message.tool_calls
            print(f"Tool calls: {json.dumps(tool_calls, default=str)}")
        else:
            print(f"Response without tool calls: {response.choices[0].message.content[:100]}...")
        
        print()
    except Exception as e:
        print(f"ERROR: Chat completions with tools failed: {str(e)}")
        print()

def test_image_analysis():
    """Test image analysis capabilities."""
    print("Testing Image Analysis...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image_url", "image_url": {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
                    }}
                ]}
            ]
        )
        print(f"SUCCESS: Image analysis working")
        print(f"Description: {response.choices[0].message.content[:150]}...")  # Show first 150 chars
        print()
    except Exception as e:
        print(f"ERROR: Image analysis failed: {str(e)}")
        print()

def main():
    """Run all tests."""
    print(f"Testing OpenAI API with key: {api_key[:5]}...{api_key[-5:]}")
    print("-" * 80)
    
    # Run tests
    test_chat_completion()
    test_tools_with_chat()
    test_image_analysis()
    
    print("All tests completed.")

if __name__ == "__main__":
    main() 