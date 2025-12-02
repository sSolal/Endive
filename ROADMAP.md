# Endive's bright future

## MVP vision : a simple proof assistant to make logic and arithmetic proofs.

### Changes

*   **Import system**, add a way to import an entire file into the context.

*   **Custom display**, add a way to customize the display of certain objects (arithmetic operations).

### Helpers

*   **Build helper**, add directives to work iteratively on a object.

*   **Church helper**, build a helper that converts numeric symbols to their corresponding Church numerals.

*   **Functoriality helper**, allow the declaration of "functorial" rules, for easier nested objects rewriting.

### Quick fixes

*   **Display parentheses**, the __repr__ method of objects should take into account precedences to put parentheses where needed.

*   **Add undo**, Add an undo command to the engine. (Wait for the engine to be functional.)

*   **Add traversal utilities**, to reduce redundancy of traversing objects and mapping a function over whole objects-trees.

*   **Improve multiple goals handling**, currently, all operations are done on the first goal object found in a depth-first search...


,
## V1 vision: a proof assistant to make any kind of maths.

*   **Streamline the printing**, make a real set of helpers for a nicer CLI.

*   **Suggestions helper**, suggest tactics based on the current goal or the current object.

*   **Computation helper**, add directives to describe computational rules, and do automatic computation.

*   **Automate helper**, add directives to automatically find a proof for simple goals.

*   **GUI**, make a nice GUI for Endive.

*   **Package**, make Endive into a standalone python package

*   **Engine return objects**, allow the engine to return objects, not just strings

*   **Parsing metadata in terms**, allow terms to contain metadata to keep track of where they come from, for further updates to return messages.

### Open questions

*   When matching to a pattern such as 0 | [P], should it be able to match "0 = 0" ? How do we give the user the ability to make that match?



## Stretched dreams: a proof assistant for non-computer scientists.

*   **Type helper**, while Endive works well without a type system, it would be a nice addition to allow for more relevant errors and suggestions.

## Annex

### Functoriality helper:

> Allow the definition of "functorial" rules, which allow nested objects rewriting in an easy way. Handles the directives "Declare" with arguments (object, position, in-rew, out-rew, rew), and automatically build and add to context the rule "(\[x\] in-rew \[y\]) rew (object(...\[x\]...) out-rew object(...\[y\]...)).
> 
> Implementing this helper may require the following codebase changes:
> 
> *   The parser should allow for rule symbol to be parsed alone.
> *   The church numerals handling should be moved to a helper instead of being handled by the parser.
> *   We need some notion of global context.

### Pipeline's return mechanism

> Allow the pipeline to return objects instead of just strings.
> The handler should return a tuple of (bool, object), where bool is a success flag.
> The helpers will be able to register backward hooks to process the objects returned by the handler in the reverse order of the forward hooks.
> Handler and hooks may store data for between the forward and reverse passes inside the data field of the objects.
> And return text may be stored in the data field of the objects too, and will be displayed by the UI when the pipeline is done.

## History

### Last commits' changes:

*   **Multi premises rules**, allow the use of rules with multiple premises in goal.

### Older changes

*   **Helpers' return mechanism**, allow the helpers to act on returned objects to undo their effects.
*   **Pipeline now returns objects**, instead of just strings. Objects can be annotated, and annotations can reference children objects.
*   **Hooks and handlers return type**, unify the typing of hooks and handlers, and allow them to return annotated objects instead of just strings.
*   **Goal helper**, allow for backward sequent-calculus with multi-premises rules. (Introducing multiple goals.)
*   **Make functionnal**, get rid of ugly "copy()", and have helpers state and objects completely functional.
*   **Goal helper**, add directives to set goals, and allow backward sequent-calculus style proofs.
*   **Parser updates**, make the parser more flexible on rule symbols and rule parsing.
*   **Check helper**, add directives to check the buildability of a objects.
*   **Aliass helper**, allow to define aliases for objects and replace them in other objects.

### Roadmap's guidelines

The roadmap must stay organized in _Milestones_ (MVP, V1, V2, Dreams..., but also Urgent, and Niceties). At the top of the roadmap are functionnalities, issues, etc... only by their title, and in the right category. Greater details may be given for each item, in the following format: 

*   Context (what part of the software, what situation, what use)
*   Description (what feature we want, what is the bug to fix)
*   Details (Anything relevant to know, or that may save some time)
*   Prerequisites (Anything that must be done prior to this one, any codebase change it will entail to work)