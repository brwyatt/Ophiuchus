import asyncio
import itertools
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
    async def wrapper(request):
        log.info(
            f"Received {request.method} request for {request.path} from "
            f"{request._transport_peername[0]}:"
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
    site_group, port, conf, endpoint_prefix="http://localhost"
):
    web_app = web.Application()

    for handler_name, handler_class in load_entry_points(
        site_group, Handler,
    ).items():
        handler = handler_class(conf)
        for route, verb in itertools.product(
            handler_class.routes,
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
                verb, route, aiohttp_wrapper(handler),
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
