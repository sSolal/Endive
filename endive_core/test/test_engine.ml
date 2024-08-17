open Endive_core.Engine
open Scripts
open Endive_core.Objects

let obj1 = h "a"
let obj2 = a "b"

let setup commands =
  ignore (reset ());
  List.iter (fun (cmd, args) -> ignore (call cmd args)) commands

let%test "check1" =
  (setup [ ("set", [ T ("", "h0", []); r "=>" (h "a") (h "a") ]) ];
   call "check" [])
  = "Ok"

let%test "check2" =
  (setup [ ("set", [ T ("", "h0", []); r "=>" (h "a") (h "b") ]) ];
   call "check" [])
  = "b is not ok"

let%test "show1" =
  (setup [ ("set", [ T ("", "h0", []); c (t "f" [ h "a"; h "b" ]) (h "c") ]) ];
   call "show" [])
  = "f(a, b) | c"

let%test "call_nb_args" = call "set" [] = "Not enough arguments"
let%test "call_unknown" = call "cheese" [ obj1 ] = "Unknown command cheese"
