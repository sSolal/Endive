open Display

let check prop =
  let result = Kernel.check [] "=>" prop in
  if Option.is_none result then display prop ^ " is ok"
  else
    Option.value (Option.map display result) ~default:"this should never appear"
    ^ " is not ok"

(** Main entrypoint to the engine *)
let call command args =
  try
    match command with
    | "check" ->
        if List.length args <> 1 then failwith "wrong number of arguments"
        else
          let prop = List.hd args in
          check prop
    | c -> "unknown command " ^ c
  with Failure e -> e
