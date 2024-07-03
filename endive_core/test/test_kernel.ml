open Scripts
open Endive_core.Objects
open Endive_core.Kernel

let obj1 = h "a"
let obj2 = t "f" [ a "x"; a "y" ]
let obj3 = t "f" [ h "a"; a "y" ]
let obj4 = t "f" [ a "x"; h "b" ]
let rule1 = r "->" (h "a") (t "g" [ a "x"; h "a" ])
let add1 = t "plus" [ a "zero"; t "s" [ t "s" [ a "zero" ] ] ]

let def_add =
  r "="
    (t "plus" [ h "a"; t "s" [ h "b" ] ])
    (t "plus" [ t "s" [ h "a" ]; h "b" ])

let%test "equals1" = equals obj1 (H ("other_id", "a"))

let%test "equals2" =
  equals obj2
    (T ("other_id", "f", [ T ("other_id", "x", []); T ("other_id", "y", []) ]))

let equals_assoc_list =
  List.for_all2 (fun (a, b) (a', b') -> a = a' && equals b b')

let%test "unify1" = unify obj1 obj2 = [ ("a", obj2) ]

let%test "unify2" =
  equals_assoc_list (unify obj3 obj4) [ ("b", a "y"); ("a", a "x") ]

let%test "apply_map1" =
  equals
    (apply_map [ ("b", obj2) ] obj4)
    (t "f" [ a "x"; t "f" [ a "x"; a "y" ] ])

let%test "compose1" = equals (compose obj2 rule1) (t "g" [ a "x"; obj2 ])
let%test "compose2" = equals (compose obj3 rule1) (t "g" [ a "x"; obj3 ])

let%test "compose_add" =
  equals (compose def_add def_add)
    (r "="
       (t "plus" [ h "a"; t "s" [ t "s" [ h "b'" ] ] ])
       (t "plus" [ t "s" [ t "s" [ h "a" ] ]; h "b'" ]))

let%test "reduce_add" =
  equals
    (reduce (c add1 (c def_add def_add)))
    (t "plus" [ t "s" [ t "s" [ a "zero" ] ]; a "zero" ])
