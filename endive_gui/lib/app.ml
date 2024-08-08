open Editor

(** Launches the interface *)
let run () =
  ignore (GMain.init ());

  let window = GWindow.window ~title:"Endive" () in
  let vbox = GPack.vbox ~packing:window#add () in
  ignore (window#connect#destroy ~callback:GMain.quit);

  let menubar = GMenu.menu_bar ~packing:vbox#pack () in
  let scrollable = GBin.scrolled_window ~packing:vbox#add () in
  let editor = new editor ~packing:scrollable#add () in

  add_editor_menu window editor menubar;

  let results = GPack.hbox ~packing:vbox#add () in
  let label = GMisc.label ~text:"..." ~packing:results#pack () in

  ignore
    (editor#text#buffer#connect#after#insert_text ~callback:(fun _ s ->
         if s = "." then label#set_text (Reader.read editor#get_text) else ()));

  window#set_default_size ~width:640 ~height:480;
  window#show ();
  GMain.main ()
