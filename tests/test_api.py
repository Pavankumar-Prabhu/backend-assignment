from __future__ import annotations

import io
import json
from pathlib import Path
import shutil
import sys
import unittest
from urllib.parse import urlsplit
import uuid
from wsgiref.util import setup_testing_defaults


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from finance_api.app import FinanceApplication
from finance_api.config import Settings


class TestClient:
    def __init__(self, app: FinanceApplication) -> None:
        self.app = app

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, object] | None = None,
        token: str | None = None,
    ) -> tuple[int, dict[str, object] | None]:
        parsed = urlsplit(path)
        raw_body = json.dumps(body).encode("utf-8") if body is not None else b""

        environ: dict[str, object] = {}
        setup_testing_defaults(environ)
        environ["REQUEST_METHOD"] = method.upper()
        environ["PATH_INFO"] = parsed.path
        environ["QUERY_STRING"] = parsed.query
        environ["wsgi.input"] = io.BytesIO(raw_body)
        environ["CONTENT_LENGTH"] = str(len(raw_body))
        environ["CONTENT_TYPE"] = "application/json" if body is not None else ""
        if token:
            environ["HTTP_AUTHORIZATION"] = f"Bearer {token}"

        response_state: dict[str, object] = {}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            response_state["status"] = status
            response_state["headers"] = headers

        chunks = self.app(environ, start_response)
        response_body = b"".join(chunks)
        status_code = int(str(response_state["status"]).split()[0])
        parsed_body = json.loads(response_body.decode("utf-8")) if response_body else None
        return status_code, parsed_body


class FinanceApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = PROJECT_ROOT / "data" / "test_runs" / uuid.uuid4().hex
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        settings = Settings(
            host="127.0.0.1",
            port=8000,
            db_path=self.temp_dir / "test.db",
            project_root=PROJECT_ROOT,
        )
        self.app = FinanceApplication(settings)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def login(self, email: str, password: str) -> str:
        status_code, payload = self.client.request(
            "POST",
            "/api/v1/auth/login",
            body={"email": email, "password": password},
        )
        self.assertEqual(status_code, 200)
        assert payload is not None
        return str(payload["access_token"])

    def create_record(self, token: str, **overrides: object) -> dict[str, object]:
        payload = {
            "amount": "2500.00",
            "type": "income",
            "category": "Consulting",
            "date": "2026-03-30",
            "notes": "March invoice",
        }
        payload.update(overrides)
        status_code, response = self.client.request("POST", "/api/v1/records", body=payload, token=token)
        self.assertEqual(status_code, 201)
        assert response is not None
        return dict(response["data"])

    def test_seeded_admin_can_log_in_and_view_profile(self) -> None:
        token = self.login("admin@finance.local", "Admin123!")
        status_code, payload = self.client.request("GET", "/api/v1/me", token=token)

        self.assertEqual(status_code, 200)
        assert payload is not None
        self.assertEqual(payload["user"]["role"], "admin")
        self.assertEqual(payload["user"]["email"], "admin@finance.local")

    def test_viewer_can_read_dashboard_but_not_records(self) -> None:
        admin_token = self.login("admin@finance.local", "Admin123!")
        self.create_record(admin_token, amount="500.00", type="expense", category="Tools")

        viewer_token = self.login("viewer@finance.local", "Viewer123!")
        summary_status, summary_payload = self.client.request("GET", "/api/v1/dashboard/summary", token=viewer_token)
        records_status, records_payload = self.client.request("GET", "/api/v1/records", token=viewer_token)

        self.assertEqual(summary_status, 200)
        assert summary_payload is not None
        self.assertEqual(summary_payload["totals"]["expenses"]["amount"], "500.00")
        self.assertEqual(records_status, 403)
        assert records_payload is not None
        self.assertEqual(records_payload["error"]["code"], "forbidden")

    def test_analyst_can_read_records_but_cannot_create_them(self) -> None:
        admin_token = self.login("admin@finance.local", "Admin123!")
        self.create_record(admin_token)

        analyst_token = self.login("analyst@finance.local", "Analyst123!")
        list_status, list_payload = self.client.request("GET", "/api/v1/records", token=analyst_token)
        create_status, create_payload = self.client.request(
            "POST",
            "/api/v1/records",
            token=analyst_token,
            body={
                "amount": "100.00",
                "type": "income",
                "category": "Bonus",
                "date": "2026-04-01",
                "notes": "Should fail",
            },
        )

        self.assertEqual(list_status, 200)
        assert list_payload is not None
        self.assertEqual(list_payload["meta"]["total"], 1)
        self.assertEqual(create_status, 403)
        assert create_payload is not None
        self.assertEqual(create_payload["error"]["code"], "forbidden")

    def test_admin_can_create_filter_update_and_delete_records(self) -> None:
        admin_token = self.login("admin@finance.local", "Admin123!")
        created = self.create_record(admin_token)

        list_status, list_payload = self.client.request(
            "GET",
            "/api/v1/records?category=Consulting&type=income",
            token=admin_token,
        )
        self.assertEqual(list_status, 200)
        assert list_payload is not None
        self.assertEqual(list_payload["meta"]["total"], 1)

        record_id = created["id"]
        update_status, update_payload = self.client.request(
            "PATCH",
            f"/api/v1/records/{record_id}",
            token=admin_token,
            body={"amount": "3000.00", "notes": "Updated invoice"},
        )
        self.assertEqual(update_status, 200)
        assert update_payload is not None
        self.assertEqual(update_payload["data"]["amount"], "3000.00")
        self.assertEqual(update_payload["data"]["notes"], "Updated invoice")

        delete_status, _ = self.client.request("DELETE", f"/api/v1/records/{record_id}", token=admin_token)
        fetch_status, fetch_payload = self.client.request("GET", f"/api/v1/records/{record_id}", token=admin_token)
        self.assertEqual(delete_status, 204)
        self.assertEqual(fetch_status, 404)
        assert fetch_payload is not None
        self.assertEqual(fetch_payload["error"]["code"], "not_found")

    def test_admin_can_manage_users_but_cannot_delete_self(self) -> None:
        admin_token = self.login("admin@finance.local", "Admin123!")

        create_status, create_payload = self.client.request(
            "POST",
            "/api/v1/users",
            token=admin_token,
            body={
                "full_name": "QA User",
                "email": "qa@finance.local",
                "password": "QaUser123!",
                "role": "viewer",
                "status": "active",
            },
        )
        self.assertEqual(create_status, 201)
        assert create_payload is not None
        user_id = create_payload["data"]["id"]

        patch_status, patch_payload = self.client.request(
            "PATCH",
            f"/api/v1/users/{user_id}",
            token=admin_token,
            body={"status": "inactive", "role": "analyst"},
        )
        self.assertEqual(patch_status, 200)
        assert patch_payload is not None
        self.assertEqual(patch_payload["data"]["status"], "inactive")
        self.assertEqual(patch_payload["data"]["role"], "analyst")

        self_delete_status, self_delete_payload = self.client.request("DELETE", "/api/v1/users/1", token=admin_token)
        self.assertEqual(self_delete_status, 409)
        assert self_delete_payload is not None
        self.assertEqual(self_delete_payload["error"]["code"], "conflict")

    def test_validation_errors_return_422(self) -> None:
        admin_token = self.login("admin@finance.local", "Admin123!")
        status_code, payload = self.client.request(
            "POST",
            "/api/v1/records",
            token=admin_token,
            body={
                "amount": "-10",
                "type": "income",
                "category": "Consulting",
                "date": "2026-13-01",
                "notes": "Invalid payload",
            },
        )

        self.assertEqual(status_code, 422)
        assert payload is not None
        self.assertEqual(payload["error"]["code"], "validation_error")


if __name__ == "__main__":
    unittest.main()
