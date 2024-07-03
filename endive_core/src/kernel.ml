open Objects

type substitution = (string * obj) list [@@deriving sexp, compare]

(** Applies a substitution map (typically generated by {!unify}) to a term*)
let rec apply_map map = function
  | H (_id, name) as h -> (
      match List.assoc_opt name map with Some obj -> obj | None -> h)
  | T (id, f, children) -> T (id, f, List.map (apply_map map) children)
  | R (id, v, l, r) -> R (id, v, apply_map map l, apply_map map r)
  | C (id, l, r) -> C (id, apply_map map l, apply_map map r)

(** Applies a unification algorithm to two patterns. On success, returns a substitution map (association list) with a term for every hole.*)
let unify a b =
  let rec aux map remaining =
    match remaining with
    | [] -> map
    | (a, b) :: remaining -> (
        match (a, b) with
        | o, o' when o = o' -> aux map remaining
        | H (_, name), o when not (List.mem name (get_holes o)) ->
            let new_sub = (name, o) in
            aux (new_sub :: map)
              (List.map
                 (fun (x, y) ->
                   ((apply_map [ new_sub ]) x, (apply_map [ new_sub ]) y))
                 remaining)
        | o, H (_, name) when not (List.mem name (get_holes o)) ->
            let new_sub = (name, o) in
            aux (new_sub :: map)
              (List.map
                 (fun (x, y) ->
                   ((apply_map [ new_sub ]) x, (apply_map [ new_sub ]) y))
                 remaining)
        | T (_, f, children), T (_, f', children') when f = f' ->
            aux map (List.combine children children' @ remaining)
        | R (_, v, left, right), R (_, v', left', right') when v = v' ->
            aux map ((left, left') :: (right, right') :: remaining)
        | C (_, left, right), C (_, left', right') ->
            aux map ((left, left') :: (right, right') :: remaining)
        | _ ->
            failwith
              ("Can not unify" ^ Display.display a ^ " and " ^ Display.display b)
        )
  in
  aux [] [ (a, b) ]

(** Compute the reduction of composing two terms when it is not ambiguous *)
let compose left right =
  match left with
  | R (_, v, ll, lr) -> (
      (*If the first is a rewrite*)
      match alpha_convert left right with
      (*Avoid collision between left and right objects holes' names*)
      | R (id, v', rl, rr) when v = v' ->
          let map = unify lr rl in
          R (id, v, apply_map map ll, apply_map map rr)
      | R _ ->
          failwith
            ("Ambiguous composition of " ^ Display.display left ^ " and "
           ^ Display.display right)
      | o ->
          let map = unify lr o in
          apply_map map ll)
  | o -> (
      match alpha_convert o right with
      | R (_, _, rl, rr) ->
          let map = unify o rl in
          apply_map map rr
      | _ ->
          failwith
            ("Can not reduce non-rewrites " ^ Display.display left ^ " and "
           ^ Display.display right))

(** Reduce an expression as much as possible *)
let rec reduce = function
  | C (id, left, right) -> (
      let l = reduce left and r = reduce right in
      try compose l r with _ -> C (id, l, r)
      (*reduce whenever it is possible*))
  | R (id, t, left, right) -> R (id, t, reduce left, reduce right)
  | T (id, t, children) -> T (id, t, List.map reduce children)
  | h -> h
