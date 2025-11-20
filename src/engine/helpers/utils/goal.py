from typing import Optional, Dict, List, Tuple
from ....core import Object, Comp, Rew, Hole, check, reduce, identify, match, apply

def Goal(term: Object, rew: Optional[str] = None) -> Object:
    """
    Creates a goal object representing a goal left to prove in a backward sequent-calculus style proof.
    The goal emulates a term, but is not a term itself.
    """
    goal_data = {'term': term, 'rew': rew}
    return Object("Goal", term.children, term.handle,
                  lambda self: f"[{self.data['rew'] if self.data['rew'] is not None else ''}{str(self.data['term'])}]",
                  goal_data)

class GoalState:
    def __init__(self) -> None:
        self.goal: Optional[Object] = None  # Current term being built towards the goal.
        # This term is kind of a "partial" term, containing "Goal" objects where there are things left to prove.

    def set_goal(self, new_goal: Object) -> Object:
        self.goal = Goal(new_goal)
        return self.goal

    def get_goal(self, obj: Optional[Object] = None) -> Optional[Object]:
        if obj is None:
            return (self.get_goal(self.goal) if self.goal is not None else None)
        if obj.type == "Goal":
            return obj
        else:
            for child in obj.children:
                result = self.get_goal(child)
                if result is not None:
                    return result
        return None


    def get_context(self, obj: Optional[Object] = None, context: Optional[Dict[str, List[Object]]] = None) -> Optional[Dict[str, List[Object]]]:
        if context is None:
            context = {}
        else:
            # Create a shallow copy of the dict, but share the lists (we'll append to new lists if needed)
            context = dict(context)

        if obj is None:
            return (self.get_context(self.goal) if self.goal is not None else None)
        if obj.type == "Goal":
            return context
        elif obj.type == "Rew":
            new_context = dict(context)
            if obj.symbol not in new_context:
                new_context[obj.symbol] = []
            else:
                new_context[obj.symbol] = list(new_context[obj.symbol])
            new_context[obj.symbol].append(obj.left)
            return self.get_context(obj.right, new_context)
        elif obj.type == "Comp":
            result_left = self.get_context(obj.left, context)
            if result_left is not None:
                return result_left
            return self.get_context(obj.right, context)
        else:
            return None

        

    def updated_goal(self, new_goal: Object, obj: Optional[Object] = None) -> Object:
        """Recursively replaces the first Goal found with new_goal."""
        def recursive_update(new_goal: Object, obj: Object) -> Tuple[Object, bool]:
            if obj.type == "Goal":
                return new_goal, True
            else:
                # Try to update children
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
                    return Object(obj.type, tuple(new_children), obj.handle, obj.repr_func, obj.data), True
            return obj, False

        result, _ = recursive_update(new_goal, self.goal if obj is None else obj)
        return result

    def update_goal(self, new_goal: Object) -> Object:
        new_goal_term = self.updated_goal(new_goal)
        self.goal = new_goal_term
        return self.goal
