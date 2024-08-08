{
  open Parser
}

rule token = parse
(* Syntax *)
| [' ' '\t' '\n']  { token lexbuf }
| ['a'-'z' 'A'-'Z']['a'-'z' 'A'-'Z' '0'-'9' '_']* as s { SYM s}
| '('              { LP }
| ')'              { RP }
| ','              { COMMA }
| '.'              { DOT }
| eof              { EOF }

(* Holes *)
| '#' ['a'-'z' 'A'-'Z']['a'-'z' 'A'-'Z' '0'-'9' '_']* as s    { HOLE (String.sub s 1 (String.length s - 1)) }

(* Rules *)
| "=>" { RULE "=>" }
| "->" { RULE "->"}
| "=" { RULE "=" }

(* Composition *)
| '|'              { COMP }


| _ as c { failwith (Printf.sprintf "unexpected character: %C" c) }