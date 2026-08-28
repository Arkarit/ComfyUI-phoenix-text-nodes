"""
@author: phoenix
@title: Phoenix Text Nodes
@nickname: phoenix-text-nodes
@description: Custom text-utility nodes for ComfyUI.
"""

from . import random_csv_text_replace
from . import save_text
from . import save_image_and_text
from . import append_text
from . import prepend_text
from . import load_text
from . import filter_comments
from . import flex_concat
from . import carriage_return

NODE_CLASS_MAPPINGS = {
    **random_csv_text_replace.NODE_CLASS_MAPPINGS,
    **save_text.NODE_CLASS_MAPPINGS,
    **save_image_and_text.NODE_CLASS_MAPPINGS,
    **append_text.NODE_CLASS_MAPPINGS,
    **prepend_text.NODE_CLASS_MAPPINGS,
    **load_text.NODE_CLASS_MAPPINGS,
    **filter_comments.NODE_CLASS_MAPPINGS,
    **flex_concat.NODE_CLASS_MAPPINGS,
    **carriage_return.NODE_CLASS_MAPPINGS,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    **random_csv_text_replace.NODE_DISPLAY_NAME_MAPPINGS,
    **save_text.NODE_DISPLAY_NAME_MAPPINGS,
    **save_image_and_text.NODE_DISPLAY_NAME_MAPPINGS,
    **append_text.NODE_DISPLAY_NAME_MAPPINGS,
    **prepend_text.NODE_DISPLAY_NAME_MAPPINGS,
    **load_text.NODE_DISPLAY_NAME_MAPPINGS,
    **filter_comments.NODE_DISPLAY_NAME_MAPPINGS,
    **flex_concat.NODE_DISPLAY_NAME_MAPPINGS,
    **carriage_return.NODE_DISPLAY_NAME_MAPPINGS,
}

WEB_DIRECTORY = "js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
