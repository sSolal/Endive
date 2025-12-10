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
        self.register_hook(['Use'], self.use_forhook, self.use_backhook)

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

    def check_rew_to_goal(self, goal_term, argument):
        """
        Check if a rewriting can be applied to a goal to extract premises and assignments.

        Returns:
            (True, premises, assignments): On successful match
            (False, error_objects): On failure
        """
        premises = []
        current = reduce(argument)
        assignements = match(goal_term.left, current)
        while assignements is None:
            assignements = match(goal_term.left, current)
            if assignements is not None:
                break
            if current.type != "Rew":
                return False, [replace(argument, data={**argument.data, "result": f"Can't apply {argument} to obtain {goal_term}"})]
            premises.append(current.left)
            current = current.right

        # Validate premise count
        if len(premises) > 2:
            return False, [replace(argument, data={
                **argument.data,
                "result": f"Rules with more than 2 premises are not yet supported. Found {len(premises)} premises."
            })]

        return True, premises, assignements

    def build_rew_goal(self, goal_term, goal_rew, argument, premises, assignements):
        """
        Build the composition given matched premises and assignments.

        Args:
            argument: The argument to use in building (may be wrapped in Goal if forced)
        """
        # Build composition based on premise count
        if len(premises) == 2:
            building = Comp(goal_term, Comp(argument, currifier(goal_rew)))
            for premise in premises:
                applied_premise = apply(premise, assignements)
                goal_premise = Goal(applied_premise, goal_rew)
                building = Comp(goal_premise, building)
        else:
            building = Comp(argument, goal_term)
            for premise in premises:
                applied_premise = apply(premise, assignements)
                goal_premise = Goal(applied_premise, goal_rew)
                building = Comp(goal_premise, building)

        return building

    @hookify
    def handle_by(self, directive: str, argument: Object, force: Optional[Object] = None) -> Tuple[bool, List[Object]]:
        """Applies a rewriting rule to progress toward the goal."""
        goal = get_goal(self.state)
        goal_rew = goal.data['rew']
        goal_term = goal.children[0]
        context = get_context(self.state)

        term = identify(goal_term, goal_rew)

        # Try to match the rule with the goal
        match_result = self.check_rew_to_goal(term, argument)

        # If matching fails, retry considering the goal term as a rew (only if it actually is a rew)
        if not match_result[0]:
            if goal_term.type == "Rew":
                match_result = self.check_rew_to_goal(goal_term, argument)
                if not match_result[0]:
                    # Both attempts failed - return error
                    return False, match_result[1]
                # Second attempt succeeded, use goal_term for building
                term = goal_term
            else:
                # Goal is not a Rew, can't retry - return the error
                return False, match_result[1]

        # Matching succeeded - unpack results
        _, premises, assignements = match_result

        # Check buildability
        is_buildable, message = check(argument, goal_rew, context)
        if goal_rew is None or not is_buildable:
            if force is None or force.symbol != "force":
                return False, [replace(argument, data={**argument.data, "result": "[] is not a known rewriting. Use 'force' to use it anyway."})]
            else:
                # Force was provided - wrap argument in Goal to make it usable
                argument = Goal(argument, goal_rew)

        # Build composition with the (possibly wrapped) argument
        building = self.build_rew_goal(term, goal_rew, argument, premises, assignements)

        # Update state and return
        new_state, _ = update_goal(self.state, building)
        self.set_state(new_state)
        new_goal = get_goal(self.state)
        return True, [replace(new_goal, data={**new_goal.data, "result": "New goal: []"})]

    @hookify
    def handle_done(self, directive: str, candidate: Object = None) -> Tuple[bool, List[Object]]:
        """Marks the current goal as completed if the provided candidate is buildable, or the goal is in the context."""
        goal = get_goal(self.state)

        # Guard against no active goals
        if goal is None:
            return False, [Term("Error", data={"result": "No active goals"})]

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

            return False, [replace(goal, data={**goal.data, "result": "Candidate does not complete the goal: []"})]
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
    def use_forhook(self, directive: str, rule: Object) -> List[Object]:
        """Check buildability of rule argument, store warning if needed."""
        goal = get_goal(self.state)

        if goal is None:
            return [rule]

        goal_rew = goal.data.get('rew')
        context = get_context(self.state)

        is_buildable, message = check(rule, goal_rew, context)

        if not is_buildable:
            # Store warning in temporary state for backhook to use
            self.hooks_state['buildability_warning'] = True

        return [rule]

    @hookify
    def use_backhook(self, directive: str, result: Object) -> List[Object]:
        """Add buildability warning to result if forhook detected non-buildable rule."""

        if not self.hooks_state.get('buildability_warning', False):
            return [result]

        existing_result = result.data.get('result', '')
        if existing_result:
            warning_msg = existing_result + " (Warning: the rule you used is not buildable)"
        else:
            warning_msg = "(Warning: the rule you used is not buildable)"

        return [replace(result, data={**result.data, "result": warning_msg})]

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