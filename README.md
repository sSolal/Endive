# Endive

Endive is a new proof assistant inspired by the state of the art in terms of proof assistants (Coq, Lean, Isabel...). The difference lies in the theory underneath proving. Instead of relying on the Curry-Howard isomorphism, or involving complex concepts from homotopy type theory, Endive use a simple deduction system based on rewriting. While this system is much more flexible and hence prone to errors, it also gives a way more tangible insight as to what **is** a proof, and does not make the inner workings of the engine out of reach without a PhD in computer science.

This repository contains two separate package :

- Endive Core
- Endive Gui

The Core is a library implementing all the proof and terms editing, checking and other miscellaneous functionnalities.

The Gui is composed of a parser and graphical interface, not unlike existing proof assistants', to enable the actual use of Endive

## Usage

You can build everything and run the gui with the following commands

```
dune build
dune exec endive_gui
```

You can run the test suite by typing

```
dune test
```

Alternatively, you can check the coverage running
```
dune runtest --instrument-with bisect_ppx --force
bisect-ppx-report html
```
And visit the *index.html* in the generated *_coverage* directory.

You can build the documentation (built in \`\_build/default/\_doc\`) typing

```
dune build @doc
```

## License

Endive Core and Endive Gui are distributed under the [MIT License](https://choosealicense.com/licenses/mit)

## Contributing

Pull requests are welcome. For major changes, please open an issue first  
to discuss what you would like to change.

Before commiting anything, please check that your code passes all the tests (and update tests in case of new functionnalities) using

```
dune runtest
```

and format your code using

```
dune fmt
```
