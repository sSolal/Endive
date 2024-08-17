open Display
open Objects

(* Some constants relative to the specific system we deal with*)
let truth = T ("", "True", [])
let base_sys = "=>"

(* The proof state *)
let current_term = ref (H ("", "h0"))
let scopes = ref [ "h0" ]

(*The current term is just a term with holes annotated as such in "scopes" *)

let reset _ =
  current_term := H ("", "h0");
  scopes := [ "h0" ];
  "Ok"

let show_term _ = display !current_term

let set_scope arg =
  let scope = unpack (arg 0) in
  if List.mem scope !scopes then (
    current_term := Kernel.apply_map [ (scope, arg 1) ] !current_term;
    scopes := List.filter (fun x -> x <> scope) !scopes;
    "Ok")
  else "Scope " ^ scope ^ " is not in " ^ String.concat ", " !scopes

let add_scope arg =
  let scope = unpack (arg 0) in
  if List.mem scope (get_holes !current_term) then
    if not (List.mem scope !scopes) then (
      scopes := scope :: !scopes;
      "Ok")
    else "Scope " ^ scope ^ " is already defined"
  else "Scope " ^ unpack (arg 0) ^ " is not a hole in " ^ display !current_term

let check _ =
  match Kernel.check [] base_sys !current_term with
  | Some obj -> display obj ^ " is not ok"
  | None -> "Ok"

let list _ = String.concat ", " !scopes

let commands =
  [
    ("set", set_scope);
    ("check", check);
    ("show", show_term);
    ("add", add_scope);
    ("reset", reset);
    ("list", list);
  ]

let call command (args : obj list) =
  try
    let arg x =
      if x >= List.length args then failwith "Not enough arguments"
      else List.nth args x
    in
    if List.mem_assoc command commands then (List.assoc command commands) arg
    else "Unknown command " ^ command
  with Failure e -> e
