"""
ASCII art and visual elements for proCoder
"""

LOGO = r"""
    ____              ______          __
   / __ \________  __/ ____/___  ____/ /__  _____
  / /_/ / ___/ _ \/ /   / __ \/ __  / _ \/ ___/
 / ____/ /  /  __/ /___/ /_/ / /_/ /  __/ /
/_/   /_/   \___/\____/\____/\__,_/\___/_/
"""

LOGO_SMALL = r"""
  ___          ___         _
 | _ \_ _ ___ / __|___  __| |___ _ _
 |  _/ '_/ _ \ (__/ _ \/ _` / -_) '_|
 |_| |_| \___/\___\___/\__,_\___|_|
"""

ROCKET = "🚀"
SPARKLE = "✨"
BRAIN = "🧠"
LIGHTNING = "⚡"
PACKAGE = "📦"
CHECK = "✓"
CROSS = "✗"
ARROW = "→"
BULLET = "•"

# Box drawing characters for modern UI
BOX_HORIZONTAL = "─"
BOX_VERTICAL = "│"
BOX_TOP_LEFT = "╭"
BOX_TOP_RIGHT = "╮"
BOX_BOTTOM_LEFT = "╰"
BOX_BOTTOM_RIGHT = "╯"
BOX_VERTICAL_RIGHT = "├"
BOX_VERTICAL_LEFT = "┤"
BOX_HORIZONTAL_DOWN = "┬"
BOX_HORIZONTAL_UP = "┴"
BOX_CROSS = "┼"

# Modern separators
SEPARATOR_HEAVY = "━" * 60
SEPARATOR_LIGHT = "─" * 60
SEPARATOR_DOTS = "·" * 60
SEPARATOR_WAVE = "～" * 60

def make_box(text: str, width: int = 60, style: str = "single") -> str:
    """Create a box around text"""
    lines = text.split('\n')
    max_len = max(len(line) for line in lines) if lines else 0
    box_width = max(width, max_len + 4)

    if style == "double":
        top = f"╔{'═' * (box_width - 2)}╗"
        bottom = f"╚{'═' * (box_width - 2)}╝"
        side = "║"
    else:
        top = f"{BOX_TOP_LEFT}{BOX_HORIZONTAL * (box_width - 2)}{BOX_TOP_RIGHT}"
        bottom = f"{BOX_BOTTOM_LEFT}{BOX_HORIZONTAL * (box_width - 2)}{BOX_BOTTOM_RIGHT}"
        side = BOX_VERTICAL

    result = [top]
    for line in lines:
        padding = box_width - len(line) - 4
        result.append(f"{side} {line}{' ' * padding} {side}")
    result.append(bottom)

    return '\n'.join(result)

def gradient_text(text: str) -> str:
    """Return text with gradient color codes for Rich"""
    # Returns the text as-is, Rich will handle the gradient
    return text
