import copy
import json
import logging
from typing import Dict


log = logging.getLogger(__name__)

routes = {}


class GlobalConfig:
    def __init__(self, endpoints: Dict[str, str] = {}, **kwargs):
        self.log = logging.getLogger(
            f"{self.__module__}.{self.__class__.__name__}",
        )

        self.log.debug(f"Adding additional endpoints: {endpoints}")
        self.endpoints = copy.deepcopy(endpoints)

        self.config = {}
        for kwarg, value in kwargs.items():
            self.log.debug(f"Adding arbitrary config: {kwarg}")
            self.config[kwarg] = value

    def add_endpoint(self, site_group: str, endpoint: str) -> None:
        if site_group in self.endpoint_map:
            raise ValueError(f"{site_group} already has an endpoint")
        self.endpoint_map[site_group] = endpoint

    def get_endpoint(self, site_group: str) -> str:
        return self.endpoint_map.get(site_group, None)

    def get_endpoints(self) -> Dict[str, str]:
        return copy.deepcopy(self.endpoint_map)

    @classmethod
    def from_file(cls, file_path):
        log.info("Loading config")
        try:
            with open(file_path) as f:
                config_from_file = json.load(f)
        except Exception as e:
            log.warn(f"Failed to load config file: {e}")
            log.warn("Continuing with empty config")
            config_from_file = {}

        return GlobalConfig(**config_from_file)


class Handler(object):
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
