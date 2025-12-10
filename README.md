# Endive

Endive is a proof assistant based on rewriting.

## Syntax

```
directive ::= directive_symbol term (, term)*
object ::= symbol, symbol(object, object...), [hole], object | object, object rule_symbol object, (object)
rule_symbol ::= =, =>, <=>, ->...
directive_symbol ::= Axiom, Axiom, Goal, Start, Use...
```

A `[hole]` is an object that kind of takes the role of variables, `term rule_symbol term` is just called a "rule", and `term | term` is called an application. The parenthesis in (term) are here to allow forcing some priorities in the parsing.

For instance,

```
Axiom A
Axiom h, A => B
Axiom h2, B => C
Goal C
Start A
Use h | h2
```

## Buildability

The core function of Endive is to help you build objects, and check that objects are indeed buildable.

An object is said to be _buildable_ in a specific _context_, for a given _rule_, if :

1.  It's already in the context (axiom)
2.  It's a composition of two buildable objects
3.  It's a rewrite where the output is buildable for the rule with input added to context

## Reduction

### Pattern Matching

Pattern matching is the process of finding an assignment of holes in an object that makes it equal to another object. In Endive, holes are represented as `[name]` and act as placeholders for variables.

**Example:**

*   Object: `f(x, g(y))`
*   Pattern: `f([a], g([b]))`
*   Match: `[a] = x` and `[b] = y`

The pattern matching algorithm recursively traverses both the pattern and the concrete term, checking:

1.  If the pattern is a hole `[name]`, it assigns the corresponding part of the term to that hole
2.  If the pattern is a term, it checks that names and structure match, then recursively matches all arguments
3.  If the pattern is an application, it matches both the function and argument parts

### Rule Application and Reduction

A term of the form `rule | rule` is called an **application**. Rules have two parts: a **pattern** (input) and a **result** (output).  
Note that rules and terms are the same "type" in Endive. In what follows, we will only talk about rules, but one can consider that a term is just a rule with the term both as pattern and result.

A composition is said to be _reducible_ if it is of the form `A -> B | B' -> C` where `->` represents any rule symbol and `B` and `B'` match.

**Rule Application Process:**

1.  **Pattern Matching**: Check if the second's part pattern matches the first's part result
2.  **Assignment**: If match succeeds, create assignments for all holes in the second's part pattern
3.  **Substitution**: Apply assignments to the second's part result, replacing holes with their assigned values
4.  **Result**: Return the resulting term

In a nutshell, `A -> B | B' -> D` reduces to `A -> D` if `B` and `B'` match.

Note that patterns of type `A | A' -> B` and `A -> B | B` are also reducible, reading them as `A -> A | A' -> B` and `A -> B | B' -> B` respectively. For legibility, one may however want to sometimes apply a rewriting to an object (that is not a rewriting), and obtain an object. See the section on syntactic sugar for logic.

### Reduction

Reduction is the process of simplifying objects by reducing reducible compositions.  
Depending on the term, reduction may emulate the behavior of a computation, of a construction, of a dynamical system, or even compute the proven result of a proof.

## Functoriality

The expressive power of Endive relies on the concept of functoriality. Functoriality is what allows to use rewriting rules inside nested components without making a mistake.

For instance, one having proven that 3 \<= 4 may want to use that to prove that 3 \* 2 \<= 4 \* 2.

To do that, you apply the functorial rewriting `(a <= b) => (a * c <= b * c)` to the object `3 <= 4`, and you get `3 * 2 <= 4 * 2`.

Note that functorial rewritings in expanded form look ugly, but the information they hold is very compact : "\*" is functorial for "\<=" on its "second" argument.

## Syntactic sugar

Since a lot of proofs will contain numbers, we have parsing level syntactic sugar for numbers, arithmetic operations, etc...

```
3 + 4 parses as plus(S(S(S(zero)))), S(S(S(S(zero))))
0 parses as zero
```

Similarly, we have specific parser constructs for quantifiers

```
forall [x] in N, P parses as forall(N, [x] -> P) (where P may contains occurences of [x] of course)
```

Since one of the use cases of Endive is to work with logic, and to prove theorems within a given logic system, we may soon want to be able to talk about "theorems" and not just "implications", as the condition on rules seems to force us to do.

To allow for this, we will add automatic translations between a term `A` and its corresponding "meaning" `True -> A`. This will allow us to for instance set a goal such as `B`, and then apply rules to transform terms one after another until we reach `B`, when in the background what we are actually proving is `True -> B`, and building steps of type `True -> ...` until we reach `True -> B`.

## Codebase structure

### Core

#### Objects

*   Object (abstract syntax tree object)
    *   Equality check
*   Term (Object)
    *   Name, arguments
*   Rew (Object)
    *   Symbol, left, right
*   Comp (Object)
    *   Left, right
*   Hole (Object)
    *   Name

#### Operations

*   Match (A: Object, B: Object) -> Assignments for holes of B to match A
*   Apply (B: Object, assignements)
*   Compose(A: Rew, B: Rew) -> Match A's right with B's left, and return the rew with A's left and B's right with assignements applied to the latter, and both's common symbol.
*   (Cocompose(A: Rew, B: Rew) -> Match B's left with A's right, and return the rew with A's left and B's right with assignements applied to the former, and both's common symbol.)
*   Reduce (A: Object) -> Find all reducible compositions and apply them.
*   ReduceFully (A: Object) -> Reduce until no more reductions are possible.

#### Buildability

*   Check(A: Object, context) -> Check buildability as defined above.

### Engine

#### Parser

The parser contains all the syntactic sugar.

*   Tokenize(line)
*   Parse(tokens list)
*   ParseLine(line) (Parses one directive followed by a comma separated list of Objects.)

#### Pipeline

*   Pipeline (register helpers, and call them in order for a given directive and arguments)
    *   process(directive, arguments)
    *   clear() (clears the state of all helpers)

#### Helpers

*   Helper (abstract class)
    *   forhooks / backhooks
    *   handlers
*   AliasHelper (allows for definition and substitutes aliases in objects)
*   GoalHelper (manages proof goals with directives: Goal, Intro, By, Axiom, Done, Status)
*   BuildHelper (manages forward-chaining proofs with directives: Start, Use, Clear, Check)
*   FunctorialHelper (manages functorial rewriting rules)
*   PeanoHelper (provides Peano arithmetic support)