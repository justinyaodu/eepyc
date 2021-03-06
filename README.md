# eepyc

*E*valuate *e*mbedded *Py*thon *c*ode in textual data, replacing code snippets with their output. Useful for templating and producing automatically generated content.

```console
$ echo 'An RGB triplet can have {{ 2 ** 24 }} possible values.' | eepyc
An RGB triplet can have 16777216 possible values.
$
```

## Features

* **Straightforward syntax** inspired by Liquid, Django, and others
* **Full access to Python's capabilities:** import modules, define functions and classes, etc.
* **Multi-line tags** improve readability and flexibility
* **Simple import system** for handling multiple files
* **Reuse existing Python code** with minimal modifications
* **Line trimming and smart indentation** for pretty source files and pretty output

## Installation

Install from [PyPI](https://pypi.org/project/eepyc):

```console
$ pip install eepyc
```

Alternatively, [download](https://github.com/justinyaodu/eepyc/tree/master/eepyc.py) the script and run it directly:

```console
$ python eepyc.py
```

## Examples

### Executing Statements

[example/mult-table.eepyc](https://github.com/justinyaodu/eepyc/tree/master/example/mult-table.eepyc)

```
Here is a multiplication table:

{{%
    # This is the inside of a statement tag, specified with '%'.

    # Define a variable.
    size = 9

    # Use list comprehensions to create a multiplication table.
    table = [[(i + 1) * (j + 1) for i in range(size)] for j in range(size)]

    # Print the multiplication table. When evaluated, this statement tag
    # will be replaced by the output of the print() calls in the tag.
    for row in table:
        print(''.join([f"{v:3}" for v in row]))
}}
```

Result:

```console
$ eepyc example/mult-table.eepyc
Here is a multiplication table:

  1  2  3  4  5  6  7  8  9
  2  4  6  8 10 12 14 16 18
  3  6  9 12 15 18 21 24 27
  4  8 12 16 20 24 28 32 36
  5 10 15 20 25 30 35 40 45
  6 12 18 24 30 36 42 48 54
  7 14 21 28 35 42 49 56 63
  8 16 24 32 40 48 56 64 72
  9 18 27 36 45 54 63 72 81
$
```

### Importing and Exporting Namespaces

[example/color.py](https://github.com/justinyaodu/eepyc/tree/master/example/color.py)

```python
# Tags and tag delimiters can be placed in Python comments
# so that the file can be used normally as a Python module.

# Export the namespace created for this file (under the name 'color').
# {{e color }}

# Begin a statement tag to capture these function definitions.
# {{%

def format_hex(color):
    """Format an RGB color tuple as a hex triplet, e.g. #0a279c."""
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"

def average(a, b):
    """Return the average of two RGB colors."""
    return (
        (a[0] + b[0]) // 2,
        (a[1] + b[1]) // 2,
        (a[2] + b[2]) // 2)

# End of statement tag.
# }}
```
[example/color-test.eepyc](https://github.com/justinyaodu/eepyc/tree/master/example/color-test.eepyc) (file extension is not important)

```
{{# This is a comment tag. The hyphens at the end of this tag delete the
newline characters that come after this tag (two hyphens for two
newlines) to keep the output formatted nicely. --}}

{{# The tag below imports the namespace exported by color.py, and gives
it the alias 'c' to keep things concise. --}}

{{i color as c --}}

{{%
    # Code in statement blocks can be indented for visual clarity.
    # The extra indentation is removed with textwrap.dedent() before evaluation.

    # Define some RGB color tuples.
    red   = (255, 0, 0)
    green = (0, 255, 0)
--}}

{{# Call the imported functions. -}}
I'm mixing {{ c.format_hex(red) }} and {{ c.format_hex(green) }}.
I got {{ c.format_hex(c.average(red, green)) }}.
```

Result:

```console
$ eepyc example/color.py example/color-test.eepyc
I'm mixing #ff0000 and #00ff00.
I got #7f7f00.
$
```

### List Expressions and Automatic Indenting

[example/planets.eepyc](https://github.com/justinyaodu/eepyc/tree/master/example/planets.eepyc)

```
{{%
    planets = ["Mercury", "Venus", "Earth", "Mars",
            "Jupiter", "Saturn", "Uranus", "Neptune"]
    descriptions = ["hot", "even hotter", "just right", "cold",
            "huge", "ringed", "turquoise", "far away"]
--}}

<h1>Planets of the Solar System</h1>
<ol>
  {{# Create a list item for each planet and its description. -}}
  {{ [f"<li>{p} is {d}.</li>" for p, d in zip(planets, descriptions)] }}
</ol>
```

Result:

```console
$ eepyc example/planets.eepyc
<h1>Planets of the Solar System</h1>
<ol>
  <li>Mercury is hot.</li>
  <li>Venus is even hotter.</li>
  <li>Earth is just right.</li>
  <li>Mars is cold.</li>
  <li>Jupiter is huge.</li>
  <li>Saturn is ringed.</li>
  <li>Uranus is turquoise.</li>
  <li>Neptune is far away.</li>
</ol>
$
```

### Meta-Example

This readme file was generated with `eepyc`, by making it evaluate its own source code before running itself on the files in the [example](https://github.com/justinyaodu/eepyc/tree/master/example) folder. ([Dogfooding](https://en.wikipedia.org/wiki/Eating_your_own_dog_food) is important.) The readme source is located [here](https://github.com/justinyaodu/eepyc/tree/master/example/README.md.eepyc).

## Command-Line Usage

From `eepyc --help`:

```
Usage:
    eepyc [file...]
    eepyc <option>

Options:
    -h, --help  Display this help message
    --version   Display version and copyright information

Each command-line parameter specifies a file which will have its
contents evaluated. If no files are specified, input is taken from
stdin. The evaluated content of the last file (only!) is written to
stdout. Users who desire more sophisticated behaviour may wish to use
eepyc's Python interface instead.
```

## Security Note

`eepyc` should not be used with untrusted input, since the Python code embedded in the input has full access to the capabilities of the Python interpreter.

## Syntax Reference

### BNF Grammar

```
<tagopen>  ::= "{{"
<tagclose> ::= "}}"

<linetrim>   ::= "" | "-" <linetrim>
<bolflag>    ::= "" | "^"
<whitespace> ::= " " | "\t" | "\n"

<tagstart> ::= <linetrim> <bolflag> <whitespace>
<tagend>   ::= <whitespace> <linetrim>

<import>  ::= <identifier> | <identifier> " as " <identifier>
<imports> ::= <import> | <import> ", " <imports>

<expressiontag> ::= <tagopen>     <tagstart> <expression> <tagend> <tagclose>
<statementtag>  ::= <tagopen> "%" <tagstart> <statements> <tagend> <tagclose>
<importtag>     ::= <tagopen> "i" <tagstart> <imports>    <tagend> <tagclose>
<exporttag>     ::= <tagopen> "e" <tagstart> <identifier> <tagend> <tagclose>
<comment>       ::= <tagopen> "#" <tagstart> <comment>    <tagend> <tagclose>
```

### Newline Trimming

The hyphens before/after a tag enable the trimming of consecutive newline characters before/after the tag. The number of hyphens specifies the number of newline characters to be removed. For example, the tag `{{# comment --}}` will remove up to two newline characters after it. This is useful for keeping the source file formatted neatly while also avoiding extraneous whitespace in the output file.

### Automatic Indenting

If a tag is indented (only whitespace between the start of the line and `{{`), each line of text output by the tag will be indented correspondingly. (Blank lines will not be indented, however.) To disable automatic indenting, place a `^` after any `-` at the start of the tag: `\n  {{-^ "don't indent me" }}` will evaluate to `"don't indent me"`.

### Escaping Literal Double Braces

Tags must not contain the substring `}}` directly; workarounds include string concatenation and substring replacement. The text outside of tags must not contain `{{` or `}}`; a simple workaround is to use an expression tag like `{{ '{' * 2 }}`.
