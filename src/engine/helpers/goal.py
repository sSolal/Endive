"""
Goal Helper

Manages usability directives
"""

from .helper import Helper
from ...core import Object, Comp, Rew, Hole, check, reduce, identify, match, apply
from .utils.goal import GoalState, Goal

# TODO : add a check when using "By", warn if not buildable and allow to add as goal anyway with a keyword?
# TODO : Allow the use of "By" with rules that have multiple premises.

class GoalHelper(Helper):
    """
    Manages goals, context, and term building.
    """

    def __init__(self):
        super().__init__()
        self.register_handler('Done', self.handle_done)
        self.register_handler('Goal', self.handle_goal)
        self.register_handler('Intro', self.handle_intro)
        self.register_handler('Status', self.handle_status)
        self.register_handler('By', self.handle_by)

        self.goal_state = GoalState()


    def handle_goal(self, argument):
        # For now, goals have to be rewritings.
        self.goal_state.set_goal(argument)
        return True, f"New goal: {self.goal_state.get_goal()}"

    def handle_intro(self):
        # Current goal should be a rewriting.
        goal = self.goal_state.get_goal()
        if goal.term.type != "Rew":
            return False, "Goal is not a rewriting"
        new_goal = Rew(goal.left, goal.term.symbol, Goal(goal.right, goal.term.symbol))
        self.goal_state.update_goal(new_goal)
        return True, f"New goal: {new_goal.right}"

    def handle_by(self, argument, force = None):
        # Apply the argument to a new Goal, and co-compose it with the current goal to find the new goal. 
        goal = self.goal_state.get_goal()
        context = self.goal_state.get_context()

        if goal.rew is None or goal.rew not in context or argument not in context[goal.rew]:
            # The rule is not buildable
            if force is None or force.symbol != "force":
                return False, f"{argument} is not a known rewriting. Use Force to use it anyway."
            else:
                argument = Goal(argument, goal.rew)

        if goal.term.type != "Rew":
            term = identify(goal.term, goal.rew)
        else:
            term = goal.term
        assignements = match(argument.right, term.left)
        if assignements is None:
            return False, f"Can't apply {argument} to obtain {term}"
        new_term = apply(argument.left, assignements)

        new_goal = Comp(Goal(new_term, goal.rew), argument)

        self.goal_state.update_goal(new_goal)
        return True, f"New goal: {new_goal.left}"

    def handle_done(self):
        goal = self.goal_state.get_goal()
        context = self.goal_state.get_context()

        if goal.rew is not None and goal.rew in context and goal.term in context[goal.rew]:
            self.goal_state.update_goal(goal.term)
            return True, f"Goal completed: {reduce(self.goal_state.goal)}"
        return False, f"Goal not completed: {goal}"

    def handle_status(self):
        return True, f"Goal: {self.goal_state.get_goal()}\ncontext: {self.goal_state.get_context()}\n proof: {self.goal_state.updated_goal(Hole("..."))}"