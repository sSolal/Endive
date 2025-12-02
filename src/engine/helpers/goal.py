"""
Goal Helper

Manages usability directives
"""

from typing import Tuple, Optional, List
from dataclasses import replace
from .helper import Helper, hookify
from ...core import Object, Comp, Rew, Hole, Term, check, reduce, identify, match, apply
from .utils.goal import GoalState, Goal, currifier


# TODO : Extend currifier approach to support 3+ premise rewritings
# TODO : When there are no goals left, Done should give a nice message.

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

    @hookify
    def handle_goal(self, directive: str, argument: Object) -> Tuple[bool, List[Object]]:
        """Sets a new goal."""
        # For now, goals have to be rewritings.
        self.goal_state.set_goal(argument)
        goal = self.goal_state.get_goal()
        return True, [replace(goal, data={**goal.data, "result": "New goal: []"})]

    @hookify
    def handle_intro(self, directive: str) -> Tuple[bool, List[Object]]:
        """Introduces a premise into the context."""
        # Current goal should be a rewriting.
        goal = self.goal_state.get_goal()
        goal_term = goal.data['term']
        if goal_term.type != "Rew":
            return False, [replace(goal, data={**goal.data, "result": "Goal is not a rewriting"})]
        new_goal = Rew(goal_term.left, goal_term.symbol, Goal(goal_term.right, goal_term.symbol))
        self.goal_state.update_goal(new_goal)
        return True, [replace(new_goal.right, data={**new_goal.right.data, "result": "New goal: []"})]

    @hookify
    def handle_by(self, directive: str, argument: Object, force: Optional[Object] = None, unpack: bool = False) -> Tuple[bool, List[Object]]:
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
                    return self.handle_by(directive, argument, force, unpack=True)
                return False, [replace(argument, data={**argument.data, "result": f"Can't apply {argument} to obtain {term}"})]
            premises.append(current.left)
            current = current.right

        # Error if more than 2 premises
        if len(premises) > 2:
            return False, [replace(argument, data={
                **argument.data,
                "result": f"Rules with more than 2 premises are not yet supported. Found {len(premises)} premises."
            })]

        if goal_rew is None or goal_rew not in context or argument not in context[goal_rew]:
            # The rule is not buildable
            if force is None or force.symbol != "force":
                return False, [replace(argument, data={**argument.data, "result": "[] is not a known rewriting. Use 'force' to use it anyway."})]
            else:
                argument = Goal(argument, goal_rew)

        # Build composition based on premise count
        if len(premises) == 2:
            
            building = Comp(term, Comp(argument, currifier(goal_rew)))

            # Wrap premises as Goals (B before A in composition)
            for premise in premises:
                applied_premise = apply(premise, assignements)
                goal_premise = Goal(applied_premise, goal_rew)
                building = Comp(goal_premise, building)
        else:
            # Original behavior for 0, 1 premise cases
            building = Comp(argument, term)

            for premise in premises:
                applied_premise = apply(premise, assignements)
                goal_premise = Goal(applied_premise, goal_rew)
                building = Comp(goal_premise, building)

        self.goal_state.update_goal(building)
        new_goal = self.goal_state.get_goal()
        return True, [replace(new_goal, data={**new_goal.data, "result": "New goal: []"})]

    @hookify
    def handle_done(self, directive: str) -> Tuple[bool, List[Object]]:
        """Marks the current goal as completed if it's in the context."""
        goal = self.goal_state.get_goal()
        goal_rew = goal.data['rew']
        goal_term = goal.data['term']
        goal_unreduced = goal.data['unreduced']
        context = self.goal_state.get_context()
        context["=>"] = context["=>"] + [Term("True", [])]

        if goal_rew is not None and goal_rew in context and goal_unreduced in context[goal_rew]:
            self.goal_state.update_goal(goal_term)
            completed = reduce(self.goal_state.goal)
            return True, [replace(completed, data={**completed.data, "result": "Goal completed: []"})]
        return False, [replace(goal, data={**goal.data, "result": "Goal not completed: []"})]

    @hookify
    def handle_status(self, directive: str) -> Tuple[bool, List[Object]]:
        """Shows the current goal state and context."""
        #Show all the goals

        result = "Goals:\n"
        goals = self.goal_state.get_goals()
        for goal in goals:
            result += f"  {goal}\n"
        result += "Object:\n"
        result += f"  {self.goal_state.goal}\n"
        # Return a Term with the result for display
        return True, [Term("Status", data={"result": result})]