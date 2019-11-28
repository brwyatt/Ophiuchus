import asyncio
import itertools
import logging
import re
from argparse import ArgumentParser
from typing import List

from aiohttp import web
from ophiuchus.cli.subcommands import EntryPointBuilderSubcommand
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
    allow_unsupported_routes: bool = False,
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

            # Check for unsupported route variables
            if re.search(r"\{[^}]*:[^}]*\}", route):
                msg = (
                    f"Unsupported route variable detected in '{route}'. While "
                    "aiohttp supports regex matches, API Gateway does not. "
                    "Only `{variable+}` is supported: "
                    "https://docs.aws.amazon.com/"
                    "apigateway/latest/developerguide/"
                    "api-gateway-method-settings-method-request.html"
                )
                if not allow_unsupported_routes:
                    log.critical(msg)
                    log.critical(
                        "If you know what you are doing, unsupported route "
                        "varables can be enabled with the "
                        "`--allow-unsupported-routes` flag, but is not "
                        "recommended.",
                    )
                    raise ValueError("Unsupported route path variable.")
                else:
                    log.warning(msg)

            # Convert API Gateway `{proxy+}` into aiohttp `{proxy:.*}`
            route = re.sub(r"(\{[^}]*)\+(\})", r"\1:.*\2", route)

            web_app.router.add_route(
                verb, route, aiohttp_wrapper(site_group, handler),
            )

    web_app_runner = web.AppRunner(web_app)
    await web_app_runner.setup()
    app_runners[site_group] = web_app_runner

    web_app_server = web.TCPSite(web_app_runner, address, port)
    await web_app_server.start()

    log.info(f"Running {site_group} on http://{address}:{port}")


class Run(EntryPointBuilderSubcommand):
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
            "--allow-unsupported-routes",
            default=False,
            action="store_true",
            help="Allow routes that are only supported in aiohttp, but not in "
            "API Gateway. Potentially unsafe and not recommended. Only use "
            "this if you really know what you're doing",
        )

    def __call__(
        self,
        site_groups: List[str],
        listen_address: str,
        first_listen_port: List[int],
        allow_unsupported_routes: bool,
        additional_endpoints: List[List[str]] = [],
        *args,
        **kwargs,
    ) -> int:
        conf = GlobalConfig()
        loop = asyncio.get_event_loop()

        port = first_listen_port

        # Add additional endpoints to config first.
        # This way, any included locally will over-ride them.
        for site_group, endpoint in additional_endpoints:
            self.log.debug(
                f"Adding additional named endpoint {site_group} at {endpoint}",
            )
            conf.add_endpoint(site_group, endpoint)

        for site_group in site_groups:
            loop.create_task(
                start_site(
                    site_group,
                    conf,
                    address=listen_address,
                    port=port,
                    allow_unsupported_routes=allow_unsupported_routes,
                ),
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
