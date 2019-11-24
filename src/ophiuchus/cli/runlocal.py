import asyncio
import logging
from argparse import ArgumentParser

from aiohttp import web
from ophiuchus.cli.subcommands import Subcommand
from ophiuchus.framework import GlobalConfig
from ophiuchus.framework import Handler
from ophiuchus.utils import load_entry_points


log = logging.getLogger(__name__)
app_runners = {}


def aiohttp_wrapper(handler: Handler):
    def wrapper(request):
        log.info(
            f"Received {request.method} request for {request.path} from "
            f"{request._transport_peername[0]}:{request._transport_peername[1]}",
        )
        event = {}
        context = {}

        response = getattr(handler, request.method)(event, context)

        return response

    return wrapper


async def start_site(
    site_group, port, conf, endpoint_prefix="http://localhost"
):
    web_app = web.Application()

    for handler_name, handler_class in load_entry_points(
        site_group, Handler,
    ).items():
        handler = handler_class(conf)
        for route in handler_class.routes:
            web_app.router.add_route(
                "*", route, aiohttp_wrapper(handler),
            )

    web_app_runner = web.AppRunner(web_app)
    await web_app_runner.setup()
    app_runners[site_group] = web_app_runner

    web_app_server = web.TCPSite(web_app_runner, "localhost", port)
    await web_app_server.start()

    log.info(f"Running {site_group} on {endpoint_prefix}:{port}")


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

        for site_group in site_groups:
            loop.create_task(
                start_site(
                    site_group, port, conf, endpoint_prefix=endpoint_prefix,
                ),
            )
            conf.add_endpoint(site_group, f"{endpoint_prefix}:{port}")
            port += 1

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            self.log.error("Keyboard Interrupt!")
        finally:
            for app_runner_name, app_runner in app_runners.items():
                self.log.info(f"Cleaning up {app_runner_name}")
                loop.run_until_complete(app_runner.cleanup())
