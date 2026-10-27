<<<<<<< HEAD
from typing import Any
import gradio as gr

def get_theme() -> Any:
=======
import gradio as gr

def get_theme():
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
    return gr.themes.Soft(
        primary_hue=gr.themes.colors.blue,
        neutral_hue=gr.themes.colors.slate,
        radius_size=gr.themes.sizes.radius_lg,
        spacing_size=gr.themes.sizes.spacing_md,
    )
