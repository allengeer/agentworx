
import cmd
import os
import sys
from getpass import getpass
from typing import Annotated, Dict, Text

import rich  # Import MessagesState
from langchain.chat_models import init_chat_model
from langchain_core.rate_limiters import InMemoryRateLimiter
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from pynput import keyboard
from rich.console import Console, ConsoleOptions, Group, group
from rich.layout import Layout, LayoutRender, RenderMap
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty
from rich.prompt import Prompt
from rich.repr import Result, rich_repr
from rich.table import Table

from sengy.agent.sengy_graph import SengyGraph

from .config import get_llm


class HistoryConsole(Console):
    def __init__(self, history="session_history", key_bindings=None, *args, **kwargs):
        self.history = FileHistory(history)
        self.session = PromptSession(history=self.history, key_bindings=key_bindings)
        return super().__init__(*args, **kwargs)

    def input(
        self, prompt="", markup=True, emoji=True, password=False, stream=None
    ) -> str:
        if prompt:
            self.print(prompt, markup=markup, emoji=emoji, end="")
        if password:
            result = getpass("", stream=stream)
        else:
            if stream:
                result = stream.readline()
            else:
                result = self.session.prompt("")
        return result
    

@rich_repr
class ScrollableLayout(Layout):
    def __init__(self, renderable = None, *, name = None, size = None, minimum_size = 1, ratio = 1, visible = True, parent=None):
        super().__init__(renderable, name=name, size=size, minimum_size=minimum_size, ratio=ratio, visible=visible)
        self.scroll_y = 0
        self.scroll_x = 0
        self.fiddle = 10
        self.parent = parent

    def scroll_up(self):
        self.scroll_y = max(0, self.scroll_y-1)

    def scroll_down(self):
        content_height = sum(
            1
            for renderable in messages_group.renderables
            for segment in renderable.__rich_console__(console, console.options)
            if segment.text.find('\n') >= 0
        ) + self.fiddle
        self.scroll_y = min(max(content_height-self.parent._make_region_map(width=console.width, height=console.height).get(self).height+4, 0), self.scroll_y+1)
    
    def scroll_bottom(self):
        content_height = sum(
            1
            for renderable in messages_group.renderables
            for segment in renderable.__rich_console__(console, console.options)
            if segment.text.find('\n') >= 0
        )   + self.fiddle
        self.scroll_y = max(0, content_height-self.parent._make_region_map(width=console.width, height=console.height).get(self).height+4)

llm = get_llm()
bindings = KeyBindings()
console = HistoryConsole(key_bindings=bindings)

rate_limiter = InMemoryRateLimiter(
    requests_per_second=5,  # <-- Super slow! We can only make a request once every 10 seconds!!
    check_every_n_seconds=0.1,  # Wake up every 100 ms to check whether allowed to make a request,
    max_bucket_size=10,  # Controls the maximum burst size.
)

layout = Layout(name="root")
layout.split_column(
    Layout(Text(" "),name="header", size=3),
    Layout(name="body", ratio=1)
)

layout["body"].split_row(
    Layout(name="chats", size=25),
    ScrollableLayout(name="active_chat", ratio=1, parent=layout)
)
scrollable_layout = layout["active_chat"]

chats = [{"id": "1", "name": "New Chat", "thread_id": None}]
active_chat = chats[0]

messages_group = Group(Panel("Waiting for messages..."))
new_chat = True
layout["active_chat"].update(Panel(messages_group, title="Active Chat", border_style="green"))

def add_message_to_log(message: Panel):
    """Add a message to the messages log."""
    global messages_group, new_chat
    
    if new_chat:
        messages_group.renderables.clear()  # Clear previous messages in the group
        new_chat = False
    messages_group.renderables.append(message)
    scrollable_layout.scroll_bottom()
    console.print(layout)  # Update the console with the new message

def get_chats_table() -> Table:
    """Create a table to display chats."""
    from rich.table import Table

    chats_table = Table(title="Chats")
    chats_table.add_column("Chat ID", justify="left", style="cyan")
    chats_table.add_column("Chat Name", justify="left", style="magenta")
    for chat in chats:
        chats_table.add_row(chat["id"], chat["name"], style="bold" if chat == active_chat else "dim")
    return chats_table



@bindings.add('s-up')
def _(event):
    scrollable_layout.scroll_up()
    console.print(layout)
@bindings.add('s-down')
def _(event):
    scrollable_layout.scroll_down()
    console.print(layout)
@bindings.add('c-s-down')
def _(event):
    scrollable_layout.fiddle += 10
    scrollable_layout.scroll_down()
    console.print(layout)

with Live(layout, refresh_per_second=1) as live:
    
    layout["chats"].update(get_chats_table())
    console.print(layout)
    # listener= keyboard.Listener(on_press=on_press)
    # listener.start()
    # listener.join()

# layout["input"].update(Panel(Prompt.ask("Enter your message: ", default="Can you review Heiner León assigned tickets from the last 9 months in the NIFI project and summarise them in terms of technology areas and major issues?"), title="Input", border_style="blue"))


sengy_graph = SengyGraph(llm=llm)
sengy_graph.build_graph()
config = {"recursion_limit": 50, "configurable": {"thread_id" : "1", "shared_data": {}}}
# inputs = {"input": "Can you completely review all information available on SPARK-47759 and summarize"}
# inputs = {"input": "Can you review Heiner León assigned tickets from the last 9 months in the NIFI project and summarise them in terms of technology areas and major issues?"}
# Get Initial Arguments


def get_human_input():
    """Get human input from the console."""
    if not active_chat.get("thread_id"):
        return console.input("What would you like to ask? ")
    else:
        return console.input("What would you like to ask? ")

def stream_llm(human_input: str):
    global sengy_graph
    add_message_to_log(Panel(human_input, title="User Input", border_style="blue"))
    if not active_chat.get("thread_id"):
        active_chat["thread_id"] = config["configurable"]["thread_id"]
    if active_chat.get("thread_id") != config["configurable"]["thread_id"]:
        config["configurable"]["thread_id"] = active_chat["thread_id"]
    for type, event in sengy_graph.graph.stream({"input": human_input}, config=config, stream_mode=['custom', 'updates']):
        if isinstance(event, dict):        
            for node_name, node_response in event.items():
                if "response" in node_response and node_response['response']:
                    add_message_to_log( Panel(Markdown(node_response['response'], code_theme="lightbulb", hyperlinks=True), title=f"{node_name}") )
                elif "final_response" in node_response and node_response['final_response']:
                    add_message_to_log( Panel(Markdown(node_response['final_response'], code_theme="lightbulb", hyperlinks=True), title=f"{node_name}") )
                elif "plan" in node_response:
                    add_message_to_log( Panel(Pretty(node_response['plan']), title=f"{node_name}"))
                elif "past_steps" in node_response:
                    add_message_to_log( Panel(Pretty(node_response['past_steps']), title=f"{node_name}"))
                elif "custom_data" == node_name:
                    add_message_to_log( Panel(str(node_response), title="TOOL", border_style="bold yellow"))
                else:
                    add_message_to_log( Panel(Pretty(node_response), title=f"{node_name}", border_style="bold red"))
        else:
            add_message_to_log(Panel(str(event), title="Unknown Event", border_style="bold red"))

args = sys.argv[1:]
while True:
    console.print(layout)
    if not args: 
        human_input = get_human_input()
    else:
        human_input = " ".join(args)
    if human_input.lower() == "exit" or human_input.lower() == "quit":
        console.print("Exiting the chat. Goodbye!")
        break
    elif human_input.lower() == "help":
        console.print("Available commands:\n- EXIT: Exit the chat\n- HELP: Show this help message\n NEWCHAT - Create a new chat")
    elif human_input.lower() == "newchat":
        chats.append({"id": str(len(chats) + 1), "name": f"New Chat"})
        active_chat = chats[-1]
        messages_group.renderables.clear()
        add_message_to_log(Panel("Waiting for messages..."))
        new_chat = True
    elif human_input.lower() == "su":
        scrollable_layout.scroll_up()
        console.print(layout)
    elif human_input.lower() == "sd":
        scrollable_layout.scroll_down()
        console.print(layout)
    else:
        stream_llm(human_input)
        args = None
        console.print(layout)
