(** All objects manipulated by Endive are of this type *)
type obj =
  | H of string * string (*Hole*)
  | T of string * string * obj list (*Term*)
  | R of string * string * obj * obj (*Rewrite*)
  | C of string * obj * obj (*Composition*)
