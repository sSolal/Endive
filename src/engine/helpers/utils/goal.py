from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from ....core import Object, Comp, Rew, Hole, Term, check, reduce, identify, match, apply


def Goal(term: Object, rew: Optional[str] = None) -> Object:
    """
    Creates a goal object representing a goal left to prove in a backward sequent-calculus style proof.
    The goal emulates a term, but is not a term itself.
    Stores both reduced (for display) and unreduced (for composition) forms.
    """
    reduced_term = reduce(term)
    goal_data = {'term': reduced_term, 'unreduced': term, 'rew': rew}
    return Object("Goal", term.children, term.handle,
                  lambda self: f"[{self.data['rew'] if self.data['rew'] is not None else ''}{str(self.data['term'])}]",
                  goal_data)


# Type alias for generic context: tuple of (symbol, term) pairs
GenericContext = Tuple[Tuple[str, Object], ...]


@dataclass(frozen=True)
class GoalState:
    """Immutable state for goal-directed proving"""
    goal: Optional[Object] = None  # Current term with Goal placeholders
    generic_context: GenericContext = (("=>", Term("True", ())),)  # Default context


def set_goal(state: GoalState, new_goal: Object) -> Tuple[GoalState, Object]:
    """Set a new goal. Returns (new_state, goal_object)."""
    goal_obj = Goal(new_goal)
    new_state = GoalState(goal=goal_obj, generic_context=state.generic_context)
    return new_state, goal_obj


def get_goal(state: GoalState, obj: Optional[Object] = None) -> Optional[Object]:
    """Find the first Goal object in the tree."""
    if obj is None:
        return get_goal(state, state.goal) if state.goal is not None else None
    if obj.type == "Goal":
        return obj
    for child in obj.children:
        result = get_goal(state, child)
        if result is not None:
            return result
    return None


def get_goals(state: GoalState, obj: Optional[Object] = None) -> List[Object]:
    """Find all Goal objects in the tree."""
    if obj is None:
        return get_goals(state, state.goal) if state.goal is not None else []
    if obj.type == "Goal":
        return [obj]
    return [goal for child in obj.children for goal in get_goals(state, child)]


def add_axiom(state: GoalState, rule_symbol: str, term: Object) -> GoalState:
    """Return new state with axiom added to context."""
    new_context = state.generic_context + ((rule_symbol, term),)
    return GoalState(goal=state.goal, generic_context=new_context)


def get_context(state: GoalState, obj: Optional[Object] = None,
                context: Optional[Dict[str, List[Object]]] = None) -> Optional[Dict[str, List[Object]]]:
    """Build context dict from goal tree and generic context."""
    if context is None:
        context = {}
    else:
        context = dict(context)

    if obj is None:
        if state.goal is not None:
            result = get_context(state, state.goal)
        else:
            result = {}

        if result is None:
            result = {}
        # Merge generic context (convert tuple to dict)
        for symbol, term in state.generic_context:
            if symbol not in result:
                result[symbol] = []
            result[symbol] = result[symbol] + [term]
        return result

    if obj.type == "Goal":
        return context
    elif obj.type == "Rew":
        new_context = dict(context)
        if obj.symbol not in new_context:
            new_context[obj.symbol] = []
        else:
            new_context[obj.symbol] = list(new_context[obj.symbol])
        new_context[obj.symbol].append(obj.left)
        return get_context(state, obj.right, new_context)
    elif obj.type == "Comp":
        result_left = get_context(state, obj.left, context)
        if result_left is not None:
            return result_left
        return get_context(state, obj.right, context)
    else:
        return None


def updated_goal(state: GoalState, new_goal: Object, obj: Optional[Object] = None) -> Object:
    """Recursively replaces the first Goal found with new_goal."""
    def recursive_update(new_goal: Object, obj: Object) -> Tuple[Object, bool]:
        if obj.type == "Goal":
            return new_goal, True
        new_children = []
        updated = False
        for child in obj.children:
            if not updated:
                result, was_updated = recursive_update(new_goal, child)
                if was_updated:
                    new_children.append(result)
                    updated = True
                else:
                    new_children.append(child)
            else:
                new_children.append(child)
        if updated:
            return Object(obj.type, tuple(new_children), obj.handle, obj.repr_func, dict(obj.data)), True
        return obj, False

    result, _ = recursive_update(new_goal, state.goal if obj is None else obj)
    return result


def update_goal(state: GoalState, new_goal: Object) -> Tuple[GoalState, Object]:
    """Update goal with new value. Returns (new_state, updated_goal)."""
    new_goal_term = updated_goal(state, new_goal)
    new_state = GoalState(goal=new_goal_term, generic_context=state.generic_context)
    return new_state, new_goal_term

def currifier(symbol: str) -> Object:
        """
        Constructs the lemma: ([X] => ([Y] => [Z])) => (([Z] => [W]) => ([X] => ([Y] => ([W])))
        (With proof :
        ([X] => ([Y] => [Z])) => (([Z] => [W]) => ([X] => ([Y] => (([Y] | ([X] | ([X] => [Y] => [Z]))) | [Z] => [W]))))
        )
        
        This lemma enables composing 2-premise curried rewritings with a rewriting that is expected to act on their result.
        It allows us to properly reduce compositions with objects such as (A => (B => X)) and (X => Y).

        Args:
            symbol: The rewriting symbol (e.g., "=>")

        """
        X, Y, Z, W = Hole("X"), Hole("Y"), Hole("Z"), Hole("W")
        inner = Rew(X, symbol, Rew(Y, symbol, Z))
        transformation = Rew(Z, symbol, W)
        result = Rew(X, symbol, Rew(Y, symbol, Comp(Comp(Y, Comp(X, inner)), transformation)))
        return Rew(inner, symbol, Rew(transformation, symbol, result))