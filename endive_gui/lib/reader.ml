open Lexer
open Parser
open Endive_core

let rec check_parsed = function
  | [] -> ""
  | obj :: tail ->
      (if Option.is_none (Kernel.check [] "=>" obj) then
         Display.display (Kernel.reduce obj) ^ " OK"
       else Display.display obj ^ " not OK")
      ^ "\n" ^ check_parsed tail

let read text =
  try
    let lexbuf = Lexing.from_string text in
    let parsed = main token lexbuf in
    check_parsed parsed
  with e -> Printexc.to_string e
