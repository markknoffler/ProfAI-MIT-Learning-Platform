import time
import streamlit as st


def render_header(title: str) -> None:
    st.markdown(f"## {title}")


def render_subheader(text: str) -> None:
    st.markdown(f"### {text}")


def animate_lesson_loading(title: str, final_content: str | None = None, min_cycles: int = 6) -> None:
    st.markdown(f"**{title}**")
    placeholder = st.empty()
    dots = [".", "..", "...", "...."]
    # Show a few cycles of thinking animation
    for i in range(min_cycles):
        placeholder.info(f"AI thinking{dots[i % len(dots)]}")
        time.sleep(0.25)
    if final_content:
        # Reveal content progressively to simulate streaming
        reveal = st.empty()
        acc = ""
        for ch in final_content:
            acc += ch
            if len(acc) % 60 == 0:
                reveal.code(acc, language="json")
                time.sleep(0.01)
        reveal.code(acc, language="json")


