"""Evaluate Python expressions and statements embedded in plaintext."""

# Enable eepyc to evaluate its own source file (used for generating
# the readme file).
# {{e eepyc }}
# {{%

__all__ = ['Evaluator']
__version__ = "0.2.0"
__author__ = "Justin Yao Du"

import io
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
        r'((?P<newlines_before>\n+)', # Newlines before.
        r'(?P<tag_indent>\s*))?',     # Whitespace used to indent this tag.
        r'\{\{',                      # Opening tag delimiter.
        r'(?P<tag_inner>.*?)',        # Text enclosed in tag delimiters.
        r'\}\}',                      # Closing tag delimiter.
        r'(?P<newlines_after>\n*)',   # Newlines after.
    ])

    tag_inner_regex = ''.join([
        r'(?P<tag_type>[#%ie]?)', # Tag type specifier.
        r'(?P<no_indent>[\^]?)',  # Caret to disable indenting of tag output.
        r'(?P<trim_before>-*)',   # Hyphens to trim newlines before.
        r'\s',                    # Mandatory whitespace character.
        r'(?P<tag_text>.*?)',     # Tag contents.
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

    def _eval_tag_text(self, tag_type, tag_text, namespace):
        """Evaluate a tag's contents in the given namespace."""

        if tag_type == '':
            # Evaluate expression.
            result = eval(tag_text, namespace)

            # Special handling for lists: print each element on a new line.
            if isinstance(result, str):
                return result
            elif isinstance(result, list):
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
            exec(textwrap.dedent(tag_text), namespace)

            # Restore the actual stdout.
            sys.stdout = actual_stdout

            # Return the text printed by the tag, with the final
            # newline trimmed. This behavior reduces the need for
            # specifying end='' in print() calls.
            return re.sub('\n$', '', fake_stdout.getvalue())

        elif tag_type == 'e':
            # Export namespace.

            match = re.fullmatch(__class__.export_regex, tag_text)
            if match is None:
                raise ValueError("Invalid syntax for export tag.")

            name = match.group('name')

            self.namespaces[name] = namespace
            return ''

        elif tag_type == 'i':
            # Import namespaces.

            for import_expr in tag_text.split(','):
                # Ignore empty and whitespace-only strings.
                if re.fullmatch(r'\s*', import_expr):
                    continue

                match = re.fullmatch(__class__.import_regex, import_expr)
                if match is None:
                    raise ValueError("Invalid syntax for import tag.")

                name = match.group('name')
                alias = match.group('alias') or name

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

    @staticmethod
    def _trim_newlines(newlines, trim):
        """Given a string of newlines, and another string whose length
        indicates the number of newlines to trim, return a string with
        the resulting number of newlines.
        """
        return newlines[len(trim):]

    def _eval_tag_outer(self, match_outer, namespace):
        """Wrapper for ``_eval_tag_text`` which handles newline
        trimming and indenting.
        """

        groups_outer = match_outer.groupdict(default='')

        # Match groups within the tag delimiters.
        match_inner = re.fullmatch(__class__.tag_inner_regex,
                groups_outer['tag_inner'], flags=re.DOTALL)
        if not match_inner:
            msg = "Invalid tag syntax in tag:\n"
            msg += match_outer.group(0)
            raise ValueError(msg)
        groups_inner = match_inner.groupdict(default='')

        # Get tag output.
        tag_type = groups_inner['tag_type']
        tag_text = groups_inner['tag_text']
        try:
            evaluated = self._eval_tag_text(tag_type, tag_text, namespace)
        except Exception as e:
            msg = "Error occurred while evaluating tag:\n"
            msg += match_outer.group(0)
            raise ValueError(msg) from e

        # Indent each line of output, unless indenting is turned off.
        tag_indent = groups_outer['tag_indent']
        if not groups_inner['no_indent']:
            # Only indent non-empty lines.
            evaluated = '\n'.join((tag_indent + s if s else "")
                    for s in evaluated.split('\n'))

        # Trim up to the number of newlines specified by the hyphens.
        newlines_before = __class__._trim_newlines(
                groups_outer['newlines_before'],
                groups_inner['trim_before'])
        newlines_after = __class__._trim_newlines(
                groups_outer['newlines_after'],
                groups_inner['trim_after'])

        return newlines_before + evaluated + newlines_after

    def eval_tags(self, text):
        """Evaluate all tags in the given string and return the
        resulting string. Each call to this function creates a new
        namespace.
        """

        # Global namespace used for eval() and exec() calls.
        namespace = dict()

        def repl_func(match):
            return self._eval_tag_outer(match, namespace)

        # Match newlines in tag contents to allow multi-line tags.
        flags = re.DOTALL

        return re.sub(__class__.tag_outer_regex, repl_func, text, flags=flags)


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
        evaluator.eval_tags(f.read())
    print(evaluator.eval_tags(files[-1].read()), end='')


if __name__ == '__main__':
    _main()
