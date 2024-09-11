from time import sleep

import streamlit as st
from streamlit.components.v1 import html


SLEEP_DELAY = 1

def read_file(file_path: str) -> str:
    with open(file_path, encoding="utf-8") as file:
        return file.read().strip()

def long_duration_function(name: str, emoji: str) -> str:
    progress_text = """# Really Complicated Operation is in progress. Please wait..."""
    st.session_state["counter"] += 1

    progress_text += f"\nCounter of interaptions = {st.session_state['counter']}"
    my_bar = st.progress(0, text=progress_text)
    for i in range(1, 11):
        sleep(SLEEP_DELAY)
        my_bar.progress(i * 10, text=progress_text)

    return f" Hello {name}, your favorite emoji is {emoji}!"


def pop_up_window() -> str:
    """Read PopUp window overlapping to disable user interaction"""
    return read_file("./static/popup_window.html")


def pop_up_window_click(activate: bool = True) -> None:
    """Pop up window overlapping to disable user interaction"""
    if activate:
        html(read_file("./static/activate_popup_js_injection.html"))

    # deactivate and clean url
    else:
        html(read_file("./static/deactivate_popup_js_injection.html"))

user_name = st.text_input("Enter your name", "Ivan")
favorite_emoji = st.selectbox(
    "Select your favorite emoji", ["😀", "😂", "😍", "😎", "🤔"]
)

if "counter" not in st.session_state:
    st.session_state["counter"] = 0

if st.button("Submit"):
  # create st.empty() container
    placeholder = st.empty()

  # insert part with popup initialization button for our HTML page to container
    placeholder.write(pop_up_window(), unsafe_allow_html=True)

  # activate pop overlay by clicking on button
    pop_up_window_click(activate=True)

  # Run long-duration function
    result = long_duration_function(user_name, favorite_emoji)

  # Deactivate pop overlay by clicking on the close button
    pop_up_window_click(activate=False)

  # Clean st.empty() container
    placeholder.empty()

    st.success(result, icon="🎉")