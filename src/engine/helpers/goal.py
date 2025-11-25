"""
Goal Helper

Manages usability directives
"""

from typing import Tuple, Optional
from .helper import Helper
from ...core import Object, Comp, Rew, Hole, Term, check, reduce, identify, match, apply
from .utils.goal import GoalState, Goal

# TODO : add a check when using "By", warn if not buildable and allow to add as goal anyway with a keyword?
# TODO : Allow the use of "By" with rules that have multiple premises.

class GoalHelper(Helper):
    """
    Manages goals, context, and term building.
    """

    def __init__(self) -> None:
        super().__init__()
        self.register_handler('Done', self.handle_done)
        self.register_handler('Goal', self.handle_goal)
        self.register_handler('Intro', self.handle_intro)
        self.register_handler('Status', self.handle_status)
        self.register_handler('By', self.handle_by)

        self.goal_state = GoalState()


    def handle_goal(self, argument: Object) -> Tuple[bool, str]:
        """Sets a new goal."""
        # For now, goals have to be rewritings.
        self.goal_state.set_goal(argument)
        return True, f"New goal: {self.goal_state.get_goal()}"

    def handle_intro(self) -> Tuple[bool, str]:
        """Introduces a premise into the context."""
        # Current goal should be a rewriting.
        goal = self.goal_state.get_goal()
        goal_term = goal.data['term']
        if goal_term.type != "Rew":
            return False, "Goal is not a rewriting"
        new_goal = Rew(goal_term.left, goal_term.symbol, Goal(goal_term.right, goal_term.symbol))
        self.goal_state.update_goal(new_goal)
        return True, f"New goal: {new_goal.right}"

    def handle_by(self, argument: Object, force: Optional[Object] = None, unpack: bool = False) -> Tuple[bool, str]:
        """Applies a rewriting rule to progress toward the goal."""
        # Apply the argument to a new Goal, and co-compose it with the current goal to find the new goal.
        goal = self.goal_state.get_goal()
        goal_rew = goal.data['rew']
        goal_term = goal.data['term']
        context = self.goal_state.get_context()

        # We want to unpack the multiple lefts of the nested rewritings, and then build the new goal object accordingly.

        ## we always try to apply the rule to the goal "as a term" first, and only if it fails may we consider it as a rewriting.
        if not unpack:
            term = identify(goal_term, goal_rew)
        else:
            term = goal_term

        premises = []
        current = argument
        assignements = match(term.left, current)
        while assignements is None:
            assignements = match(term.left, current)
            if assignements is not None:
                break
            if current.type != "Rew":
                if not unpack: # We retry with the goal as a rewriting.
                    return self.handle_by(argument, force, unpack=True)
                return False, f"Can't apply {argument} to obtain {term}"
            premises.append(current.left)
            current = current.right
        
        if goal_rew is None or goal_rew not in context or argument not in context[goal_rew]:
            # The rule is not buildable
            if force is None or force.symbol != "force":
                return False, f"{argument} is not a known rewriting. Use 'force' to use it anyway."
            else:
                argument = Goal(argument, goal_rew)

        building = argument

        for premise in premises:
            applied_premise = apply(premise, assignements)
            goal_premise = Goal(applied_premise, goal_rew)
            building = Comp(goal_premise, building)

        self.goal_state.update_goal(building)
        return True, f"New goal: {self.goal_state.get_goal()}"

    def handle_done(self) -> Tuple[bool, str]:
        """Marks the current goal as completed if it's in the context."""
        goal = self.goal_state.get_goal()
        goal_rew = goal.data['rew']
        goal_term = goal.data['term']
        goal_unreduced = goal.data['unreduced']
        context = self.goal_state.get_context()
        context["=>"] = context["=>"] + [Term("True", [])]

        if goal_rew is not None and goal_rew in context and goal_unreduced in context[goal_rew]:
            self.goal_state.update_goal(goal_term)
            return True, f"Goal completed: {reduce(self.goal_state.goal)}"
        return False, f"Goal not completed: {goal}"

    def handle_status(self) -> Tuple[bool, str]:
        """Shows the current goal state and context."""
        #Show all the goals

        result = "Goals:\n"
        goals = self.goal_state.get_goals()
        for goal in goals:
            result += f"  {goal}\n"
        result += "Object:\n"
        result += f"  {self.goal_state.goal}\n"
        return True, result