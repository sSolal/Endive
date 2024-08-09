open! Base
open Endive_core.Engine
open Scripts

let obj1 = h "a"
let obj2 = a "b"

let%test_unit "check1" =
  [%test_eq: string] (check (r "=>" obj1 obj1)) "a => a is ok"

let%test_unit "check2" =
  [%test_eq: string] (check (r "=>" obj1 obj2)) "b is not ok"

let%test_unit "call1" =
  [%test_eq: string] (call "check" [ r "=>" obj2 obj2 ]) "b => b is ok"

let%test_unit "call2" =
  [%test_eq: string] (call "check" [ r "=>" obj2 obj1 ]) "a is not ok"

let%test_unit "call_nb_args" =
  [%test_eq: string]
    (call "check" [ obj1; obj1; obj1 ])
    "wrong number of arguments"

let%test_unit "call_unknown" =
  [%test_eq: string] (call "cheese" [ obj1 ]) "unknown command cheese"
