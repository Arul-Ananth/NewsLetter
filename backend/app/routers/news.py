from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database import get_session
from app.dependencies import get_current_user
from app.models.sql import User
from app.models.schemas import NewsRequest, NewsResponse, FeedbackRequest
from app.services import billing, crew_agent, vector_db
from app.models.sql import User
from app.dependencies import get_current_user

router = APIRouter(tags=["News"])

@router.post("/generate", response_model=NewsResponse)
def generate_news(
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
        crew_result = crew_agent.run_newsletter_crew(request.topic, context, api_keys=api_keys)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # 4. CALCULATE TOKENS & DEDUCT FUNDS
    usage = crew_result.token_usage
    input_tok = usage.prompt_tokens
    output_tok = usage.completion_tokens
    
    receipt = billing.process_transaction(
        session, current_user.id, request.topic, input_tok, output_tok
    )
    
    return {
        "topic": request.topic,
        "content": str(crew_result.raw),
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