"""
Display module for converting Object AST nodes to human-readable strings.

This module provides the opposite functionality of the parser: it converts
Object instances back into readable text with precedence-aware parenthesization
and customizable display overrides.
"""

from typing import Optional, Callable, Dict, Any
from ..core import Object

# ============================================================================
# Precedence Constants (mirroring parser structure)
# ============================================================================

PREC_COMPOSITION = 10       # | (lowest precedence)
PREC_ALPHA_RULE = 20        # gives, and, or (alphanumeric rules)
PREC_SPECIAL_RULE = 30      # =>, ->, <-> (special char rules)
PREC_ADDITION = 40          # +, -
PREC_MULTIPLICATION = 50    # *
PREC_DIVISION = 60          # /
PREC_APPLICATION = 70       # f(x, y) (highest precedence)

INFIX_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "plus": {"symbol": " + ", "precedence": PREC_ADDITION},
    "minus": {"symbol": " - ", "precedence": PREC_ADDITION},
    "mult": {"symbol": " * ", "precedence": PREC_MULTIPLICATION},
    "div": {"symbol": " / ", "precedence": PREC_DIVISION},
    "and": {"symbol": " ∧ ", "precedence": PREC_ALPHA_RULE},
    "or": {"symbol": " ∨ ", "precedence": PREC_ALPHA_RULE},
}

DISPLAY_OVERRIDES: Dict = {}

def is_alphanumeric_symbol(symbol: str) -> bool:
    """Check if a symbol consists only of alphanumeric characters and underscores."""
    return symbol.replace("_", "").replace(".", "").isalnum()

def is_infix_term(obj: Object) -> bool:
    """Check if a term should be displayed as an infix operator."""
    return (obj.type == "Term" and
            obj.handle in INFIX_OVERRIDES and
            len(obj.children) == 2)

def get_precedence(obj: Object, as_infix: bool = False) -> int:
    if obj.type == "Comp":
        return PREC_COMPOSITION

    if obj.type == "Rew":
        # Check if symbol is alphanumeric or special chars
        symbol = obj.handle
        if is_alphanumeric_symbol(symbol):
            return PREC_ALPHA_RULE
        else:
            return PREC_SPECIAL_RULE

    if obj.type == "Term":
        name = obj.handle

        # Check if this term has an infix override
        if as_infix and name in INFIX_OVERRIDES:
            return INFIX_OVERRIDES[name]["precedence"]

        # Regular term application (function call)
        return PREC_APPLICATION

    # Hole has highest precedence (atomic)
    return PREC_APPLICATION

def needs_parens(child: Object, parent_prec: int, position: str = "left") -> bool:
    """
    Determine if an object needs parentheses when displayed in a parent context.

        child: The object being displayed
        parent_prec: The precedence of the parent operator
        position: "left" or "right" (matters for associativity)

    """
    child_prec = get_precedence(child, as_infix=is_infix_term(child))

    # Lower precedence always needs parens
    if child_prec < parent_prec:
        return True

    # Equal precedence: check associativity
    # All operators are right-associative, so equal precedence needs parens on left
    if child_prec == parent_prec:
        return position == "left"

    # Higher precedence doesn't need parens
    return False


def register_display(name: str, func) -> None:
    """
    Register a custom display function for a specific term name.
    """
    DISPLAY_OVERRIDES[name] = func


def display_infix_term(obj: Object, parent_prec: int) -> str:
    """Display a term as an infix operator: left op right"""
    name = obj.handle
    metadata = INFIX_OVERRIDES[name]
    symbol = metadata["symbol"]
    my_prec = metadata["precedence"]

    left, right = obj.children
    # Display children without parent context (they don't wrap themselves)
    left_str = display(left, 0)
    right_str = display(right, 0)

    # We decide if children need wrapping based on precedence + position
    if needs_parens(left, my_prec, "left"):
        left_str = f"({left_str})"
    if needs_parens(right, my_prec, "right"):
        right_str = f"({right_str})"

    result = f"{left_str}{symbol}{right_str}"

    # Wrap ourselves if our precedence is lower than parent's
    if my_prec < parent_prec:
        result = f"({result})"

    return result

def display_prefix_term(obj: Object, parent_prec: int) -> str:
    """Display a term as a function application: f(args...)"""
    name = obj.handle

    if len(obj.children) == 0:
        # Nullary term (constant)
        return name

    # Format arguments (use precedence 0 for arguments in parens)
    arg_strs = [display(child, 0) for child in obj.children]
    return f"{name}({', '.join(arg_strs)})"

def display_rew(obj: Object, parent_prec: int) -> str:
    """Display a rewriting rule: left symbol right"""
    symbol = obj.handle
    my_prec = get_precedence(obj)

    left, right = obj.children
    # Display children without parent context (they don't wrap themselves)
    left_str = display(left, 0)
    right_str = display(right, 0)

    # We decide if children need wrapping based on precedence + position
    if needs_parens(left, my_prec, "left"):
        left_str = f"({left_str})"
    if needs_parens(right, my_prec, "right"):
        right_str = f"({right_str})"

    result = f"{left_str} {symbol} {right_str}"

    # Wrap ourselves if our precedence is lower than parent's
    if my_prec < parent_prec:
        result = f"({result})"

    return result

def display_comp(obj: Object, parent_prec: int) -> str:
    """Display a composition: left | right"""
    my_prec = PREC_COMPOSITION

    left, right = obj.children
    # Display children without parent context (they don't wrap themselves)
    left_str = display(left, 0)
    right_str = display(right, 0)

    # We decide if children need wrapping based on precedence + position
    if needs_parens(left, my_prec, "left"):
        left_str = f"({left_str})"
    if needs_parens(right, my_prec, "right"):
        right_str = f"({right_str})"

    result = f"{left_str} | {right_str}"

    # Wrap ourselves if our precedence is lower than parent's
    if my_prec < parent_prec:
        result = f"({result})"

    return result

def display(obj: Object, parent_prec: int = 0) -> str:
    """
    Convert an Object to its string representation with minimal parentheses.

    This function is the main entry point for displaying objects. It handles:
    - Custom display overrides for specific term names
    - Church numeral detection and conversion to integers
    - Precedence-aware parenthesization
    - All object types: Term, Rew, Comp, Hole

    Args:
        obj: The object to display
        parent_prec: The precedence of the parent context (for parenthesization)

    Returns:
        String representation of the object
    """
    # Handle custom overrides for Terms
    if obj.type == "Term" and obj.handle in DISPLAY_OVERRIDES:
        result = DISPLAY_OVERRIDES[obj.handle](obj)
        if result is not None:
            # The override handled it
            return result

    # Type-specific display
    if obj.type == "Hole":
        return f"#{obj.handle}"

    elif obj.type == "Term":
        if is_infix_term(obj):
            return display_infix_term(obj, parent_prec)
        else:
            return display_prefix_term(obj, parent_prec)

    elif obj.type == "Rew":
        return display_rew(obj, parent_prec)

    elif obj.type == "Comp":
        return display_comp(obj, parent_prec)

    # Fallback to default repr
    return str(obj)

# ============================================================================
# Default Display Overrides
# ============================================================================

def display_not(obj: Object) -> Optional[str]:
    """Display logical NOT as prefix operator with ¬ symbol."""
    if len(obj.children) == 1:
        arg_str = display(obj.children[0], PREC_APPLICATION)
        # May need parens around arg if it's low precedence
        child = obj.children[0]
        if get_precedence(child, as_infix=is_infix_term(child)) < PREC_APPLICATION:
            arg_str = f"({arg_str})"
        return f"¬{arg_str}"
    return None

def display_naturals(obj: Object) -> Optional[str]:
    """Display naturals as ℕ symbol."""
    if len(obj.children) == 0:
        return "ℕ"
    return None

def display_integers(obj: Object) -> Optional[str]:
    """Display integers as ℤ symbol."""
    if len(obj.children) == 0:
        return "ℤ"
    return None

def display_reals(obj: Object) -> Optional[str]:
    """Display reals as ℝ symbol."""
    if len(obj.children) == 0:
        return "ℝ"
    return None

# Register default overrides
register_display("not", display_not)
register_display("naturals", display_naturals)
register_display("integers", display_integers)
register_display("reals", display_reals)
