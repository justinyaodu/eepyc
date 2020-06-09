"""Evaluate Python expressions and statements embedded in plaintext."""

# Enable eepyc to evaluate its own source file (used for generating
# the readme file).
# {{e eepyc }}
# {{%

__all__ = ['Evaluator']
__version__ = "0.3.0"
__author__ = "Justin Yao Du"

import io
import itertools
import re
import sys
import textwrap


class _DictWrapper():
    """Allow dict items to be accessed as attributes."""
    def __init__(self, wrapped_dict):
        self.__dict__ = wrapped_dict


class Evaluator:
    """Evaluates tags in text and manages exported namespaces."""

    tag_outer_regex = ''.join([
        r'(?P<newlines_before>\n*)?', # Newlines before.
        r'(?P<tag_indent>^[ \t]*)?',  # Whitespace used to indent this tag.
        r'\{\{',                      # Opening tag delimiter.
        r'(?P<tag_inner>.*?)',        # Text enclosed in tag delimiters.
        r'\}\}',                      # Closing tag delimiter.
        r'(?P<newlines_after>\n*)',   # Newlines after.
    ])

    tag_inner_regex = ''.join([
        r'(?P<tag_type>[#%ie]?)', # Tag type specifier.
        r'(?P<trim_before>-*)',   # Hyphens to trim newlines before.
        r'(?P<no_indent>[\^]?)',  # Caret to disable indenting of tag output.
        r'\s',                    # Mandatory whitespace character.
        r'(?P<tag_contents>.*?)', # The text within the tag.
        r'\s',                    # Mandatory whitespace character.
        r'(?P<trim_after>-*)',    # Hyphens to trim newlines after.
    ])

    import_regex = ''.join([
        r'\s*',                       # Whitespace before.
        r'(?P<name>\S+)',             # Name of namespace to import.
        r'(\s+as\s+(?P<alias>\S+))?', # Optional alias (import as).
        r'\s*',                       # Whitespace after.
    ])

    export_regex = ''.join([
        r'\s*',           # Whitespace before.
        r'(?P<name>\S+)', # Name to export namespace under.
        r'\s*',           # Whitespace after.
    ])

    def __init__(self):
        # Map exported namespace names to namespaces, so they can be
        # imported later.
        self.namespaces = dict()

    def _eval_tag_contents(self, tag_type, tag_contents, namespace):
        """Evaluate a tag's contents in the given namespace."""

        if tag_type == '':
            # Evaluate expression.
            result = eval(textwrap.dedent(tag_contents), namespace)

            # Special handling for lists: print each element on a new line.
            if isinstance(result, list):
                return '\n'.join(str(v) for v in result)
            else:
                return str(result)

        elif tag_type == '%':
            # Execute statements.

            # Redirect print() calls from tag code.
            actual_stdout = sys.stdout
            fake_stdout = io.StringIO()
            sys.stdout = fake_stdout

            # Dedent code before executing, to properly handle indented code.
            exec(textwrap.dedent(tag_contents), namespace)

            # Restore the actual stdout.
            sys.stdout = actual_stdout

            # Return the text printed by the tag, with the final
            # newline trimmed. This behavior reduces the need for
            # specifying end='' in print() calls.
            return re.sub('\n$', '', fake_stdout.getvalue())

        elif tag_type == 'e':
            # Export namespace.

            match = re.fullmatch(__class__.export_regex, tag_contents)
            if match is None:
                raise ValueError("Invalid syntax for export tag.")

            name = match['name']

            self.namespaces[name] = namespace
            return ''

        elif tag_type == 'i':
            # Import namespaces.

            for import_expr in tag_contents.split(','):
                # Ignore empty and whitespace-only strings.
                if re.fullmatch(r'\s*', import_expr):
                    continue

                match = re.fullmatch(__class__.import_regex, import_expr)
                if match is None:
                    raise ValueError("Invalid syntax for import tag.")

                name = match['name']
                alias = match['alias'] or name

                try:
                    # Import requested namespace into current namespace.
                    namespace[alias] = _DictWrapper(self.namespaces[name])
                except KeyError as e:
                    msg = f"The namespace '{name}' is not defined."
                    raise NameError(msg) from e

            return ''
        
        elif tag_type == '#':
            # Comment.
            return ''

        else:
            # Shouldn't ever be raised, assuming the character class for tag
            # type specifiers in the regex matches the characters handled
            # above.
            raise ValueError(f"Unknown tag type '{tag_type}'.")

    def _eval_tag(self, outer_match, namespace):
        """Given a match of tag_outer_regex, return the evaluated text
        as a tuple (whitespace_before, evaluated_tag_output,
        whitespace_after). Raises ValueError if the tag does not match
        tag_inner_regex.
        """

        outer_groups = outer_match.groupdict(default='')

        # Match groups within the tag delimiters.
        inner_match = re.fullmatch(__class__.tag_inner_regex,
                outer_groups['tag_inner'], flags=re.DOTALL)
        if not inner_match:
            raise ValueError("Invalid syntax within tag.")
        inner_groups = inner_match.groupdict(default='')

        # Get tag output.
        try:
            evaluated = self._eval_tag_contents(inner_groups['tag_type'],
                    inner_groups['tag_contents'], namespace)
        except:
            raise

        # Indent each line of output, unless indenting is turned off.
        if not inner_groups['no_indent']:
            # Only indent non-empty lines.
            evaluated = '\n'.join((outer_groups['tag_indent'] + s if s else "")
                    for s in evaluated.split('\n'))

        # Trim newlines before and after the tag.
        newlines_before = outer_groups['newlines_before']
        newlines_after  = outer_groups['newlines_after' ]
        newlines_before = newlines_before[len(inner_groups['trim_before']):]
        newlines_after  = newlines_after [len(inner_groups['trim_after' ]):]

        return newlines_before, evaluated, newlines_after

    def evaluate(self, text):
        """Evaluate all tags in the given string and return the
        resulting string. Each call to this function creates a new
        namespace.
        """

        # Create a new namespace.
        namespace = {}

        remaining = text
        chunks = []
        while True:
            # Find the next tag.
            match = re.search(__class__.tag_outer_regex, remaining,
                    re.DOTALL | re.MULTILINE)
            if not match:
                # No more tags.
                chunks.append(remaining)
                break

            # Text before matched tag.
            chunks.append(remaining[:match.start()])

            ws_before, evaluated, ws_after = self._eval_tag(match, namespace)
            chunks.append(ws_before)
            chunks.append(evaluated)

            # Include whitespace after tag in the remaining string, so that it
            # is available to be manipulated by the next tag.
            remaining = ws_after + remaining[match.end():]

        return ''.join(chunks)


help__ = f"""Usage:
    eepyc [file...]
    eepyc <option>

Options:
    -h, --help  Display this help message
    --version   Display version and copyright information

Each command-line parameter specifies a file which will have its
contents evaluated. If no files are specified, input is taken from
stdin. The evaluated content of the last file (only!) is written to
stdout. Users who desire more sophisticated behaviour may wish to use
eepyc's Python interface instead."""


version__ = f"""eepyc {__version__}
Copyright (C) 2020 {__author__}
Licensed under the MIT License."""


# Close the eepyc statement tag opened at the beginning of the file.
# }}


def _main():
    # Check for help or version options.
    if len(sys.argv) == 2:
        if sys.argv[1] in ['-h', '--help']:
            print(help__)
            sys.exit(0)
        elif sys.argv[1] == '--version':
            print(version__)
            sys.exit(0)

    # Take input from the files named as command-line arguments, or
    # stdin if no files are specified.
    files = [open(f) for f in sys.argv[1:]] or [sys.stdin]

    evaluator = Evaluator()

    # Evaluate the files in the order given, only producing output for
    # the last file. This assumes that the preceding files are for
    # imports only, which should cover most use cases.
    for f in files[:-1]:
        evaluator.evaluate(f.read())
    print(evaluator.evaluate(files[-1].read()), end='')


if __name__ == '__main__':
    _main()
