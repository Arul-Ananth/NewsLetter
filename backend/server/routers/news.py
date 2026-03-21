import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from backend.common.config import settings
from backend.common.database import get_session
from backend.common.models.schemas import (
    FeedbackRequest,
    FeedbackResponse,
    NewsRequest,
    NewsResponse,
    ProfileResponse,
)
from backend.common.services.auth.resolver import get_current_principal
from backend.common.services.auth.types import AuthPrincipal
from backend.common.services.llm.newsletter_service import newsletter_service
from backend.common.services.memory import vector_db
from backend.server.services import billing

logger = logging.getLogger(__name__)

router = APIRouter(tags=["News"])


@router.post("/generate", response_model=NewsResponse)
async def generate_news(
    request: NewsRequest,
    principal: AuthPrincipal = Depends(get_current_principal),
    session: Session = Depends(get_session),
):
    billing.check_funds(session, principal.user_id)

    context = vector_db.get_user_context(principal.user_id, request.topic)

    try:
        api_keys = {
            "serper_api_key": request.serper_api_key,
            "openai_api_key": request.openai_api_key,
        }
        result_response = await newsletter_service.generate_newsletter(
            topic=request.topic,
            user_id=principal.user_id,
            context=str(context),
            api_keys=api_keys,
        )
        content = result_response.content
        input_tok = 100
        output_tok = 100
    except Exception as exc:
        logger.exception("Newsletter generation failed: %s", exc)
        raise HTTPException(status_code=500, detail="Newsletter generation failed.") from exc

    receipt = billing.process_transaction(session, principal.user_id, request.topic, input_tok, output_tok)

    return NewsResponse(
        topic=request.topic,
        content=content,
        bill=receipt,
    )


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(
    feedback: FeedbackRequest,
    principal: AuthPrincipal = Depends(get_current_principal),
):
    vector_db.save_feedback(
        principal.user_id,
        feedback.original_topic,
        feedback.feedback_text,
        feedback.sentiment,
    )
    return FeedbackResponse(status="Feedback recorded")


@router.get("/profile", response_model=ProfileResponse)
def get_current_profile(
    principal: AuthPrincipal = Depends(get_current_principal),
):
    memories = vector_db.fetch_memories(principal.user_id)
    return ProfileResponse(memories=memories)


@router.get("/profile/{user_id}", response_model=ProfileResponse)
def get_profile(
    user_id: int,
    principal: AuthPrincipal = Depends(get_current_principal),
):
    if not settings.is_trusted_lan_auth() and user_id != principal.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this profile")

    effective_user_id = principal.user_id if settings.is_trusted_lan_auth() else user_id
    memories = vector_db.fetch_memories(effective_user_id)
    return ProfileResponse(memories=memories)
