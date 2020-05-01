"""Evaluate Python expressions and statements embedded in plaintext."""

# Enable eepyc to evaluate its own source file (used for generating
# the readme file).
# {{e eepyc }}
# {{%

__all__ = ['Evaluator']
__version__ = "0.1.2"
__author__ = "Justin Yao Du"

import io
import re
import sys


class _DictWrapper():
    """Allow dict items to be accessed as attributes."""
    def __init__(self, wrapped_dict):
        self.__dict__ = wrapped_dict


class Evaluator:
    """Evaluates tags in text and manages exported namespaces."""
    
    tag_regex = ''.join([
        r'(?P<newlines_before>\n*)', # Newlines before.
        re.escape('{{'),             # Opening delimiter.
        r'(?P<tag_type>[#%ie]?)',    # Tag type specifier.
        r'(?P<trim_before>-*)',      # Hyphens to trim newlines before.
        r'\s+',                      # Mandatory whitespace.
        r'(?P<tag_text>.*?)',        # Tag contents.
        r'\s+',                      # Mandatory whitespace.
        r'(?P<trim_after>-*?)',      # Hyphens to trim newlines after.
        re.escape('}}'),             # Closing delimiter.
        r'(?P<newlines_after>\n*)'   # Newlines after.
    ])

    import_regex = ''.join([
        r'^(?P<name>\S+)',            # Name of namespace to import.
        r'(\s+as\s+(?P<alias>\S+))?$' # Optional alias (import as).
    ])

    export_regex = r'^(?P<name>\S+)$' # Name to export namespace under.

    def __init__(self):
        # Map exported namespace names to namespaces, so they can be
        # imported later.
        self.namespaces = dict()

    def _eval_tag(self, tag_type, tag_text, namespace):
        """Evaluate a tag's contents in the given namespace."""

        if tag_type == '':
            # Evaluate expression.
            return str(eval(tag_text, namespace))

        elif tag_type == '%':
            # Execute statements.

            # Redirect print() calls from tag code.
            actual_stdout = sys.stdout
            fake_stdout = io.StringIO()
            sys.stdout = fake_stdout

            exec(tag_text, namespace)

            # Restore the actual stdout.
            sys.stdout = actual_stdout

            # Return the text printed by the tag, with the final
            # newline trimmed. This behavior reduces the need for
            # specifying end='' in print() calls.
            return re.sub('\n$', '', fake_stdout.getvalue())

        elif tag_type == 'e':
            # Export namespace.

            match = re.match(__class__.export_regex, tag_text)
            if match is None:
                raise ValueError("Invalid syntax for export tag.")

            name = match.group('name')

            self.namespaces[name] = namespace
            return ''

        elif tag_type == 'i':
            # Import namespace.
            
            match = re.match(__class__.import_regex, tag_text)
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

    def _sub_tag(self, match, namespace):
        """Wrapper for ``_eval_tag`` which handles newline trimming."""

        groups = match.groupdict(default='')

        # Get tag output.
        tag_type = groups['tag_type']
        tag_text = groups['tag_text']

        try:
            evaluated = self._eval_tag(tag_type, tag_text, namespace)
        except Exception as e:
            msg = f"Error occurred while evaluating tag:\n{match.group(0)}"
            raise ValueError(msg) from e

        # Trim up to the number of newlines specified by the hyphens.
        trim_before = len(groups['trim_before'])
        newlines_before = len(groups['newlines_before'])
        newlines_before = '\n' * max(0, newlines_before - trim_before)

        trim_after = len(groups['trim_after'])
        newlines_after = len(groups['newlines_after'])
        newlines_after = '\n' * max(0, newlines_after - trim_after)

        return newlines_before + evaluated + newlines_after

    def eval_tags(self, text):
        """Evaluate all tags in the given string and return the
        resulting string. Each call to this function creates a new
        namespace.
        """

        # Global namespace used for eval() and exec() calls.
        namespace = dict()

        def replace_func(match):
            return self._sub_tag(match, namespace)

        # Match newlines in tag contents to allow multi-line tags.
        flags = re.DOTALL

        return re.sub(__class__.tag_regex, replace_func, text, flags=flags)


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
