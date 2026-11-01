
import streamlit as st
from core.notes_database import NotesDatabase

db = NotesDatabase()


def show_notes():

    st.title("✍️ NOVA Notes")
    st.caption("Capture ideas, organize thoughts, and keep important notes.")

    if "note_edit_id" not in st.session_state:
        st.session_state.note_edit_id = None

    if "note_new_mode" not in st.session_state:
        st.session_state.note_new_mode = True

    if "note_search" not in st.session_state:
        st.session_state.note_search = ""

    # Search and create controls
    col1, col2 = st.columns([3, 1])

    with col1:
        search = st.text_input(
            "Search notes",
            placeholder="Search by title or content...",
            key="note_search"
        )

    with col2:
        st.write("")
        st.write("")
        if st.button("+ New Note", use_container_width=True):
            st.session_state.note_edit_id = None
            st.session_state.note_new_mode = True
            st.rerun()

    notes = db.get_notes(search)

    pinned_count = sum(1 for note in notes if note["pinned"])

    st.caption(
        f"{len(notes)} notes · {pinned_count} pinned"
    )

    st.divider()

    # Notes layout
    left, right = st.columns([1, 2])

    with left:
        st.subheader("YOUR NOTES")

        if not notes:
            st.info("No notes found. Create your first note!")

        for note in notes:

            pin = "📌 " if note["pinned"] else ""

            with st.container(border=True):
                st.markdown(f"**{pin}{note['title']}**")

                preview = note["content"].strip()

                if preview:
                    st.caption(preview[:100] + (
                        "..." if len(preview) > 100 else ""
                    ))

                st.caption(
                    f"Updated: {note['updated_at']}"
                )

                if st.button(
                    "Open Note",
                    key=f"open_note_{note['id']}",
                    use_container_width=True
                ):
                    st.session_state.note_edit_id = note["id"]
                    st.session_state.note_new_mode = False
                    st.rerun()

    with right:

        note = None

        if not st.session_state.note_new_mode:
            if st.session_state.note_edit_id is not None:
                note = db.get_note(st.session_state.note_edit_id)

        if note is None and not st.session_state.note_new_mode:
            st.info("Select a note from the left to edit it.")
        else:

            if st.session_state.note_new_mode:
                st.subheader("CREATE NEW NOTE")
                title_value = ""
                content_value = ""
                pinned_value = False
            else:
                st.subheader("EDIT NOTE")
                title_value = note["title"]
                content_value = note["content"]
                pinned_value = bool(note["pinned"])

            with st.form("note_editor"):

                title = st.text_input(
                    "Note title",
                    value=title_value,
                    placeholder="Enter note title"
                )

                content = st.text_area(
                    "Note content",
                    value=content_value,
                    placeholder="Start writing your note here...",
                    height=300
                )

                pinned = st.checkbox(
                    "📌 Pin this note",
                    value=pinned_value
                )

                col1, col2 = st.columns(2)

                with col1:
                    save = st.form_submit_button(
                        "Save Note",
                        use_container_width=True
                    )

                with col2:
                    cancel = st.form_submit_button(
                        "Cancel",
                        use_container_width=True
                    )

                if save:

                    if not title.strip() and not content.strip():
                        st.error(
                            "Please enter a title or some content."
                        )

                    else:
                        final_title = title.strip() or "Untitled Note"

                        if st.session_state.note_new_mode:

                            new_id = db.add_note(
                                final_title,
                                content,
                                pinned
                            )

                            st.session_state.note_edit_id = new_id
                            st.session_state.note_new_mode = False

                        else:

                            db.update_note(
                                note["id"],
                                final_title,
                                content,
                                pinned
                            )

                        st.success("Note saved successfully!")
                        st.rerun()

                if cancel:
                    st.session_state.note_edit_id = None
                    st.session_state.note_new_mode = True
                    st.rerun()

            if note is not None:

                st.divider()

                st.caption(
                    f"Created: {note['created_at']}"
                )

                st.caption(
                    f"Updated: {note['updated_at']}"
                )

                if st.button(
                    "🗑️ Delete Note",
                    use_container_width=True
                ):
                    st.session_state.note_delete_id = note["id"]
                    st.rerun()

                if st.session_state.get("note_delete_id") == note["id"]:

                    st.warning(
                        "Are you sure you want to delete this note?"
                    )

                    yes, no = st.columns(2)

                    with yes:
                        if st.button("Yes, delete", key="confirm_note_delete"):
                            db.delete_note(note["id"])
                            st.session_state.note_edit_id = None
                            st.session_state.note_new_mode = True
                            st.session_state.note_delete_id = None
                            st.rerun()

                    with no:
                        if st.button("Cancel", key="cancel_note_delete"):
                            st.session_state.note_delete_id = None
                            st.rerun()
