
import re
import streamlit as st

from core.chat_database import ChatDatabase
from modules.ai.context_engine import ContextAwareNOVAEngine
from modules.ai.ollama_client import OllamaClient


SYSTEM_PROMPT = (
    "You are NOVA, a helpful personal AI assistant. "
    "Be friendly, intelligent, clear, and concise. "
    "Help with programming, gaming, studies, productivity, "
    "technology, and everyday questions. "
    "Use simple explanations when appropriate. "
    "Never claim to have performed an action unless it "
    "was actually performed. "
    "Do not invent messages from the user. "
    "Never write fake User messages or continue the conversation "
    "transcript. "
    "Do not prefix replies with NOVA: or Assistant:. "
    "Respond to the latest user message using previous messages "
    "as context."
)


def initialize_ai():
    if "nova_chat_db" not in st.session_state:
        st.session_state.nova_chat_db = ChatDatabase()

    if "nova_engine" not in st.session_state:
        st.session_state.nova_engine = ContextAwareNOVAEngine()

    if "nova_ollama" not in st.session_state:
        st.session_state.nova_ollama = OllamaClient()

    if "nova_chat_id" not in st.session_state:
        st.session_state.nova_chat_id = None

    if "nova_messages" not in st.session_state:
        st.session_state.nova_messages = []


def reset_context():
    engine = st.session_state.nova_engine

    if hasattr(engine, "context"):
        engine.context.clear()


def load_conversation(chat_id):
    st.session_state.nova_chat_id = chat_id

    rows = st.session_state.nova_chat_db.get_messages(chat_id)

    st.session_state.nova_messages = [
        {"sender": sender, "content": content}
        for sender, content in rows
    ]

    reset_context()


def create_new_chat():
    st.session_state.nova_chat_id = None
    st.session_state.nova_messages = []
    reset_context()


def is_context_task_followup(message):
    context = st.session_state.nova_engine.context

    if not context.resolve_reference(message):
        return False

    command = " ".join(message.lower().strip().split())

    patterns = (
        r"^(?:make|set|change)\s+(?:it|that|this)\s+"
        r"(?:to\s+)?(?:high|medium|low)(?:\s+priority)?$",

        r"^(?:move|reschedule|change|update)\s+"
        r"(?:it|that|this)(?:\s+task)?\s+"
        r"(?:to|deadline\s+to|due\s+date\s+to)\s+.+$",

        r"^(?:complete|finish|delete|remove)\s+"
        r"(?:it|that|this)(?:\s+task)?$",

        r"^mark\s+(?:it|that|this)(?:\s+task)?\s+"
        r"(?:as\s+)?(?:complete|completed|done)$",

        r"^(?:rename|retitle)\s+(?:it|that|this)"
        r"(?:\s+task)?\s+to\s+.+$",

        r"^(?:have\s+i\s+completed|have\s+i\s+finished)\s+"
        r"(?:it|that|this)(?:\s+task)?\??$",

        r"^(?:is|was)\s+(?:it|that|this)(?:\s+task)?\s+"
        r"(?:still\s+)?(?:done|complete|completed|pending)\??$",

        r"^did\s+i\s+(?:finish|complete)\s+"
        r"(?:it|that|this)(?:\s+task)?\??$",

        r"^(?:what(?:'s| is)|tell me)\s+"
        r"(?:the\s+)?(?:status|priority|deadline|due date)"
        r"(?:\s+of)?\s+(?:it|that|this)\??$",
    )

    return any(
        re.fullmatch(pattern, command, re.IGNORECASE)
        for pattern in patterns
    )


def is_local_command(message):
    command = " ".join(message.lower().strip().split())

    exact_commands = {
        "help", "commands", "what can you do?",
        "hello", "hi", "hey",
        "list tasks", "show tasks", "my tasks",
        "show my tasks", "what are my tasks",
        "what tasks do i have", "what do i have to do",
        "what do i have to do today",
        "what's on my task list", "whats on my task list",
        "upcoming events", "show events", "my events",
        "show my events", "what events are coming up",
        "what's on my calendar", "whats on my calendar",
        "show my calendar",
        "list notes", "show notes", "my notes",
        "show my notes", "what notes do i have",
        "system status", "pc status",
        "how is my pc doing", "how is my pc performing",
        "check my pc", "system performance",
        "today", "today's tasks", "todays tasks",
        "show today's tasks", "show todays tasks",
        "what should i work on next", "what should i do next",
        "what should i work on", "next task",
        "overdue", "overdue tasks",
    }

    if command in exact_commands:
        return True

    if is_context_task_followup(command):
        return True

    task_terms = ("task", "tasks", "to-do", "todo")
    task_intents = (
        "show", "list", "what", "which", "tell", "find",
        "search", "today", "tomorrow", "overdue", "pending",
        "completed", "complete", "unfinished", "priority",
        "deadline", "due", "work on", "next", "remaining",
        "have i", "did i", "is it", "are my"
    )

    if any(term in command for term in task_terms) and any(
        intent in command for intent in task_intents
    ):
        return True

    if any(term in command for term in ("note", "notes")) and any(
        word in command for word in (
            "show", "list", "find", "search", "look",
            "what", "which", "tell", "read", "open"
        )
    ):
        return True

    if any(term in command for term in (
        "calendar", "event", "events", "appointment", "appointments"
    )) and any(word in command for word in (
        "show", "list", "what", "which", "tell", "upcoming",
        "tomorrow", "today", "next", "coming", "scheduled"
    )):
        return True

    if any(term in command for term in (
        "pc", "computer", "system", "cpu", "gpu",
        "graphics card", "processor", "ram",
        "memory usage", "disk usage", "performance"
    )) and any(word in command for word in (
        "status", "check", "show", "tell", "how",
        "usage", "temperature", "performance",
        "doing", "performing", "report"
    )):
        return True

    if re.fullmatch(
        r"(?:mark\s+.+\s+(?:as\s+)?(?:completed|complete|done)|"
        r"complete\s+(?:my\s+)?(?:task\s+)?(?:called\s+)?\S.*)",
        command
    ):
        return True

    if re.fullmatch(
        r"(?:delete|remove)\s+(?:my\s+)?(?:task\s+)?\S.*",
        command
    ):
        return True

    if re.fullmatch(
        r"(?:make|set|change)\s+.+\s+"
        r"(?:task\s+)?(?:to\s+)?(?:high|medium|low)"
        r"(?:\s+priority)?",
        command
    ):
        return True

    if re.fullmatch(
        r"(?:change|move|update|reschedule)\s+.+\s+"
        r"(?:task\s+)?(?:deadline|due date)\s+to\s+.+",
        command
    ):
        return True

    if re.fullmatch(r"(?:move|reschedule)\s+.+\s+to\s+.+", command):
        return True

    if re.fullmatch(r"(?:rename|retitle)\s+.+\s+to\s+.+", command):
        return True

    prefixes = (
        "search notes |", "add task |", "complete task |",
        "delete task |", "add note |", "add event |",
        "remind me to ", "remind me ",
        "add a task to ", "add task to ",
        "create a task to ", "create task to ",
        "make a task to ", "i need to ", "i have to ",
        "i want to ", "i must ", "need to ", "have to ",
        "finish ", "complete ", "study ", "prepare for ",
        "revise ", "submit ", "do my ", "clean ",
        "organise ", "organize ",
    )

    return command.startswith(prefixes)


def save_message(sender, content):
    chat_id = st.session_state.nova_chat_id

    if chat_id is not None:
        st.session_state.nova_chat_db.save_message(
            chat_id, sender, content
        )


def ensure_conversation(first_message):
    if st.session_state.nova_chat_id is not None:
        return

    title = first_message.strip().replace("\n", " ")

    if len(title) > 30:
        title = title[:30].rstrip() + "..."

    chat_id = st.session_state.nova_chat_db.create_conversation(title)
    st.session_state.nova_chat_id = chat_id


def build_ai_prompt():
    messages = []

    for item in st.session_state.nova_messages[-12:]:
        role = "user" if item["sender"] == "You" else "assistant"

        messages.append({
            "role": role,
            "content": item["content"]
        })

    return messages


def show_sidebar():
    with st.sidebar:
        st.markdown(
            "<h2 style='color:#A58BFF;'>◈ NOVA AI</h2>"
            "<p style='color:#8995AA;font-size:10px;"
            "letter-spacing:2px;'>YOUR PERSONAL ASSISTANT</p>",
            unsafe_allow_html=True
        )

        if st.button("+ New Chat", use_container_width=True):
            create_new_chat()
            st.rerun()

        st.divider()
        st.caption("RECENT CHATS")

        conversations = st.session_state.nova_chat_db.get_conversations()

        for chat_id, title, created_at, updated_at in conversations:
            col1, col2 = st.columns([5, 1])

            with col1:
                if st.button(
                    title,
                    key=f"open_chat_{chat_id}",
                    use_container_width=True
                ):
                    load_conversation(chat_id)
                    st.rerun()

            with col2:
                if st.button(
                    "×",
                    key=f"delete_chat_{chat_id}",
                    help="Delete conversation"
                ):
                    st.session_state.confirm_delete_chat = chat_id

        if st.session_state.get("confirm_delete_chat") is not None:
            chat_id = st.session_state.confirm_delete_chat

            st.warning("Permanently delete this conversation?")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Delete", key="confirm_delete"):
                    st.session_state.nova_chat_db.delete_conversation(chat_id)

                    if st.session_state.nova_chat_id == chat_id:
                        create_new_chat()

                    st.session_state.confirm_delete_chat = None
                    st.rerun()

            with col2:
                if st.button("Cancel", key="cancel_delete"):
                    st.session_state.confirm_delete_chat = None
                    st.rerun()

        st.divider()
        st.caption("NOVA AI • BETA")


def show_ai():
    initialize_ai()

    st.markdown("""
    <style>
    .stApp {
        background: #090D16;
        color: #E8ECF5;
    }
    [data-testid="stSidebar"] {
        background: #0D1320;
        border-right: 1px solid #202B3D;
    }
    [data-testid="stChatMessage"] {
        background: #111A2A;
        border: 1px solid #243149;
        border-radius: 12px;
        padding: 12px;
    }
    .stButton button {
        background: #1C2840;
        color: #E8ECF5;
        border: 1px solid #354363;
        border-radius: 8px;
    }
    .stButton button:hover {
        background: #30254D;
        border-color: #9675FF;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    show_sidebar()

    st.title("NOVA Assistant")

    client = st.session_state.nova_ollama

    if client.is_available():
        st.caption("🟢 Local AI ready • Qwen 2.5")
    else:
        st.caption("🟠 Ollama is not reachable")

    if st.button("Clear Current Chat"):
        if st.session_state.nova_chat_id is not None:
            st.session_state.nova_chat_db.delete_conversation(
                st.session_state.nova_chat_id
            )

        create_new_chat()
        st.rerun()

    if not st.session_state.nova_messages:
        st.markdown("""
        ### Hello! I'm NOVA.

        I can help with:
        - Conversations and explanations
        - Programming, gaming and studies
        - Managing your tasks
        - Searching and saving notes
        - Checking your calendar
        - Checking system information

        Try asking me something, or type `help`.
        """)

    for item in st.session_state.nova_messages:
        role = "user" if item["sender"] == "You" else "assistant"

        with st.chat_message(role):
            st.markdown(item["content"])

    message = st.chat_input("Ask NOVA anything...")

    if message:
        ensure_conversation(message)

        st.session_state.nova_messages.append({
            "sender": "You",
            "content": message
        })

        save_message("You", message)

        with st.chat_message("user"):
            st.markdown(message)

        if is_local_command(message):
            with st.chat_message("assistant"):
                with st.spinner("Running NOVA local intelligence..."):
                    try:
                        response = st.session_state.nova_engine.process(message)
                        response = str(response)
                    except Exception as error:
                        response = (
                            "Something went wrong while processing "
                            f"your command: {error}"
                        )

                st.markdown(response)

        else:
            with st.chat_message("assistant"):
                try:
                    prompt_messages = build_ai_prompt()

                    with st.spinner("NOVA is thinking..."):
                        response = st.write_stream(
                            client.stream_chat(
                                prompt_messages,
                                system_prompt=SYSTEM_PROMPT
                            )
                        )

                    response = str(response)

                except Exception as error:
                    response = (
                        "Sorry, something went wrong with the AI connection. "
                        f"Details: {error}"
                    )

                st.markdown(response)

        st.session_state.nova_messages.append({
            "sender": "AI",
            "content": response
        })

        save_message("AI", response)


if __name__ == "__main__":
    show_ai()
