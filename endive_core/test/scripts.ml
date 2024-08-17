open Endive_core.Objects

open Endive_core.Display
(** Define some functions to build and manipulate terms more easily for testing *)

let counter = ref 0

let fresh () =
  counter := !counter + 1;
  string_of_int !counter

let h n = H (fresh (), n)
let t f children = T (fresh (), f, children)
let a f = T (fresh (), f, [])
let r v l r = R (fresh (), v, l, r)
let c l r = C (fresh (), l, r)

let test_display obj =
  print_endline (display obj);
  obj

let test_print str =
  print_endline str;
  str
