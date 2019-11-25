import asyncio
import itertools
import logging
from argparse import ArgumentParser
from typing import List

from aiohttp import web
from ophiuchus.cli.subcommands import Subcommand
from ophiuchus.framework import GlobalConfig
from ophiuchus.framework import Handler
from ophiuchus.framework import routes
from ophiuchus.utils import load_entry_points


log = logging.getLogger(__name__)
app_runners = {}


def aiohttp_wrapper(site_group, handler: Handler):
    async def wrapper(request):
        log.info(
            f"Received {request.method} request for {site_group}{request.path} "
            f"from {request._transport_peername[0]}:"
            f"{request._transport_peername[1]}",
        )
        log.debug(f"Request details: {request.__dict__}")

        try:
            # Get the formatter if present
            # Nasty, but, it works. I'm open to alternatives...
            event_resource = request.match_info.route.resource._formatter
        except AttributeError:
            # Fallback for simpler resources
            event_resource = request.path

        event = {
            "httpMethod": request.method,
            "path": request.path,
            "pathParameters": {
                key: value for key, value in request.match_info.items()
            },
            "queryStringParameters": {
                key: value for key, value in request.query.items()
            },
            "headers": {key: value for key, value in request.headers.items()},
            "requestContext": {
                "identity": {
                    "sourceIp": request.remote,
                    "userAgent": request.headers.get("user-agent", "null"),
                },
            },
            "resource": event_resource,
            "body": str(await request.read(), "utf-8"),
        }
        context = None

        log.debug(f"Constructed synthetic event: {event}")

        raw_response = getattr(handler, request.method)(event, context)

        if raw_response is None:
            raw_response = {}

        response = web.Response(headers=raw_response.get("headers", {}))
        response.body = raw_response.get("body", "")
        response.content_type = response.headers.get("Content-Type")

        return response

    return wrapper


async def start_site(
    site_group: str,
    conf: GlobalConfig,
    address: str = "127.0.0.1",
    port: int = 3000,
):
    web_app = web.Application()

    for handler_name, handler_class in load_entry_points(
        site_group, Handler,
    ).items():
        handler = handler_class(conf)
        for route, verb in itertools.product(
            routes[f"{handler_class.__module__}.{handler_class.__name__}"],
            [
                "GET",
                "HEAD",
                "POST",
                "PUT",
                "DELETE",
                "CONNECT",
                "OPTIONS",
                "TRACE",
                "PATCH",
            ],
        ):
            if not hasattr(handler, verb) or not callable(
                getattr(handler, verb),
            ):
                continue
            log.debug(f"Adding route '{route}' for {verb} to {site_group}")
            web_app.router.add_route(
                verb, route, aiohttp_wrapper(site_group, handler),
            )

    web_app_runner = web.AppRunner(web_app)
    await web_app_runner.setup()
    app_runners[site_group] = web_app_runner

    web_app_server = web.TCPSite(web_app_runner, address, port)
    await web_app_server.start()

    log.info(f"Running {site_group} on http://{address}:{port}")


class Run(Subcommand):
    description = "Run website locally"

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser)

        parser.add_argument(
            "--listen-address",
            default="127.0.0.1",
            type=str,
            help="Address to start local servers on. (Default: '%(default)s')",
        )
        parser.add_argument(
            "--first-listen-port",
            default=3000,
            type=int,
            help="Port to start first service on. (Default: %(default)i)",
        )
        parser.add_argument(
            "site_groups",
            nargs="+",
            metavar="site_group",
            type=str,
            help="Entry point group name(s) for website Lambda handlers",
        )

    def __call__(
        self,
        site_groups: List[str],
        listen_address: str,
        first_listen_port: List[int],
        *args,
        **kwargs,
    ) -> int:
        conf = GlobalConfig()
        loop = asyncio.get_event_loop()

        port = first_listen_port

        for site_group in site_groups:
            loop.create_task(
                start_site(site_group, conf, listen_address, port),
            )
            conf.add_endpoint(site_group, f"http://{listen_address}:{port}")
            port += 1

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            self.log.error("Keyboard Interrupt!")
        finally:
            for app_runner_name, app_runner in app_runners.items():
                self.log.info(f"Cleaning up {app_runner_name}")
                loop.run_until_complete(app_runner.cleanup())
