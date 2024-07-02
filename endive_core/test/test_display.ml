open! Base
open Endive_core.Objects
open Endive_core.Display

let obj1 = T ("1", "f", [ H ("2", "x"); H ("3", "y") ])

let obj2 =
  C
    ( "1",
      T ("2", "plus", [ T ("3", "x", []); T ("4", "y", []) ]),
      R
        ( "5",
          "=",
          T ("6", "plus", [ H ("7", "a"); H ("8", "b") ]),
          T ("9", "plus", [ H ("10", "b"); H ("11", "a") ]) ) )

let%test_unit "display1" = [%test_eq: string] (display obj1) "f(x, y)"

let%test_unit "display2" =
  [%test_eq: string] (display obj2) "plus(x, y) | plus(a, b) = plus(b, a)"
