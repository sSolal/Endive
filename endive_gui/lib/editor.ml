open Files
open GdkKeysyms

(** A class regrouping the text area widget, along with file related methods*)
class editor ?packing ?show () =
  object (self)
    val text = GText.view ?packing ?show ()
    val mutable filename = None
    method text = text
    method get_text = text#buffer#get_text ()

    method load_file name =
      try
        let b = Buffer.create 1024 in
        with_file name ~f:(input_channel b);
        let s = Glib.Convert.locale_to_utf8 (Buffer.contents b) in
        let n_buff = GText.buffer ~text:s () in
        text#set_buffer n_buff;
        filename <- Some name;
        n_buff#place_cursor ~where:n_buff#start_iter
      with _ -> prerr_endline "Load failed"

    method open_file () = file_dialog ~action:`OPEN ~callback:self#load_file ()

    method save_dialog () =
      file_dialog ~action:`SAVE ?filename
        ~callback:(fun file -> self#output ~file)
        ()

    method save_file () =
      match filename with
      | Some file -> self#output ~file
      | None -> self#save_dialog ()

    method output ~file =
      try
        if Sys.file_exists file then Sys.rename file (file ^ "~");
        let s = text#buffer#get_text () in
        let oc = open_out file in
        output_string oc (Glib.Convert.locale_from_utf8 s);
        close_out oc;
        filename <- Some file
      with _ -> prerr_endline "Save failed"
  end

(** Sets up the top menu related to text handling*)
let add_editor_menu window editor menubar =
  let factory = new GMenu.factory ~accel_path:"<EDITOR2>/" menubar in
  let accel_group = factory#accel_group in

  let file_menu = factory#add_submenu "File" in
  let edit_menu = factory#add_submenu "Edit" in

  let factory =
    new GMenu.factory ~accel_path:"<EDITOR2 File>/////" file_menu ~accel_group
  in
  ignore (factory#add_item "Open" ~key:_O ~callback:editor#open_file);
  ignore (factory#add_item "Save" ~key:_S ~callback:editor#save_file);
  ignore (factory#add_item "Save as..." ~callback:editor#save_dialog);
  ignore (factory#add_separator ());
  ignore (factory#add_item "Quit" ~key:_Q ~callback:window#destroy);
  let factory =
    new GMenu.factory ~accel_path:"<EDITOR2 File>///" edit_menu ~accel_group
  in
  ignore
    (factory#add_item "Copy" ~key:_C ~callback:(fun () ->
         editor#text#buffer#copy_clipboard GMain.clipboard));
  ignore
    (factory#add_item "Cut" ~key:_X ~callback:(fun () ->
         GtkSignal.emit_unit editor#text#as_view
           ~sgn:GtkText.View.S.cut_clipboard));
  ignore
    (factory#add_item "Paste" ~key:_V ~callback:(fun () ->
         GtkSignal.emit_unit editor#text#as_view
           ~sgn:GtkText.View.S.paste_clipboard));
  ignore (factory#add_separator ());
  ignore
    (factory#add_check_item "Word wrap" ~active:false ~callback:(fun b ->
         editor#text#set_wrap_mode (if b then `WORD else `NONE)));
  ignore (window#add_accel_group accel_group)
