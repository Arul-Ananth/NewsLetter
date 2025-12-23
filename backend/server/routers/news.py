import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from backend.common.database import get_session
from backend.common.models.schemas import FeedbackRequest, NewsRequest, NewsResponse
from backend.common.models.sql import User
from backend.common.services import vector_db
from backend.common.services.newsletter_service import newsletter_service
from backend.server.dependencies import get_current_user
from backend.server.services import billing

logger = logging.getLogger(__name__)

router = APIRouter(tags=["News"])


@router.post("/generate", response_model=NewsResponse)
async def generate_news(
    request: NewsRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    billing.check_funds(session, current_user.id)

    context = vector_db.get_user_context(current_user.id, request.topic)

    try:
        api_keys = {
            "serper_api_key": request.serper_api_key,
            "openai_api_key": request.openai_api_key,
        }
        result_response = await newsletter_service.generate_newsletter(
            topic=request.topic,
            user_id=current_user.id,
            context=str(context),
            api_keys=api_keys,
        )
        content = result_response.content
        input_tok = 100
        output_tok = 100
    except Exception as exc:
        logger.exception("Newsletter generation failed: %s", exc)
        raise HTTPException(status_code=500, detail="Newsletter generation failed.")

    receipt = billing.process_transaction(session, current_user.id, request.topic, input_tok, output_tok)

    return {
        "topic": request.topic,
        "content": content,
        "bill": receipt,
    }


@router.post("/feedback")
def submit_feedback(
    feedback: FeedbackRequest,
    current_user: User = Depends(get_current_user),
):
    vector_db.save_feedback(
        current_user.id,
        feedback.original_topic,
        feedback.feedback_text,
        feedback.sentiment,
    )
    return {"status": "Feedback recorded"}


@router.get("/profile/{user_id}")
def get_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this profile")

    memories = vector_db.fetch_memories(user_id)
    return {"memories": memories}
