"""Connection setup routes: credentials are checked before saving and never returned."""

from __future__ import annotations

import json
import logging
import stat

import pytest

from backend.platform.bcourses import BCoursesUnavailable
from backend.platform.google import client_file, token_file
from backend.platform.secrets import read_secret, secrets_file

TOKEN = "1072~SecretTokenValue123"
SECRET = "GOCSPX-very-secret"


def _client_json(client_id="123-abc.apps.googleusercontent.com", secret=SECRET, kind="installed"):
    return json.dumps({kind: {"client_id": client_id, "project_id": "p", "client_secret": secret,
                              "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                              "token_uri": "https://oauth2.googleapis.com/token",
                              "redirect_uris": ["http://localhost"]}})


@pytest.fixture
def checks(client):
    seen: list[str] = []
    outcome: dict[str, object] = {"error": None}

    def checker(token):
        seen.append(token)
        if outcome["error"]:
            raise outcome["error"]
    client.app.state.bcourses_token_checker = checker
    return seen, outcome


def test_nothing_is_set_at_first(client):
    state = client.get("/api/connections").json()
    assert state["bcourses"] == {"set": False, "saved_at": None, "checked_at": None, "check_ok": None, "check_message": None}
    assert state["google"]["set"] is False and state["google"]["connected"] is False
    assert state["folder"].endswith(secrets_file().parent.name)


def test_token_is_checked_saved_owner_only_and_never_returned(client, checks, caplog):
    seen, _ = checks
    secrets_file().parent.mkdir(parents=True, exist_ok=True)
    secrets_file().write_text("# my notes\nOTHER=x\nBCOURSES_TOKEN=old\n")
    with caplog.at_level(logging.DEBUG):
        response = client.put("/api/connections/bcourses", json={"token": f"  {TOKEN}\n"})
    assert response.status_code == 200 and seen == [TOKEN]
    assert TOKEN not in response.text and TOKEN not in caplog.text
    state = response.json()["bcourses"]
    assert state["set"] and state["saved_at"] and state["check_ok"] is True
    assert read_secret("BCOURSES_TOKEN") == TOKEN and read_secret("OTHER") == "x"
    assert secrets_file().read_text().startswith("# my notes\n")
    assert stat.S_IMODE(secrets_file().stat().st_mode) == 0o600
    assert stat.S_IMODE(secrets_file().parent.stat().st_mode) == 0o700
    assert TOKEN not in client.get("/api/connections").text
    assert client.get("/api/bcourses").json()["configured"] is True


def test_rejected_token_keeps_the_old_one(client, checks):
    _, outcome = checks
    client.put("/api/connections/bcourses", json={"token": "good-token"})
    outcome["error"] = BCoursesUnavailable("bcourses_token_rejected", "no")
    response = client.put("/api/connections/bcourses", json={"token": TOKEN})
    assert response.status_code == 422 and TOKEN not in response.text
    assert response.json()["error"]["field"] == "token" and "previous token was kept" in response.json()["error"]["message"]
    assert read_secret("BCOURSES_TOKEN") == "good-token"


def test_unreachable_bcourses_saves_nothing(client, checks):
    _, outcome = checks
    outcome["error"] = BCoursesUnavailable("bcourses_unreachable", "Cannot reach bCourses.")
    response = client.put("/api/connections/bcourses", json={"token": TOKEN})
    assert response.status_code == 502 and "nothing was changed" in response.json()["error"]["message"]
    assert read_secret("BCOURSES_TOKEN") is None and TOKEN not in response.text


@pytest.mark.parametrize("token", ["two words", "", "x" * 600, "tab\there"])
def test_malformed_tokens_are_refused_without_a_check_or_echo(client, checks, token):
    seen, _ = checks
    response = client.put("/api/connections/bcourses", json={"token": token})
    assert response.status_code == 422 and seen == []
    assert (token not in response.text) if token.strip() else True
    assert read_secret("BCOURSES_TOKEN") is None


def test_check_and_remove_token(client, checks):
    _, outcome = checks
    assert client.post("/api/connections/bcourses/check").status_code == 422
    client.put("/api/connections/bcourses", json={"token": TOKEN})
    outcome["error"] = BCoursesUnavailable("bcourses_token_rejected", "no")
    state = client.post("/api/connections/bcourses/check").json()["bcourses"]
    assert state["set"] and state["check_ok"] is False and "did not accept" in state["check_message"]
    state = client.delete("/api/connections/bcourses").json()["bcourses"]
    assert state == {"set": False, "saved_at": None, "checked_at": None, "check_ok": None, "check_message": None}
    assert read_secret("BCOURSES_TOKEN") is None


@pytest.mark.parametrize("text,phrase", [
    ("not json", "not JSON"),
    (_client_json(kind="web"), "Web application"),
    (_client_json(client_id="someone-else"), "missing"),
    (_client_json(secret=" "), "missing"),
    (json.dumps({"installed": {"client_id": "a.apps.googleusercontent.com", "client_secret": SECRET,
                               "auth_uri": "https://evil.example/", "token_uri": "https://oauth2.googleapis.com/token"}}), "missing"),
])
def test_bad_google_files_keep_the_old_one(client, text, phrase):
    assert client.put("/api/connections/google", json={"client_file": _client_json(secret="first")}).status_code == 200
    response = client.put("/api/connections/google", json={"client_file": text})
    assert response.status_code == 422 and phrase in response.json()["error"]["message"]
    assert SECRET not in response.text
    assert json.loads(client_file().read_text())["installed"]["client_secret"] == "first"


def test_google_file_saved_trimmed_owner_only_and_never_returned(client):
    response = client.put("/api/connections/google", json={"client_file": _client_json()})
    assert response.status_code == 200 and SECRET not in response.text and "123-abc" not in response.text
    assert response.json()["google"]["set"] is True and response.json()["google"]["check_ok"] is True
    stored = json.loads(client_file().read_text())
    assert set(stored["installed"]) == {"client_id", "client_secret", "auth_uri", "token_uri"}
    assert stat.S_IMODE(client_file().stat().st_mode) == 0o600
    assert client.get("/api/google").json()["configured"] is True


def test_replacing_with_another_client_signs_out_but_the_same_client_does_not(client):
    client.put("/api/connections/google", json={"client_file": _client_json()})
    token_file().write_text(json.dumps({"refresh_token": "r", "scope": ""}))
    client.put("/api/connections/google", json={"client_file": _client_json(secret="rotated")})
    assert client.get("/api/connections").json()["google"]["connected"] is True
    client.put("/api/connections/google", json={"client_file": _client_json(client_id="999-new.apps.googleusercontent.com")})
    assert client.get("/api/connections").json()["google"]["connected"] is False and not token_file().exists()


def test_removing_the_google_file_also_signs_out(client):
    client.put("/api/connections/google", json={"client_file": _client_json()})
    token_file().write_text(json.dumps({"refresh_token": "r", "scope": ""}))
    state = client.delete("/api/connections/google").json()["google"]
    assert state["set"] is False and state["connected"] is False
    assert not client_file().exists() and not token_file().exists()


def test_other_websites_cannot_change_credentials(client, checks):
    for method, path, body in (("put", "/api/connections/bcourses", {"token": TOKEN}),
                               ("put", "/api/connections/google", {"client_file": _client_json()}),
                               ("delete", "/api/connections/google", None)):
        response = client.request(method.upper(), path, json=body, headers={"Origin": "https://evil.example"})
        assert response.status_code == 403
    assert checks[0] == [] and read_secret("BCOURSES_TOKEN") is None and not client_file().exists()


def test_status_file_holds_no_credentials(client, checks):
    client.put("/api/connections/bcourses", json={"token": TOKEN})
    client.put("/api/connections/google", json={"client_file": _client_json()})
    status = (secrets_file().parent / "status.json").read_text()
    assert TOKEN not in status and SECRET not in status and "googleusercontent" not in status


def test_real_token_check_is_one_small_read_only_request(monkeypatch):
    from backend.platform.bcourses import BCoursesClient

    class Reply:
        headers = {"Link": '<https://bcourses.berkeley.edu/api/v1/courses?page=2>; rel="next"'}

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self, *args):
            data, self.body = getattr(self, "body", b"[]"), b""
            return data

    seen = []
    checker = BCoursesClient(token=TOKEN)
    monkeypatch.setattr(checker._opener, "open", lambda request, timeout: (seen.append(request), Reply())[1])
    checker.check()
    assert len(seen) == 1 and seen[0].get_method() == "GET" and "per_page=1" in seen[0].full_url
    assert seen[0].full_url.startswith("https://bcourses.berkeley.edu/api/v1/courses?") and TOKEN not in seen[0].full_url


def test_failed_google_save_keeps_the_old_file_and_sign_in(client, monkeypatch):
    from backend.routes import connections

    client.put("/api/connections/google", json={"client_file": _client_json()})
    token_file().write_text(json.dumps({"refresh_token": "r", "scope": ""}))

    def full_disk(path, data):
        raise OSError(28, "No space left on device")
    monkeypatch.setattr(connections, "write_private_file", full_disk)
    other = _client_json(client_id="999-new.apps.googleusercontent.com")
    with pytest.raises(OSError):
        client.put("/api/connections/google", json={"client_file": other})
    assert token_file().exists() and "123-abc" in client_file().read_text()
