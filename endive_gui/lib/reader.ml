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

let read_line (command, args) =
  try Engine.call command args with e -> Printexc.to_string e

let read text =
  try
    let lexbuf = Lexing.from_string text in
    let lines = main token lexbuf in
    ignore (Engine.reset ());
    String.concat "\n" (List.map read_line lines)
  with e -> "Syntax error : " ^ Printexc.to_string e
