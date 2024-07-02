(** All objects manipulated by Endive are of this type *)
type obj =
  | H of string * string (*Hole*)
  | T of string * string * obj list (*Term*)
  | R of string * string * obj * obj (*Rewrite*)
  | C of string * obj * obj (*Composition*)

let rec get_holes = function
  | H (_, name) -> [ name ]
  | T (_, _, children) -> List.concat (List.map get_holes children)
  | R (_, _, pattern, result) -> get_holes pattern @ get_holes result
  | C (_, obj, rule) -> get_holes obj @ get_holes rule
