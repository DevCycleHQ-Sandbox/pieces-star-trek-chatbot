from dotenv import load_dotenv
from devcycle_python_sdk import DevCycleLocalClient, DevCycleLocalOptions
from devcycle_python_sdk.models.user import DevCycleUser
from openfeature import api
from openfeature.evaluation_context import EvaluationContext
from pieces_os_client.api.conversation_messages_api import ConversationMessagesApi
from pieces_os_client.wrapper import PiecesClient
import os
import time
import shutil
import pieces_os_client
import pyfiglet
from rich.console import Console
from rich.rule import Rule
from rich import print as rich_print

# Load environment variables
load_dotenv()

devcycle_key = os.getenv("DEVCYCLE_SERVER_SDK_KEY")

# configure your options
options = DevCycleLocalOptions()

# Initialize DevCycle client and set it as the OpenFeature provider
devcycle_client = DevCycleLocalClient(devcycle_key, options)

# Set OpenFeature Provider and get client
api.set_provider(devcycle_client.get_openfeature_provider())
open_feature_client = api.get_client()


# wait for devcycle_client to initialize
for i in range(0, 10):
    if devcycle_client.is_initialized():
        break
    time.sleep(0.5)
# Create user context
context = EvaluationContext(
    targeting_key='your-user-id',
)

# Retrieve customizable prompt from DevCycle
try:
    # Fetch the system prompt variable using the identifier key, with a default value and context
    # The default value can be of type string, boolean, number, or JSON
    system_prompt = open_feature_client.get_string_value(
        "system-prompt",
        "You are an unhelpful copilot. Respond in the style of Q from Star Trek the Next Generation.",
        context
    )
except Exception as e:
    print(f"Exception when retrieving 'system-prompt' from DevCycle: {e}")

# Retrieve model name from DevCycle
try:
    # Fetch the model name variable using the identifier key, with a default value and context
    model_name = open_feature_client.get_string_value(
        "model",
        "GPT-4o Chat Model",
        context
    )
except Exception as e:
    print(f"Exception when retrieving 'model' from DevCycle: {e}")


# Initialize the Pieces client and set up the chat session
pieces_client = PiecesClient()
conversation_messages_api = ConversationMessagesApi(
    pieces_client)  # Initialize the messages API

# Start a new chat session
chat = pieces_client.copilot.create_chat()
conversation_id = chat.conversation.id  # Retrieve the conversation ID
chat.name = "Star Trek Co-Pilot Chat"  # Assign a name to the chat session
pieces_client.model_name = model_name  # Set the model name for Pieces client

# Prepare the system prompt as an initial message for the chat
with pieces_os_client.api_client.ApiClient() as api_client:
    # Initialize the API client instance for sending messages
    api_instance = ConversationMessagesApi(api_client)

    # Create and send the initial system prompt message
    system_prompt_message = {
        'role': 'SYSTEM',
        'fragment': {
            'string': {
                'raw': system_prompt,  # System prompt message content
            },
        },
        # Associate with the chat session
        'conversation': {'id': conversation_id},
    }

    # Send the system prompt message to initialize the conversation
    api_instance.messages_create_specific_message(
        seeded_conversation_message=system_prompt_message)

# Create console for styled printing
console = Console()


def show_intro_message():
    """Displays a centered, styled intro message using ASCII art."""
    font = pyfiglet.Figlet(
        font="standard")  # Use the desired font, e.g., 'standard' or 'starwars'
    ascii_art = font.renderText("Greetings, Captain!")

    # Get the width of the console
    console_width = shutil.get_terminal_size().columns

    # Center each line of the ASCII art
    centered_ascii_art = "\n".join(line.center(
        console_width) for line in ascii_art.splitlines())

    # Print centered ASCII art in yellow
    rich_print(f"[yellow]{centered_ascii_art}[/yellow]")

    # Print a centered ruled line
    console.print(Rule(style="yellow"))


def ask_question_and_stream_answer(client, question):
    """Streams each chunk of the response to a question from the client."""
    for response in client.copilot.stream_question(question):
        if response.question:
            for answer in response.question.answers.iterable:
                print(answer.text, end="")  # Stream answer chunks inline
    print("\n" * 2)


# Show intro message
show_intro_message()

ask_question_and_stream_answer(pieces_client, "Hello, who are you?")

# Interactive conversation loop; exits on "goodbye"
while True:
    question = input(": ")
    if question.strip().lower() == "goodbye":
        break
    ask_question_and_stream_answer(pieces_client, question)

pieces_client.close()  # Clean up resources when done
