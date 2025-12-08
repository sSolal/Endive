"""
Goal Helper

Manages usability directives
"""

from typing import Tuple, Optional, List
from dataclasses import replace
from .helper import Helper, hookify
from ...core import Object, Comp, Rew, Hole, Term, check, reduce, identify, match, apply
from .utils.goal import (
    GoalState, Goal, currifier,
    set_goal, get_goal, get_goals, get_context, update_goal, add_axiom
)


# TODO : Extend currifier approach to support 3+ premise rewritings
# TODO : When there are no goals left, Done should give a nice message.

class GoalHelper(Helper[GoalState]):
    """
    Manages goals, context, and term building.
    State: GoalState (goal, generic_context)
    """

    def __init__(self) -> None:
        super().__init__(GoalState())
        self.register_handler('Done', self.handle_done)
        self.register_handler('Goal', self.handle_goal)
        self.register_handler('Intro', self.handle_intro)
        self.register_handler('Status', self.handle_status)
        self.register_handler('By', self.handle_by)
        self.register_handler('Axiom', self.handle_axiom)

    @hookify
    def handle_goal(self, directive: str, argument: Object) -> Tuple[bool, List[Object]]:
        """Sets a new goal."""
        # For now, goals have to be rewritings.
        new_state, goal_obj = set_goal(self.state, argument)
        self.set_state(new_state)
        goal = get_goal(self.state)
        return True, [replace(goal, data={**goal.data, "result": "New goal: []"})]

    @hookify
    def handle_intro(self, directive: str) -> Tuple[bool, List[Object]]:
        """Introduces a premise into the context."""
        goal = get_goal(self.state)
        goal_term = goal.children[0]
        if goal_term.type != "Rew":
            return False, [replace(goal, data={**goal.data, "result": "Goal is not a rewriting"})]
        new_goal = Rew(goal_term.left, goal_term.symbol, Goal(goal_term.right, goal_term.symbol))
        new_state, _ = update_goal(self.state, new_goal)
        self.set_state(new_state)
        return True, [replace(new_goal.right, data={**new_goal.right.data, "result": "New goal: []"})]

    @hookify
    def handle_by(self, directive: str, argument: Object, force: Optional[Object] = None, unpack: bool = False) -> Tuple[bool, List[Object]]:
        """Applies a rewriting rule to progress toward the goal."""
        # Apply the argument to a new Goal, and co-compose it with the current goal to find the new goal.
        goal = get_goal(self.state)
        goal_rew = goal.data['rew']
        goal_term = goal.children[0]
        context = get_context(self.state)

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
                if not unpack:  # Retry with the goal as a rewriting
                    return self.handle_by(directive, argument, force, unpack=True)
                return False, [replace(argument, data={**argument.data, "result": f"Can't apply {argument} to obtain {term}"})]
            premises.append(current.left)
            current = current.right

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
            building = Comp(argument, term)
            for premise in premises:
                applied_premise = apply(premise, assignements)
                goal_premise = Goal(applied_premise, goal_rew)
                building = Comp(goal_premise, building)

        new_state, _ = update_goal(self.state, building)
        self.set_state(new_state)
        new_goal = get_goal(self.state)
        return True, [replace(new_goal, data={**new_goal.data, "result": "New goal: []"})]

    @hookify
    def handle_done(self, directive: str, candidate: Object = None) -> Tuple[bool, List[Object]]:
        """Marks the current goal as completed if the provided candidate is buildable, or the goal is in the context."""
        goal = get_goal(self.state)
        goal_rew = goal.data['rew']
        goal_term = goal.children[0]
        goal_unreduced = goal.data['unreduced']
        context = get_context(self.state)

        if candidate is not None:
            # Forward-chaining: check both buildability and reduction
            is_buildable, message = check(candidate, goal_rew, context)
            # Reduce the candidate first
            reduced_candidate = reduce(candidate)
            reduces_to_goal = reduced_candidate == goal_term

            if is_buildable and reduces_to_goal:
                new_state, _ = update_goal(self.state, candidate)
                self.set_state(new_state)
                completed = reduce(self.state.goal)
                return True, [replace(completed, data={**completed.data, "result": "Goal completed: []"})]

            if is_buildable and reduced_candidate.type == "Rew": # Second chance : check buildability of the left and the buildability
                is_buildable_left, message = check(reduced_candidate.left, goal_rew, context)
                reduced_candidate_right = reduce(reduced_candidate.right)
                reduces_to_goal = reduced_candidate_right == goal_term

                if is_buildable_left and reduces_to_goal:
                    new_state, _ = update_goal(self.state, Comp(reduced_candidate.left, candidate))
                    self.set_state(new_state)
                    completed = reduce(self.state.goal)
                    return True, [replace(completed, data={**completed.data, "result": "Goal completed: []"})]

            return False, [replace(goal, data={**goal.data, "result": "Goal not completed: []"})]
        else:
            # Backward-chaining: check if goal is buildable in context
            if goal_rew is not None and goal_rew in context and goal_unreduced in context[goal_rew]:
                new_state, _ = update_goal(self.state, goal_term)
                self.set_state(new_state)
                completed = reduce(self.state.goal)
                return True, [replace(completed, data={**completed.data, "result": "Goal completed: []"})]
            return False, [replace(goal, data={**goal.data, "result": "Goal not completed: []"})]

    @hookify
    def handle_status(self, directive: str) -> Tuple[bool, List[Object]]:
        """Shows the current goal state and context."""
        result = "Goals:\n"
        goals = get_goals(self.state)
        for goal in goals:
            result += f"  {goal}\n"
        result += "Object:\n"
        result += f"  {self.state.goal}\n"
        return True, [Term("Status", data={"result": result})]

    @hookify
    def handle_axiom(self, directive: str, *args: Object) -> Tuple[bool, List[Object]]:
        """Add a term to the generic context.

        Usage:
            Axiom True          # Adds True to => context
            Axiom <=>, True     # Adds True to <=> context
        """
        if len(args) == 1:
            rule_symbol = "=>"
            axiom_term = args[0]
        elif len(args) == 2:
            if args[0].type == "Term":
                rule_symbol = args[0].symbol
            else:
                rule_symbol = getattr(args[0], 'symbol', str(args[0]))
            axiom_term = args[1]
        else:
            return False, [Term("Error", data={"result": f"Axiom expects 1 or 2 arguments, got {len(args)}"})]

        self.set_state(add_axiom(self.state, rule_symbol, axiom_term))
        return True, [replace(axiom_term, data={**axiom_term.data, "result": f"Added [] to context for {rule_symbol}"})]