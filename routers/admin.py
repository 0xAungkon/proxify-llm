import json
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse

from config.settings import settings
from inc.TokenManager import decrypt_token, encrypt_token
from schema.AdminSchema import AdminLoginSchema

router = APIRouter(tags=["Admin"])

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"


def _get_log_root() -> Path:
	configured_log_folder = Path(settings.log_folder)
	if configured_log_folder.is_absolute():
		return configured_log_folder.resolve()
	return (BASE_DIR / configured_log_folder).resolve()


def _serialize_log_file(log_file: Path, log_root: Path) -> dict[str, str]:
	stats = log_file.stat()
	return {
		"full_path": str(log_file.resolve()),
		"relative_path": log_file.relative_to(log_root).as_posix(),
		"file_name": log_file.name,
		"date": datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).astimezone().isoformat(),
	}


def _list_log_files(log_root: Path, response_root: Path | None = None) -> list[dict[str, str]]:
	if not log_root.exists() or not log_root.is_dir():
		return []

	serialization_root = response_root or log_root
	log_files = [path for path in log_root.rglob("*.json") if path.is_file()]
	log_files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
	return [_serialize_log_file(log_file=log_file, log_root=serialization_root) for log_file in log_files]


def _resolve_log_path(log_path: str) -> Path:
	log_root = _get_log_root()
	candidate = Path(log_path)
	resolved_path = (candidate if candidate.is_absolute() else (log_root / candidate)).resolve()

	try:
		resolved_path.relative_to(log_root)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid log path") from exc

	if not resolved_path.exists():
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log path not found")

	return resolved_path


def _decode_admin_session(session_token: str) -> dict[str, str | float]:
	decrypted_token = decrypt_token(session_token)
	if decrypted_token.get("status") != "success":
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin session")

	try:
		session_data = json.loads(decrypted_token["data"])
	except (TypeError, json.JSONDecodeError) as exc:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin session") from exc

	if session_data.get("type") != "admin_session":
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin session")

	session_username = str(session_data.get("username", ""))
	if not secrets.compare_digest(session_username, settings.admin_username):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin session")

	expires_at = float(session_data.get("expires_at", 0))
	if expires_at <= time.time():
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin session expired")

	return session_data


def require_admin_session(request: Request) -> dict[str, str | float]:
	session_cookie = request.cookies.get(settings.admin_session_cookie_name)
	if not session_cookie:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing admin session")
	return _decode_admin_session(session_cookie)


def _has_valid_admin_session(request: Request) -> bool:
	session_cookie = request.cookies.get(settings.admin_session_cookie_name)
	if not session_cookie:
		return False

	try:
		_decode_admin_session(session_cookie)
	except HTTPException:
		return False

	return True


@router.post("/common/login")
async def login_admin(payload: AdminLoginSchema, request: Request, response: Response):
	if not settings.admin_username or not settings.admin_password:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Admin credentials are not configured",
		)

	username_is_valid = secrets.compare_digest(payload.username, settings.admin_username)
	password_is_valid = secrets.compare_digest(payload.password, settings.admin_password)

	if not (username_is_valid and password_is_valid):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

	issued_at = int(time.time())
	max_age_seconds = settings.admin_session_max_age_hours * 60 * 60
	session_payload = {
		"type": "admin_session",
		"username": settings.admin_username,
		"issued_at": issued_at,
		"expires_at": issued_at + max_age_seconds,
	}

	encrypted_session = encrypt_token(json.dumps(session_payload, separators=(",", ":")))
	if encrypted_session.get("status") != "success":
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Unable to create admin session",
		)

	session_token = encrypted_session["token"]
	response.set_cookie(
		key=settings.admin_session_cookie_name,
		value=session_token,
		max_age=max_age_seconds,
		httponly=True,
		secure=request.url.scheme == "https",
		samesite="lax",
		path="/",
	)

	return {
		"status": "success",
		"message": "Admin authentication successful",
		"cookie": session_token,
	}


@router.get("/admin/logs")
async def get_admin_logs(_: dict[str, str | float] = Depends(require_admin_session)):
	log_root = _get_log_root()
	return {
		"status": "success",
		"logs": _list_log_files(log_root=log_root),
	}


@router.delete("/admin/logs/clear")
async def clear_admin_logs(_: dict[str, str | float] = Depends(require_admin_session)):
	log_root = _get_log_root()
	if not log_root.exists() or not log_root.is_dir():
		return {"status": "success", "deleted": 0}

	deleted = 0
	errors: list[str] = []
	for log_file in log_root.rglob("*.json"):
		if not log_file.is_file():
			continue
		try:
			log_file.unlink()
			deleted += 1
		except OSError as exc:
			errors.append(f"{log_file.name}: {exc.strerror}")

	return {
		"status": "success" if not errors else "partial",
		"deleted": deleted,
		**({"errors": errors} if errors else {}),
	}


@router.delete("/admin/logs/delete/{log_path:path}")
async def delete_admin_log(
	log_path: str,
	_: dict[str, str | float] = Depends(require_admin_session),
):
	resolved_path = _resolve_log_path(log_path)
	if not resolved_path.is_file():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path is not a file")
	try:
		resolved_path.unlink()
	except OSError as exc:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
	return {"status": "success", "deleted": log_path}


@router.get("/admin/logs/curl/{log_path:path}")
async def get_admin_log_curl(
	log_path: str,
	_: dict[str, str | float] = Depends(require_admin_session),
):
	resolved_path = _resolve_log_path(log_path)
	if not resolved_path.is_file():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path is not a file")
	try:
		log_data = json.loads(resolved_path.read_text(encoding="utf-8", errors="replace"))
	except (json.JSONDecodeError, ValueError) as exc:
		raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unable to parse log file") from exc

	method = log_data.get("method", "POST")
	path = log_data.get("path", "").lstrip("/")
	request_body = log_data.get("request")
	upstream_url = f"http://{settings.ollama_host}:{settings.ollama_port}/{path}"

	parts = [f"curl -X {method}", f"'{upstream_url}'"]
	if request_body is not None:
		body_str = json.dumps(request_body, separators=(",", ":")).replace("'", "'\\''")
		parts.append("-H 'Content-Type: application/json'")
		parts.append(f"-d '{body_str}'")

	return {"status": "success", "curl": " \\\n  ".join(parts)}


@router.get("/admin/logs/download/{log_path:path}")
async def download_admin_log(
	log_path: str,
	_: dict[str, str | float] = Depends(require_admin_session),
):
	resolved_path = _resolve_log_path(log_path)
	if not resolved_path.is_file():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path is not a file")
	return FileResponse(
		path=str(resolved_path),
		filename=resolved_path.name,
		media_type="application/json",
	)


@router.post("/admin/logs/replay/{log_path:path}")
async def replay_admin_log(
	log_path: str,
	_: dict[str, str | float] = Depends(require_admin_session),
):
	resolved_path = _resolve_log_path(log_path)
	if not resolved_path.is_file():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path is not a file")
	try:
		log_data = json.loads(resolved_path.read_text(encoding="utf-8", errors="replace"))
	except (json.JSONDecodeError, ValueError) as exc:
		raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unable to parse log file") from exc

	method = log_data.get("method", "POST")
	path = log_data.get("path", "").lstrip("/")
	request_body = log_data.get("request")
	upstream_url = f"http://{settings.ollama_host}:{settings.ollama_port}/{path}"

	async def _stream():
		async with httpx.AsyncClient(timeout=None) as client:
			async with client.stream(
				method,
				upstream_url,
				json=request_body if isinstance(request_body, dict) else None,
			) as response:
				async for chunk in response.aiter_bytes():
					yield chunk

	return StreamingResponse(_stream(), media_type="application/json")


@router.get("/admin/logs/{log_path:path}")
async def get_admin_log_path(
	log_path: str,
	_: dict[str, str | float] = Depends(require_admin_session),
):
	log_root = _get_log_root()
	resolved_path = _resolve_log_path(log_path)

	if resolved_path.is_dir():
		return {
			"status": "success",
			"logs": _list_log_files(log_root=resolved_path, response_root=log_root),
		}

	return {
		"status": "success",
		"log": {
			**_serialize_log_file(log_file=resolved_path, log_root=log_root),
			"content": resolved_path.read_text(encoding="utf-8", errors="replace"),
		},
	}


@router.get("/app")
@router.get("/app/")
async def admin_dashboard(request: Request):
	if not _has_valid_admin_session(request):
		return RedirectResponse(url="/app/login", status_code=status.HTTP_302_FOUND)
	return FileResponse(TEMPLATE_DIR / "index.html")


@router.get("/app/login")
async def admin_login_page(request: Request):
	if _has_valid_admin_session(request):
		return RedirectResponse(url="/app", status_code=status.HTTP_302_FOUND)
	return FileResponse(TEMPLATE_DIR / "login.html")


@router.get("/app/logout")
async def admin_logout(request: Request):
	response = RedirectResponse(url="/app/login", status_code=status.HTTP_302_FOUND)
	response.delete_cookie(key=settings.admin_session_cookie_name, path="/")
	return response
