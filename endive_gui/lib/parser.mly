%{
open Endive_core.Objects

let fresh = ref 0
let fresh_name () = 
  fresh := !fresh + 1;
  (string_of_int !fresh)
%}

%token <string> SYM
%token LP RP EOF COMMA DOT
%token <string> HOLE
%token <string> RULE
%token COMP

%start <obj list> main
%%

main : 
| obj DOT main { $1 :: $3 }
| EOF {[]}

obj:
| comp { $1 }

obj_list:
| obj COMMA obj_list { $1 :: $3 }
|                    { [] }

comp:
| comp COMP rule { C(fresh_name(), $1, $3) }
| rule { $1 }

rule : 
| term RULE rule { R(fresh_name(), $2, $1, $3) }
| term { $1 }

term : 
| SYM LP obj_list RP { T(fresh_name (), $1, $3) }
| atom { $1 }

atom :
| LP obj RP { $2 }
| HOLE { H("", $1) }
| SYM { T("", $1, []) }







