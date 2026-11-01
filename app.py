
import streamlit as st
from datetime import date

from tasks_streamlit import show_tasks
from calendar_streamlit import show_calendar
from notes_streamlit import show_notes
from pc_monitor_streamlit import show_pc_monitor
from ai_streamlit import show_ai

from core.database import Database
from core.calendar_database import CalendarDatabase
from core.notes_database import NotesDatabase


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="NOVA | Command Center",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------------------------------
# DATABASES
# --------------------------------------------------

@st.cache_resource
def get_databases():
    return Database(), CalendarDatabase(), NotesDatabase()


# --------------------------------------------------
# NAVIGATION
# --------------------------------------------------

PAGES = [
    "Dashboard",
    "Tasks",
    "Calendar",
    "Notes",
    "PC Monitor",
    "NOVA AI"
]


def navigate_to(page_name):
    st.session_state.nova_page = page_name


def sync_navigation():
    st.session_state.nova_page = st.session_state.nova_navigation


# --------------------------------------------------
# THEME
# --------------------------------------------------

st.markdown("""
<style>
.stApp {
    background-color: #090D16;
    color: #E8ECF5;
}

[data-testid="stSidebar"] {
    background-color: #0D1320;
    border-right: 1px solid #202B3D;
}

[data-testid="stSidebar"] hr {
    border-color: #202B3D;
}

h1, h2, h3 {
    color: #E8ECF5;
}

p, label {
    color: #8995AA;
}

.stButton button {
    background-color: #1C2840;
    color: #E8ECF5;
    border: 1px solid #354363;
    border-radius: 8px;
    transition: 0.2s;
}

.stButton button:hover {
    background-color: #30254D;
    border-color: #9675FF;
    color: white;
}

.stTextInput input,
.stTextArea textarea,
.stDateInput input {
    background-color: #111A2A;
    color: #E8ECF5;
    border: 1px solid #354363;
}

[data-testid="stMetric"] {
    background: #111A2A;
    border: 1px solid #243149;
    padding: 16px;
    border-radius: 12px;
}

[data-testid="stMetricLabel"] {
    color: #8998B0;
}

[data-testid="stMetricValue"] {
    color: #B6A3FF;
}

[data-testid="stSidebar"] .stRadio label {
    color: #8995AA;
}

.nova-card {
    background: #111A2A;
    border: 1px solid #243149;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 12px;
}

.nova-muted {
    color: #8794AA;
    font-size: 13px;
}

.nova-accent {
    color: #B6A3FF;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

def show_dashboard():

    task_db, calendar_db, notes_db = get_databases()

    today = date.today()

    tasks = task_db.get_tasks()
    events = calendar_db.get_upcoming_events(limit=5)
    notes = notes_db.get_notes()

    total_tasks = len(tasks)

    completed_tasks = sum(
        1 for task in tasks
        if int(task.get("completed", 0)) == 1
    )

    pending_tasks = total_tasks - completed_tasks

    overdue_tasks = []

    for task in tasks:
        if int(task.get("completed", 0)) == 0:
            try:
                due = date.fromisoformat(str(task["due_date"])[:10])

                if due < today:
                    overdue_tasks.append(task)

            except (ValueError, TypeError, KeyError):
                pass

    pinned_notes = [
        note for note in notes
        if int(note.get("pinned", 0)) == 1
    ]

    # HEADER

    st.title("◈ NOVA Dashboard")

    st.caption(
        f"Your personal command center • "
        f"{today.strftime('%A, %d %B %Y')}"
    )

    st.divider()

    # TASK METRICS

    st.subheader("Task Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Tasks", total_tasks)
    c2.metric("Completed", completed_tasks)
    c3.metric("Pending", pending_tasks)
    c4.metric("Overdue", len(overdue_tasks))

    if total_tasks:
        progress = completed_tasks / total_tasks

        st.progress(
            progress,
            text=f"Task completion: {progress * 100:.0f}%"
        )
    else:
        st.caption("You haven't added any tasks yet.")

    st.divider()

    # EVENTS AND TASKS

    left, right = st.columns(2)

    with left:

        st.subheader("Upcoming Events")

        if events:

            for event in events:

                event_date = str(event.get("event_date", ""))
                event_time = str(event.get("event_time", ""))

                st.markdown(
                    f"""
                    <div class="nova-card">
                        <div class="nova-accent">
                            ◈ {event.get("title", "Untitled Event")}
                        </div>
                        <div class="nova-muted">
                            {event_date} {event_time}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        else:
            st.info("No upcoming events. Your calendar is clear!")

        if st.button(
            "Open Calendar →",
            key="dashboard_open_calendar"
        ):
            navigate_to("Calendar")
            st.rerun()

    with right:

        st.subheader("Pending Tasks")

        pending_list = [
            task for task in tasks
            if int(task.get("completed", 0)) == 0
        ]

        if pending_list:

            for task in pending_list[:5]:

                priority = task.get("priority", "Medium")
                due_date = task.get("due_date", "No date")

                st.markdown(
                    f"""
                    <div class="nova-card">
                        <div class="nova-accent">
                            ◈ {task.get("title", "Untitled Task")}
                        </div>
                        <div class="nova-muted">
                            Priority: {priority} |
                            Due: {due_date}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        else:
            st.success("All tasks completed!")

        if st.button(
            "Open Tasks →",
            key="dashboard_open_tasks"
        ):
            navigate_to("Tasks")
            st.rerun()

    st.divider()

    # NOTES

    st.subheader("Notes")

    n1, n2 = st.columns(2)

    n1.metric("Total Notes", len(notes))
    n2.metric("Pinned Notes", len(pinned_notes))

    if notes:

        st.markdown("#### Recent Notes")

        for note in notes[:5]:

            pin_label = (
                "📌 Pinned"
                if int(note.get("pinned", 0)) == 1
                else "Note"
            )

            st.markdown(
                f"""
                <div class="nova-card">
                    <div class="nova-accent">
                        {pin_label} · {note.get("title", "Untitled")}
                    </div>
                    <div class="nova-muted">
                        {str(note.get("content", ""))[:150]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    else:
        st.info("No notes saved yet.")

    if st.button(
        "Open Notes →",
        key="dashboard_open_notes"
    ):
        navigate_to("Notes")
        st.rerun()

    st.divider()

    # QUICK ACCESS

    st.subheader("Quick Access")

    q1, q2, q3 = st.columns(3)

    with q1:
        if st.button("◈ PC Monitor", use_container_width=True):
            navigate_to("PC Monitor")
            st.rerun()

    with q2:
        if st.button("◈ NOVA AI", use_container_width=True):
            navigate_to("NOVA AI")
            st.rerun()

    with q3:
        if st.button("⚙ Settings", use_container_width=True):
            navigate_to("Settings")
            st.rerun()

    st.caption("NOVA BETA • YOUR PERSONAL COMMAND CENTER")


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

if "nova_page" not in st.session_state:
    st.session_state.nova_page = "Dashboard"

if "nova_navigation" not in st.session_state:
    st.session_state.nova_navigation = "Dashboard"


with st.sidebar:

    st.markdown("""
    <div style="padding:10px 0 20px 0;">
        <h1 style="color:#A58BFF; margin-bottom:0;">
            ◈ NOVA
        </h1>
        <p style="letter-spacing:3px; font-size:10px;">
            PERSONAL COMMAND CENTER
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.radio(
        "NAVIGATION",
        PAGES,
        key="nova_navigation",
        index=PAGES.index(st.session_state.nova_page)
        if st.session_state.nova_page in PAGES else 0,
        on_change=sync_navigation
    )

    st.divider()

    st.button(
        "⚙  Settings",
        key="sidebar_settings",
        use_container_width=True,
        on_click=navigate_to,
        args=("Settings",)
    )

    st.markdown("""
    <div style="padding-top:15px;">
        <p style="font-size:10px; letter-spacing:2px; color:#68758B;">
            NOVA BETA • PRIVATE ACCESS
        </p>
    </div>
    """, unsafe_allow_html=True)


# --------------------------------------------------
# PAGE ROUTING
# --------------------------------------------------

page = st.session_state.nova_page

if page == "Dashboard":

    show_dashboard()

elif page == "Tasks":

    show_tasks()

elif page == "Calendar":

    show_calendar()

elif page == "Notes":

    show_notes()

elif page == "PC Monitor":

    show_pc_monitor()

elif page == "NOVA AI":

    show_ai()

elif page == "Settings":

    st.title("⚙ Settings")
    st.caption("NOVA-Beta application settings")

    st.divider()

    st.subheader("Appearance")
    st.write("Theme: Dark Navy / Purple")

    st.subheader("Application")
    st.write("Version: NOVA-Beta")
    st.write("Interface: Streamlit")

    st.subheader("Data Storage")
    st.write("Beta databases are stored in the beta_data folder.")

    st.info(
        "More settings will be added as the web application develops."
    )

    st.divider()

    st.caption("NOVA BETA")
