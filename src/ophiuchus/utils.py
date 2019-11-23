from typing import Dict
from typing import Optional

import pkg_resources


def load_entry_points(
    group: str, type_constraint: Optional[type] = None,
) -> Dict[str, callable]:
    entry_points = {}

    for entry_point in pkg_resources.iter_entry_points(group):
        loaded = entry_point.load()
        if type_constraint and not issubclass(loaded, type_constraint):
            raise TypeError(
                f'Entry Point "{entry_point.name}" from "{group}" does not '
                f'match type constraint for "{type_constraint.__module__}.'
                f'{type_constraint.__name__}".',
            )
        entry_points[entry_point.name] = loaded

    return entry_points
