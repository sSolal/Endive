from ....core import Object, Comp, Rew, Hole, check, reduce, identify, match, apply
from copy import deepcopy as copy

class Goal(Object):
    """
    Represents a goal left to prove in a backward sequent-calculus style proof.
    The goal emulates a term, but is not a term itself.
    """
    def __init__(self, term, rew = None):
        super().__init__("Goal", term.children, term.handle, term.repr)
        self.term = term
        self.rew = rew
        self.repr = lambda self: f"[{self.rew if self.rew is not None else ""}{str(self.term)}]"

class GoalState:
    def __init__(self):
        self.goal = None # Current term being built towards the goal.
        # This term is kind of a "partial" term, containing "Goal" objects where there are things left to prove.

    def set_goal(self, new_goal):
        self.goal = Goal(new_goal)
        return self.goal

    def get_goal(self, obj = None):
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


    def get_context(self, obj = None, context = {}):
        context = copy(context)
        if obj is None:
            return (self.get_context(self.goal) if self.goal is not None else None)
        if obj.type == "Goal":
            return context
        elif obj.type == "Rew":
            if obj.symbol not in context:
                context[obj.symbol] = []
            context[obj.symbol].append(obj.left)
            return self.get_context(obj.right, context)
        elif obj.type == "Comp":
            result_left = self.get_context(obj.left, context)
            if result_left is not None:
                return result_left
            return self.get_context(obj.right, context)
        else:
            return None

        

    def updated_goal(self, new_goal, obj = None):

        def recursive_update(new_goal, obj):
            if obj.type == "Goal":
                return new_goal, True
            else:
                new_obj = copy(obj)
                for i, child in enumerate(new_obj.children):
                    result, updated = recursive_update(new_goal, child)
                    if updated:
                        new_obj.children[i] = result
                        return new_obj, True
            return obj, False

        result,_ = recursive_update(new_goal, self.goal if obj is None else obj)
        return result

    def update_goal(self, new_goal):
        new_goal_term = self.updated_goal(new_goal)
        self.goal = new_goal_term
        return self.goal
