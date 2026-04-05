from __future__ import annotations


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        code: str = "api_error",
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "error": {
                "code": self.code,
                "message": self.message,
            }
        }
        if self.details:
            payload["error"]["details"] = self.details
        return payload


def validation_error(details: dict[str, object]) -> ApiError:
    return ApiError(
        status_code=422,
        message="Validation failed.",
        code="validation_error",
        details=details,
    )

