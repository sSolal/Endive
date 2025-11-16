# Endive's bright future

## MVP vision : a simple proof assistant to make arithmetic proofs.

### Changes

*   **Parser updates**, make the parser more flexible on rule symbols and rule parsing.

*   **Helpers' state display**, add a way for helpers to display their state in a nice way.

### Helpers

*   **Goal helper**, add directives to set goals, and allow backward sequent-calculus style proofs.

*   **Build helper**, add directives to work iteratively on a object.

*   **Church helper**, move the church numerals handling from the parser to a helper.

*   **Functoriality helper**, allow the declaration of "functorial" rules, for easier nested objects rewriting.




## V1 vision: a proof assistant to make any kind of maths.

*   **Suggestions helper**, suggest tactics based on the current goal or the current object.

*   **Computation helper**, add directives to describe computational rules, and do automatic computation.

*   **Automate helper**, add directives to automatically find a proof for simple goals.

*   **GUI**, make a nice GUI for Endive.

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


## History

*   **Check helper**, add directives to check the buildability of a objects.
*   **Aliass helper**, allow to define aliases for objects and replace them in other objects.

### Roadmap's guidelines

The roadmap must stay organized in _Milestones_ (MVP, V1, V2, Dreams..., but also Urgent, and Niceties). At the top of the roadmap are functionnalities, issues, etc... only by their title, and in the right category. Greater details may be given for each item, in the following format: 

*   Context (what part of the software, what situation, what use)
*   Description (what feature we want, what is the bug to fix)
*   Details (Anything relevant to know, or that may save some time)
*   Prerequisites (Anything that must be done prior to this one, any codebase change it will entail to work)