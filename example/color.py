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
