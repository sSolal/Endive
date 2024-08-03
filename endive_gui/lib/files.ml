(**/**)

type action = [ `OPEN | `SAVE | `DELETE_EVENT | `CANCEL ]

let file_dialog ~(action : [ `OPEN | `SAVE ]) ~callback ?filename () =
  let dialog =
    GWindow.file_chooser_dialog
      ~action:(action :> GtkEnums.file_chooser_action)
      ~modal:true ?filename ()
  in
  dialog#add_button_stock `CANCEL `CANCEL;
  dialog#add_select_button_stock (action :> GtkStock.id) (action :> action);
  (match dialog#run () with
  | `OPEN | `SAVE -> (
      match dialog#filename with None -> () | Some s -> callback s)
  | `DELETE_EVENT | `CANCEL -> ());
  dialog#destroy ()

let input_channel b ic =
  let buf = Bytes.create 1024 and len = ref 0 in
  while
    len := input ic buf 0 1024;
    !len > 0
  do
    Buffer.add_subbytes b buf 0 !len
  done

let with_file name ~f =
  let ic = open_in name in
  try
    f ic;
    close_in ic
  with exn ->
    close_in ic;
    raise exn

(**/**)
