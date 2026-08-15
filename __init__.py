"""
@author: phoenix
@title: Phoenix Text Nodes
@nickname: phoenix-text-nodes
@description: Custom text-utility nodes for ComfyUI.
"""

from . import nodes
from . import random_csv_text_replace

NODE_CLASS_MAPPINGS = {
    **nodes.NODE_CLASS_MAPPINGS,
    **random_csv_text_replace.NODE_CLASS_MAPPINGS,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    **nodes.NODE_DISPLAY_NAME_MAPPINGS,
    **random_csv_text_replace.NODE_DISPLAY_NAME_MAPPINGS,
}

WEB_DIRECTORY = "js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
