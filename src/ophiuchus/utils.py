import logging
from typing import Dict
from typing import Optional

import pkg_resources


log = logging.getLogger(__name__)


def load_entry_points(
    group: str,
    type_constraint: Optional[type] = None,
    working_set: pkg_resources.WorkingSet = pkg_resources.working_set,
) -> Dict[str, callable]:
    entry_points = {}

    log.info(f'Loading entry points for "{group}"')

    for entry_point in working_set.iter_entry_points(group):
        log.debug(f'Loading entry point "{entry_point.name}" from "{group}"')

        try:
            loaded = entry_point.load()
        except Exception as e:
            msg = (
                f'Failed to load Entry point "{entry_point.name}" from '
                f'"{group}": {e}'
            )
            log.error(msg)
            raise e

        if type_constraint and not issubclass(loaded, type_constraint):
            msg = (
                f'Entry Point "{entry_point.name}" from "{group}" does not '
                f'match type constraint for "{type_constraint.__module__}.'
                f'{type_constraint.__name__}".',
            )
            log.error(msg)
            raise TypeError(msg)

        log.debug(f'Successfully loaded "{entry_point.name}" from "{group}"')
        entry_points[entry_point.name] = loaded

    log.debug(f'Finished loading {len(entry_points)} from "{group}"')
    return entry_points
