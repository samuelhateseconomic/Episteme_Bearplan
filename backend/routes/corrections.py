from fastapi import APIRouter, Request
from pydantic import StrictStr

from backend.domain.corrections import CorrectionDraft, apply_correction, list_saved_sessions, preview_correction

router = APIRouter(prefix="/api/sessions")


class ApplyRequest(CorrectionDraft):
    preview_token: StrictStr
    operation_id: StrictStr


@router.get("")
def saved_sessions(request: Request) -> dict:
    return {"sessions": list_saved_sessions(request.app.state.db)}


@router.post("/{session_id}/correction/preview")
def preview(session_id: str, body: CorrectionDraft, request: Request) -> dict:
    return preview_correction(request.app.state.db, session_id, body)


@router.post("/{session_id}/correction")
def apply(session_id: str, body: ApplyRequest, request: Request) -> dict:
    return apply_correction(request.app.state.db, session_id,
                            CorrectionDraft(**body.model_dump(exclude={"operation_id", "preview_token"})),
                            body.preview_token, body.operation_id)
