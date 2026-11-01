
import streamlit as st
from datetime import date, time
from core.calendar_database import CalendarDatabase

db = CalendarDatabase()

REMINDERS = {
    "No reminder": 0,
    "5 minutes before": 5,
    "10 minutes before": 10,
    "15 minutes before": 15,
    "30 minutes before": 30,
    "60 minutes before": 60,
}


def show_calendar():

    st.title("📅 Calendar")
    st.caption("Manage your schedule and upcoming events.")

    if "calendar_edit_id" not in st.session_state:
        st.session_state.calendar_edit_id = None

    if "calendar_selected_date" not in st.session_state:
        st.session_state.calendar_selected_date = date.today()

    # Date selection
    st.subheader("MONTH VIEW")

    selected_date = st.date_input(
        "Select a date",
        value=st.session_state.calendar_selected_date,
        key="calendar_date_picker"
    )

    st.session_state.calendar_selected_date = selected_date

    st.divider()

    # Add event
    with st.container(border=True):
        st.subheader("CREATE EVENT")

        with st.form("create_calendar_event"):

            title = st.text_input(
                "Event title",
                placeholder="Enter event title"
            )

            description = st.text_area(
                "Description",
                placeholder="Add event details..."
            )

            col1, col2 = st.columns(2)

            with col1:
                event_date = st.date_input(
                    "Event date",
                    value=selected_date,
                    key="new_event_date"
                )

            with col2:
                event_time = st.time_input(
                    "Event time",
                    value=time(12, 0),
                    key="new_event_time"
                )

            reminder = st.selectbox(
                "Reminder",
                list(REMINDERS.keys())
            )

            submitted = st.form_submit_button(
                "＋ Create Event",
                use_container_width=True
            )

            if submitted:
                if not title.strip():
                    st.error("Please enter an event title.")
                else:
                    db.add_event(
                        title.strip(),
                        description.strip(),
                        event_date.isoformat(),
                        event_time.strftime("%H:%M"),
                        REMINDERS[reminder]
                    )

                    st.success("Event created!")
                    st.session_state.calendar_selected_date = event_date
                    st.rerun()

    # Selected date events
    st.divider()
    st.subheader("SELECTED DATE EVENTS")
    st.caption(selected_date.strftime("%A, %d %B %Y"))

    events = db.get_events(selected_date.isoformat())

    if not events:
        st.info("No events scheduled for this date.")

    else:
        event_options = {
            f'{event["event_time"] or "No time"} | {event["title"]}': event["id"]
            for event in events
        }

        selected_label = st.selectbox(
            "Choose an event",
            list(event_options.keys()),
            key="selected_calendar_event"
        )

        selected_id = event_options[selected_label]

        selected_event = db.get_event(selected_id)

        for event in events:
            with st.container(border=True):
                st.markdown(
                    f'**{event["event_time"] or "No time"} — {event["title"]}**'
                )

                if event["description"]:
                    st.caption(event["description"])

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✎ Edit Event", use_container_width=True):
                st.session_state.calendar_edit_id = selected_id
                st.rerun()

        with col2:
            if st.button("⌫ Delete Event", use_container_width=True):
                st.session_state.calendar_delete_id = selected_id
                st.rerun()

        # Delete confirmation
        if st.session_state.get("calendar_delete_id") == selected_id:
            st.warning("Are you sure you want to delete this event?")

            yes, no = st.columns(2)

            with yes:
                if st.button("Yes, delete event"):
                    db.delete_event(selected_id)
                    st.session_state.calendar_delete_id = None
                    st.session_state.calendar_edit_id = None
                    st.rerun()

            with no:
                if st.button("Cancel delete"):
                    st.session_state.calendar_delete_id = None
                    st.rerun()

        # Edit event
        if st.session_state.calendar_edit_id == selected_id and selected_event:

            st.divider()
            st.subheader("EDIT EVENT")

            with st.form("edit_calendar_event"):

                edit_title = st.text_input(
                    "Event title",
                    value=selected_event["title"],
                    key=f"edit_title_{selected_id}"
                )

                edit_description = st.text_area(
                    "Description",
                    value=selected_event["description"] or "",
                    key=f"edit_description_{selected_id}"
                )

                col1, col2 = st.columns(2)

                with col1:
                    edit_date = st.date_input(
                        "Date",
                        value=date.fromisoformat(
                            selected_event["event_date"]
                        ),
                        key=f"edit_date_{selected_id}"
                    )

                with col2:
                    saved_time = selected_event["event_time"] or "12:00"

                    edit_time = st.time_input(
                        "Time",
                        value=time.fromisoformat(saved_time),
                        key=f"edit_time_{selected_id}"
                    )

                current_reminder = selected_event["reminder_minutes"]

                reminder_names = list(REMINDERS.keys())

                reminder_index = next(
                    (
                        i for i, value in enumerate(REMINDERS.values())
                        if value == current_reminder
                    ),
                    0
                )

                edit_reminder = st.selectbox(
                    "Reminder",
                    reminder_names,
                    index=reminder_index,
                    key=f"edit_reminder_{selected_id}"
                )

                save_edit = st.form_submit_button(
                    "Save Changes",
                    use_container_width=True
                )

                if save_edit:
                    if not edit_title.strip():
                        st.error("Please enter an event title.")
                    else:
                        db.update_event(
                            selected_id,
                            edit_title.strip(),
                            edit_description.strip(),
                            edit_date.isoformat(),
                            edit_time.strftime("%H:%M"),
                            REMINDERS[edit_reminder]
                        )

                        st.session_state.calendar_edit_id = None
                        st.session_state.calendar_selected_date = edit_date
                        st.success("Event updated!")
                        st.rerun()

            if st.button("Cancel Edit"):
                st.session_state.calendar_edit_id = None
                st.rerun()

    # Upcoming events
    st.divider()
    st.subheader("UPCOMING EVENTS")

    upcoming = db.get_upcoming_events(10)

    if not upcoming:
        st.info("No upcoming events.")

    else:
        for event in upcoming:
            with st.container(border=True):
                event_date = date.fromisoformat(event["event_date"])

                st.markdown(
                    f'**{event_date.strftime("%d %b %Y")} | '
                    f'{event["event_time"] or "--:--"} | '
                    f'{event["title"]}**'
                )

                if event["description"]:
                    st.caption(event["description"])

                if st.button(
                    "Open event date",
                    key=f"open_event_{event['id']}"
                ):
                    st.session_state.calendar_selected_date = event_date
                    st.rerun()
