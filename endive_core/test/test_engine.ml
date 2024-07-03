open! Base

let%test "boolean" = 2 + 2 = 4
let%test_unit "equality" = [%test_eq: int] (2 + 2) 4
