from __future__ import annotations

from wsgiref.simple_server import make_server

from .app import FinanceApplication
from .config import get_settings


def run_server() -> None:
    settings = get_settings()
    application = FinanceApplication(settings)

    print("Finance API server starting...")
    print(f"Host: http://{settings.host}:{settings.port}")
    print(f"Docs: http://{settings.host}:{settings.port}/docs")
    print(f"OpenAPI: http://{settings.host}:{settings.port}/openapi.json")
    print("Seeded accounts:")
    print("  admin@finance.local / Admin123!")
    print("  analyst@finance.local / Analyst123!")
    print("  viewer@finance.local / Viewer123!")

    with make_server(settings.host, settings.port, application) as server:
        server.serve_forever()

