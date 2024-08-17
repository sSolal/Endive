(** All objects manipulated by Endive are of this type *)
type obj =
  | H of string * string (*Hole*)
  | T of string * string * obj list (*Term*)
  | R of string * string * obj * obj (*Rewrite*)
  | C of string * obj * obj (*Composition*)

let unpack = function
  | T (_, n, _) -> n
  | _ -> failwith "Trying to unpack a non-term object"

(** Get the pattern (left) side of a rule *)
let get_pattern = function
  | R (_, _, pattern, _) -> pattern
  | _ -> failwith "Trying to get the pattern of a non-rule object"

let get_result = function
  | R (_, _, _, result) -> result
  | _ -> failwith "Trying to get the result of a non-rule object"

let get_sys = function
  | R (_, sys, _, _) -> sys
  | _ -> failwith "Trying to get the system of a non-rule object"

(** Get the list of holes in an object *)
let rec get_holes = function
  | H (_, name) -> [ name ]
  | T (_, _, children) -> List.concat (List.map get_holes children)
  | R (_, _, pattern, result) -> get_holes pattern @ get_holes result
  | C (_, obj, rule) -> get_holes obj @ get_holes rule

(** Compare two objects while discarding differences of ids *)
let rec equals a b =
  match (a, b) with
  | H (_, name), H (_, name') -> name = name'
  | T (_, f, children), T (_, f', children') ->
      f = f' && List.for_all2 equals children children'
  | R (_, v, l, r), R (_, v', l', r') -> v = v' && equals l l' && equals r r'
  | C (_, l, r), C (_, l', r') -> equals l l' && equals r r'
  | _ -> false

(** Annotate holes to avoid collision with holes from another object. *)
let alpha_convert model obj =
  let hole_names = get_holes model in
  let rec aux = function
    | H (id, name) as h ->
        if List.mem name hole_names then aux (H (id, name ^ "'")) else h
    | T (id, f, children) -> T (id, f, List.map aux children)
    | R (id, v, l, r) -> R (id, v, aux l, aux r)
    | C (id, l, r) -> C (id, aux l, aux r)
  in
  aux obj
