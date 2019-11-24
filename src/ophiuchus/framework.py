import logging
from typing import Dict


log = logging.getLogger(__name__)

routes = {}


class GlobalConfig:
    def __init__(self):
        self.endpoint_map = {}

    def add_endpoint(self, site_group: str, endpoint: str):
        if site_group in self.endpoint_map:
            raise ValueError(f"{site_group} already has an endpoint")
        self.endpoint_map[site_group] = endpoint

    def get_endpoint(self, site_group: str):
        return self.endpoint_map.get(site_group, None)


class HandlerMeta(type):
    def __init__(self, *args):
        super().__init__(*args)
        self.routes = []


class Handler(object, metaclass=HandlerMeta):
    def __init__(self, config):
        self.config = config


def route(*handler_routes: str) -> Handler:
    def dec(handler: Handler):
        name = f"{handler.__module__}.{handler.__name__}"
        if name not in routes:
            routes[name] = []

        for route in handler_routes:
            if route in routes[name]:
                log.warning(f"'{route}' already in route table for '{name}'!")
                continue
            routes[name].append(route)

        return handler

    return dec
