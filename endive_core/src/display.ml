open Objects

let rec display = function
  | T (_, f, []) -> f
  | T (_, f, children) ->
      f ^ "(" ^ String.concat ", " (List.map display children) ^ ")"
  | H (_, h) -> h
  | R (_, f, a, b) -> display a ^ " " ^ f ^ " " ^ display b
  | C (_, a, b) -> display a ^ " | " ^ display b
