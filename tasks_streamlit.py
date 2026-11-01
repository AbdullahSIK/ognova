
import streamlit as st
from datetime import date
from core.database import Database

db = Database()


def show_tasks():
    st.title("Task Manager")
    st.caption(
        "Organize your work. Manage your priorities. "
        "Stay productive."
    )

    # Initialize editing state
    if "editing_task_id" not in st.session_state:
        st.session_state.editing_task_id = None

    tasks = db.get_tasks()

    # Task creation / editing
    with st.container(border=True):
        st.subheader(
            "EDIT TASK" if st.session_state.editing_task_id
            else "CREATE TASK"
        )

        editing_task = next(
            (
                task for task in tasks
                if task["id"] == st.session_state.editing_task_id
            ),
            None
        )

        with st.form("task_form"):
            title = st.text_input(
                "Task name",
                value=editing_task["title"] if editing_task else "",
                placeholder="Enter your task name..."
            )

            description = st.text_input(
                "Description (optional)",
                value=editing_task["description"] if editing_task else ""
            )

            col1, col2 = st.columns(2)

            with col1:
                priority = st.selectbox(
                    "Priority",
                    ["Low", "Medium", "High"],
                    index=(
                        ["Low", "Medium", "High"].index(
                            editing_task["priority"]
                        ) if editing_task else 1
                    )
                )

            with col2:
                due_date = st.date_input(
                    "Due date",
                    value=(
                        date.fromisoformat(editing_task["due_date"])
                        if editing_task else date.today()
                    )
                )

            submitted = st.form_submit_button(
                "Save Changes" if editing_task else "＋ Add Task",
                use_container_width=True
            )

            if submitted:
                if not title.strip():
                    st.error("Please enter a task name.")
                else:
                    if editing_task:
                        db.update_task(
                            editing_task["id"],
                            title.strip(),
                            description.strip(),
                            priority,
                            due_date.isoformat()
                        )
                        st.session_state.editing_task_id = None
                        st.success("Task updated!")
                    else:
                        db.add_task(
                            title.strip(),
                            description.strip(),
                            priority,
                            due_date.isoformat()
                        )
                        st.success("Task added!")

                    st.rerun()

        if editing_task:
            if st.button("Cancel Edit"):
                st.session_state.editing_task_id = None
                st.rerun()

    # Refresh task list
    tasks = db.get_tasks()

    completed = sum(bool(task["completed"]) for task in tasks)

    st.subheader(
        f"YOUR TASKS  •  {len(tasks)} TOTAL  •  {completed} COMPLETED"
    )

    # Task statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Tasks", len(tasks))

    with col2:
        st.metric("Completed", completed)

    with col3:
        st.metric("Pending", len(tasks) - completed)

    if not tasks:
        st.info("No tasks yet. Create your first task!")
        return

    # Task selection
    task_options = {
        f'{task["title"]} | {task["priority"]} | {task["due_date"]} | '
        f'{"Completed" if task["completed"] else "Pending"}': task["id"]
        for task in tasks
    }

    selected_label = st.selectbox(
        "Select a task to manage",
        list(task_options.keys())
    )

    selected_id = task_options[selected_label]

    selected_task = next(
        task for task in tasks if task["id"] == selected_id
    )

    # Task list
    st.dataframe(
        [
            {
                "Task": task["title"],
                "Priority": task["priority"],
                "Due Date": task["due_date"],
                "Status": (
                    "Completed" if task["completed"] else "Pending"
                )
            }
            for task in tasks
        ],
        use_container_width=True,
        hide_index=True
    )

    # Actions
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✓ Complete / Undo", use_container_width=True):
            db.set_completed(
                selected_id,
                not bool(selected_task["completed"])
            )
            st.rerun()

    with col2:
        if st.button("✎ Edit Task", use_container_width=True):
            st.session_state.editing_task_id = selected_id
            st.rerun()

    with col3:
        if st.button("⌫ Delete Task", use_container_width=True):
            st.session_state.confirm_delete = selected_id

    if st.session_state.get("confirm_delete"):
        st.warning("Are you sure you want to delete this task?")

        yes, no = st.columns(2)

        with yes:
            if st.button("Yes, delete"):
                db.delete_task(st.session_state.confirm_delete)
                st.session_state.confirm_delete = None
                st.session_state.editing_task_id = None
                st.rerun()

        with no:
            if st.button("Cancel deletion"):
                st.session_state.confirm_delete = None
                st.rerun()
