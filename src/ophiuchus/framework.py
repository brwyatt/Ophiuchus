from typing import Dict


class GlobalConfig:
    def __init__(self):
        self.endpoint_map = {}

    def add_endpoint(self, site_group: str, endpoint: str):
        if site_group in self.endpoint_map:
            raise ValueError(f"{site_group} already has an endpoint")
        self.endpoint_map[site_group] = endpoint

    def get_endpoint(self, site_group: str):
        return self.endpoint_map.get(site_group, None)


class Handler:
    routes = []

    def __init__(self, config):
        self.config = config

    def GET(self, *args, **kwargs):
        pass

    def POST(self, *args, **kwargs):
        pass

    def PUT(self, *args, **kwargs):
        pass

    def OPTIONS(self, *args, **kwargs):
        pass


def route(*routes: str) -> Handler:
    def dec(handler: Handler):
        handler.routes = routes
        return handler

    return dec
