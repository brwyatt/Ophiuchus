import asyncio
import logging
from argparse import ArgumentParser

from aiohttp import web
from ophiuchus.cli.subcommands import Subcommand
from ophiuchus.framework import GlobalConfig
from ophiuchus.framework import Handler
from ophiuchus.utils import load_entry_points


log = logging.getLogger(__name__)


def aiohttp_wrapper(handler: Handler):
    def wrapper(request):
        event = {}
        context = {}

        response = getattr(handler, request.method)(event, context)

        return response

    return wrapper


class Run(Subcommand):
    description = "Run website locally"

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser)

        parser.add_argument(
            "site_groups",
            nargs="+",
            metavar="site_group",
            type=str,
            help="Entry point group name(s) for website Lambda handlers",
        )

    def __call__(self, site_groups, *args, **kwargs) -> int:
        conf = GlobalConfig()
        loop = asyncio.get_event_loop()

        endpoint_prefix = "http://localhost"
        port = 3000

        web_app_list = {}

        for site_group in site_groups:
            web_app_list[site_group] = {}

            web_app = web.Application()
            web_app_list[site_group]["app"] = web_app

            for handler_name, handler_class in load_entry_points(
                site_group, Handler,
            ).items():
                handler = handler_class(conf)
                for route in handler_class.routes:
                    web_app.router.add_route(
                        "*", route, aiohttp_wrapper(handler),
                    )

            web_app_handler = web_app.make_handler()
            web_app_list[site_group]["handler"] = web_app_handler
            web_app_couroutine = loop.create_server(
                web_app_handler, "127.0.0.1", port,
            )
            web_app_server = loop.run_until_complete(web_app_couroutine)
            web_app_list[site_group]["server"] = web_app_server
            self.log.info(f"Running {site_group} on {endpoint_prefix}:{port}")

            conf.add_endpoint(site_group, f"{endpoint_prefix}:{port}")

            port += 1

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            self.log.error("Keyboard Interrupt!")
        finally:
            for site_group, site in web_app_list.items():
                self.log.info(f"Shutting down {site_group}")
                site["server"].close()
                loop.run_until_complete(site["app"].shutdown())
                loop.run_until_complete(site["handler"].shutdown(60.0))
                loop.run_until_complete(
                    site["handler"].finish_connections(1.0),
                )
                loop.run_until_complete(site["app"].cleanup())

        loop.close()
