from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
import json
from typing import Any, Callable
from urllib.parse import parse_qs
import re

from .api_spec import get_openapi_spec
from .config import Settings
from .database import Database
from .docs import render_docs_html
from .errors import ApiError
from .permissions import ensure_permission
from .services import dashboard, records, users


Handler = Callable[..., "Response"]


@dataclass
class Route:
    method: str
    pattern: re.Pattern[str]
    handler: Handler
    require_auth: bool = False
    permission: str | None = None


@dataclass
class Response:
    status_code: int
    body: Any | None = None
    content_type: str = "application/json; charset=utf-8"


class Request:
    def __init__(self, environ: dict[str, Any]) -> None:
        self.environ = environ
        self.method = environ.get("REQUEST_METHOD", "GET").upper()
        self.path = environ.get("PATH_INFO", "/")
        self.query = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True)
        self.headers = self._extract_headers(environ)
        self._body: bytes | None = None
        self._json: Any | None = None

    def _extract_headers(self, environ: dict[str, Any]) -> dict[str, str]:
        headers: dict[str, str] = {}
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                normalized = key[5:].replace("_", "-").title()
                headers[normalized] = value
        if environ.get("CONTENT_TYPE"):
            headers["Content-Type"] = environ["CONTENT_TYPE"]
        if environ.get("CONTENT_LENGTH"):
            headers["Content-Length"] = environ["CONTENT_LENGTH"]
        return headers

    @property
    def body(self) -> bytes:
        if self._body is None:
            content_length = self.environ.get("CONTENT_LENGTH", "")
            try:
                body_length = int(content_length) if content_length else 0
            except ValueError:
                body_length = 0
            self._body = self.environ["wsgi.input"].read(body_length)
        return self._body

    def json(self) -> Any:
        if self._json is not None:
            return self._json
        if not self.body:
            self._json = {}
            return self._json
        try:
            self._json = json.loads(self.body.decode("utf-8"))
            return self._json
        except json.JSONDecodeError as exc:
            raise ApiError(400, "Malformed JSON body.", code="invalid_json") from exc

    def bearer_token(self) -> str | None:
        raw_value = self.headers.get("Authorization")
        if not raw_value:
            return None
        parts = raw_value.split(" ", maxsplit=1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise ApiError(
                401,
                "Authorization header must use Bearer <token> format.",
                code="unauthorized",
            )
        return parts[1].strip()


class FinanceApplication:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.database = Database(settings.db_path)
        self.database.initialize()
        self.routes = self._build_routes()

    def _build_routes(self) -> list[Route]:
        return [
            Route("GET", re.compile(r"^/health$"), self.healthcheck),
            Route("GET", re.compile(r"^/docs$"), self.docs_page),
            Route("GET", re.compile(r"^/openapi\.json$"), self.openapi_document),
            Route("POST", re.compile(r"^/api/v1/auth/login$"), self.login),
            Route("POST", re.compile(r"^/api/v1/auth/logout$"), self.logout, require_auth=True),
            Route("GET", re.compile(r"^/api/v1/me$"), self.me, require_auth=True),
            Route(
                "GET",
                re.compile(r"^/api/v1/users$"),
                self.list_users,
                require_auth=True,
                permission="users:read",
            ),
            Route(
                "POST",
                re.compile(r"^/api/v1/users$"),
                self.create_user,
                require_auth=True,
                permission="users:write",
            ),
            Route(
                "GET",
                re.compile(r"^/api/v1/users/(?P<user_id>[^/]+)$"),
                self.get_user,
                require_auth=True,
                permission="users:read",
            ),
            Route(
                "PATCH",
                re.compile(r"^/api/v1/users/(?P<user_id>[^/]+)$"),
                self.update_user,
                require_auth=True,
                permission="users:write",
            ),
            Route(
                "DELETE",
                re.compile(r"^/api/v1/users/(?P<user_id>[^/]+)$"),
                self.delete_user,
                require_auth=True,
                permission="users:write",
            ),
            Route(
                "GET",
                re.compile(r"^/api/v1/records$"),
                self.list_records,
                require_auth=True,
                permission="records:read",
            ),
            Route(
                "POST",
                re.compile(r"^/api/v1/records$"),
                self.create_record,
                require_auth=True,
                permission="records:write",
            ),
            Route(
                "GET",
                re.compile(r"^/api/v1/records/(?P<record_id>[^/]+)$"),
                self.get_record,
                require_auth=True,
                permission="records:read",
            ),
            Route(
                "PATCH",
                re.compile(r"^/api/v1/records/(?P<record_id>[^/]+)$"),
                self.update_record,
                require_auth=True,
                permission="records:write",
            ),
            Route(
                "DELETE",
                re.compile(r"^/api/v1/records/(?P<record_id>[^/]+)$"),
                self.delete_record,
                require_auth=True,
                permission="records:write",
            ),
            Route(
                "GET",
                re.compile(r"^/api/v1/dashboard/summary$"),
                self.summary,
                require_auth=True,
                permission="dashboard:read",
            ),
            Route(
                "GET",
                re.compile(r"^/api/v1/dashboard/category-breakdown$"),
                self.category_breakdown,
                require_auth=True,
                permission="dashboard:read",
            ),
            Route(
                "GET",
                re.compile(r"^/api/v1/dashboard/trends$"),
                self.trends,
                require_auth=True,
                permission="dashboard:read",
            ),
            Route(
                "GET",
                re.compile(r"^/api/v1/dashboard/recent-activity$"),
                self.recent_activity,
                require_auth=True,
                permission="dashboard:read",
            ),
        ]

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]) -> list[bytes]:
        request = Request(environ)

        if request.method == "OPTIONS":
            return self._send_response(start_response, Response(204, None))

        try:
            response = self._dispatch(request)
        except ApiError as exc:
            response = Response(exc.status_code, exc.to_dict())
        except Exception:
            response = Response(
                500,
                {
                    "error": {
                        "code": "internal_error",
                        "message": "An unexpected server error occurred.",
                    }
                },
            )
        return self._send_response(start_response, response)

    def _dispatch(self, request: Request) -> Response:
        allowed_methods: set[str] = set()
        for route in self.routes:
            match = route.pattern.match(request.path)
            if not match:
                continue
            allowed_methods.add(route.method)
            if route.method != request.method:
                continue

            current_user: dict[str, object] | None = None
            if route.require_auth:
                current_user = users.authenticate_request(self.database, request.bearer_token())
            if route.permission and current_user is not None:
                ensure_permission(current_user, route.permission)

            return route.handler(request=request, current_user=current_user, **match.groupdict())

        if allowed_methods:
            raise ApiError(
                405,
                "Method not allowed.",
                code="method_not_allowed",
                details={"allowed_methods": sorted(allowed_methods)},
            )
        raise ApiError(404, "Route not found.", code="not_found")

    def _send_response(self, start_response: Callable[..., Any], response: Response) -> list[bytes]:
        headers = [
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Headers", "Authorization, Content-Type"),
            ("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS"),
        ]

        body_bytes = b""
        if response.body is not None:
            if response.content_type.startswith("application/json"):
                body_bytes = json.dumps(response.body, indent=2).encode("utf-8")
            else:
                body_bytes = str(response.body).encode("utf-8")

        headers.append(("Content-Type", response.content_type))
        headers.append(("Content-Length", str(len(body_bytes))))
        start_response(f"{response.status_code} {HTTPStatus(response.status_code).phrase}", headers)
        return [body_bytes]

    def healthcheck(self, request: Request, current_user: dict[str, object] | None = None) -> Response:
        return Response(200, {"status": "ok", "service": "finance-dashboard-backend"})

    def docs_page(self, request: Request, current_user: dict[str, object] | None = None) -> Response:
        return Response(200, render_docs_html(), content_type="text/html; charset=utf-8")

    def openapi_document(self, request: Request, current_user: dict[str, object] | None = None) -> Response:
        return Response(200, get_openapi_spec())

    def login(self, request: Request, current_user: dict[str, object] | None = None) -> Response:
        return Response(200, users.authenticate_login(self.database, request.json()))

    def logout(self, request: Request, current_user: dict[str, object] | None = None) -> Response:
        assert current_user is not None
        return Response(200, users.logout(self.database, current_user))

    def me(self, request: Request, current_user: dict[str, object] | None = None) -> Response:
        assert current_user is not None
        return Response(
            200,
            {
                "user": {
                    "id": current_user["id"],
                    "full_name": current_user["full_name"],
                    "email": current_user["email"],
                    "role": current_user["role"],
                    "status": current_user["status"],
                }
            },
        )

    def list_users(self, request: Request, current_user: dict[str, object] | None = None) -> Response:
        return Response(200, {"data": users.list_users(self.database)})

    def create_user(self, request: Request, current_user: dict[str, object] | None = None) -> Response:
        return Response(201, {"data": users.create_user(self.database, request.json())})

    def get_user(self, request: Request, user_id: str, current_user: dict[str, object] | None = None) -> Response:
        return Response(200, {"data": users.get_user(self.database, user_id)})

    def update_user(self, request: Request, user_id: str, current_user: dict[str, object] | None = None) -> Response:
        assert current_user is not None
        return Response(
            200,
            {"data": users.update_user(self.database, user_id, request.json(), current_user)},
        )

    def delete_user(self, request: Request, user_id: str, current_user: dict[str, object] | None = None) -> Response:
        assert current_user is not None
        users.delete_user(self.database, user_id, current_user)
        return Response(204, None)

    def list_records(self, request: Request, current_user: dict[str, object] | None = None) -> Response:
        return Response(200, records.list_records(self.database, request.query))

    def create_record(self, request: Request, current_user: dict[str, object] | None = None) -> Response:
        assert current_user is not None
        return Response(201, {"data": records.create_record(self.database, request.json(), current_user)})

    def get_record(self, request: Request, record_id: str, current_user: dict[str, object] | None = None) -> Response:
        return Response(200, {"data": records.get_record(self.database, record_id)})

    def update_record(self, request: Request, record_id: str, current_user: dict[str, object] | None = None) -> Response:
        assert current_user is not None
        return Response(
            200,
            {"data": records.update_record(self.database, record_id, request.json(), current_user)},
        )

    def delete_record(self, request: Request, record_id: str, current_user: dict[str, object] | None = None) -> Response:
        assert current_user is not None
        records.delete_record(self.database, record_id, current_user)
        return Response(204, None)

    def summary(self, request: Request, current_user: dict[str, object] | None = None) -> Response:
        return Response(200, dashboard.get_summary(self.database, request.query))

    def category_breakdown(self, request: Request, current_user: dict[str, object] | None = None) -> Response:
        return Response(200, dashboard.get_category_breakdown(self.database, request.query))

    def trends(self, request: Request, current_user: dict[str, object] | None = None) -> Response:
        return Response(200, dashboard.get_trends(self.database, request.query))

    def recent_activity(self, request: Request, current_user: dict[str, object] | None = None) -> Response:
        return Response(200, dashboard.get_recent_activity(self.database, request.query))

