open Endive_core.Objects
open Endive_core.Kernel

let obj1 = H ("1", "a")
let obj2 = T ("2", "f", [ T ("3", "x", []); T ("4", "y", []) ])
let obj3 = T ("1", "f", [ H ("2", "a"); T ("3", "y", []) ])
let obj4 = T ("1", "f", [ T ("2", "x", []); H ("3", "b") ])
let%test "unify1" = unify obj1 obj2 = [ ("a", obj2) ]

let%test "unify2" =
  unify obj3 obj4 = [ ("b", T ("3", "y", [])); ("a", T ("2", "x", [])) ]

let%test "apply_map1" =
  apply_map [ ("b", obj2) ] obj4
  = T
      ( "1",
        "f",
        [
          T ("2", "x", []); T ("2", "f", [ T ("3", "x", []); T ("4", "y", []) ]);
        ] )
