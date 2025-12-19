from fastapi import APIRouter, Depends, HTTPException
import os
from sqlmodel import Session
from backend.server.database import get_session
from backend.server.dependencies import get_current_user
from backend.server.models.sql import User
from backend.server.models.schemas import NewsRequest, NewsResponse, FeedbackRequest
from backend.server.services import billing, vector_db
from backend.server.services.newsletter_service import newsletter_service
from backend.server.models.sql import User
from backend.server.dependencies import get_current_user

router = APIRouter(tags=["News"])

@router.post("/generate", response_model=NewsResponse)
async def generate_news(
    request: NewsRequest, 
    current_user: User = Depends(get_current_user), 
    session: Session = Depends(get_session)
):
    # 1. BILLING CHECK
    billing.check_funds(session, current_user.id)
    
    # 2. RETRIEVE CONTEXT (Chroma)
    context = vector_db.get_user_context(current_user.id, request.topic)
    
    # 3. RUN AGENT
    try:
        api_keys = {
            "serper_api_key": request.serper_api_key,
            "openai_api_key": request.openai_api_key
        }
        # Use Shared Service Layer
        result_response = await newsletter_service.generate_newsletter(
            topic=request.topic, 
            user_id=current_user.id,
            context=str(context),
            api_keys=api_keys
        )
        content = result_response.content
        
        # Estimate usage (mock for now or derive from response if added)
        input_tok = 100 
        output_tok = 100 
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # 4. CALCULATE TOKENS & DEDUCT FUNDS
    receipt = billing.process_transaction(
        session, current_user.id, request.topic, input_tok, output_tok
    )
    
    return {
        "topic": request.topic,
        "content": content,
        "bill": receipt
    }

@router.post("/feedback")
def submit_feedback(
    feedback: FeedbackRequest, 
    current_user: User = Depends(get_current_user)
):
    vector_db.save_feedback(
        current_user.id, 
        feedback.original_topic, 
        feedback.feedback_text, 
        feedback.sentiment
    )
    return {"status": "Feedback recorded"}


@router.get("/profile/{user_id}")
def get_profile(
    user_id: int, 
    current_user: User = Depends(get_current_user)
):
    # Security Check: Prevent User 1 from seeing User 2's data
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this profile")

    memories = vector_db.fetch_memories(user_id)
    return {"memories": memories}