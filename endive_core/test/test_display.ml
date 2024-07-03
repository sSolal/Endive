open! Base
open Scripts
open Endive_core.Display

let obj1 = t "f" [ h "x"; h "y" ]

let obj2 =
  c
    (t "plus" [ a "x"; a "y" ])
    (r "=" (t "plus" [ h "a"; h "b" ]) (t "plus" [ h "b"; h "a" ]))

let%test_unit "display1" = [%test_eq: string] (display obj1) "f(x, y)"

let%test_unit "display2" =
  [%test_eq: string] (display obj2) "plus(x, y) | plus(a, b) = plus(b, a)"
