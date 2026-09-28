from pathlib import Path

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import HTTPException
from fastapi import Request
from fastapi import status

from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from fastapi.templating import Jinja2Templates

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import get_db
from .gemini_service import gemini_service
from .models import User
from .schemas import FeedbackRequest
from .schemas import UserInput


BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(
        BASE_DIR / "templates"
    )
)


router = APIRouter()


def user_context(
    user: User,
    plan: str | None = None,
) -> dict:

    return {

        "username": user.username,

        "user_id": user.user_id,

        "age": user.age,

        "weight": user.weight,

        "goal": user.goal,

        "intensity": user.intensity,

        "workout_plan":
            plan
            or user.updated_plan
            or user.original_plan,

        "original_plan":
            user.original_plan,

        "nutrition_tip":
            user.nutrition_tip,

        "feedback":
            user.last_feedback
            or "",
    }


# ============================================================
# HOME
# ============================================================

@router.get(
    "/",
    response_class=HTMLResponse,
)
def home(
    request: Request,
):

    return templates.TemplateResponse(

        request=request,

        name="index.html",

        context={
            "app_name": "FitBuddy",
            "error": None,
        },
    )


# ============================================================
# GENERATE WORKOUT
# ============================================================

@router.post(
    "/generate-workout",
    response_class=HTMLResponse,
)
def generate_workout(

    request: Request,

    username: str = Form(...),

    user_id: str = Form(...),

    age: int = Form(...),

    weight: float = Form(...),

    goal: str = Form(...),

    intensity: str = Form(...),

    db: Session = Depends(get_db),
):

    try:

        user_input = UserInput(

            username=username,

            user_id=user_id,

            age=age,

            weight=weight,

            goal=goal,

            intensity=intensity.lower(),
        )

    except Exception as exc:

        return templates.TemplateResponse(

            request=request,

            name="index.html",

            context={
                "app_name": "FitBuddy",
                "error": str(exc),
            },

            status_code=422,
        )

    # Check if user already exists.
    existing_user = db.scalar(

        select(User).where(
            User.user_id
            == user_input.user_id
        )
    )

    # Generate workout.
    plan = gemini_service.generate_workout(

        username=user_input.username,

        age=user_input.age,

        weight=user_input.weight,

        goal=user_input.goal,

        intensity=user_input.intensity,
    )

    # Generate nutrition tip.
    nutrition_tip = (
        gemini_service.generate_nutrition_tip(
            user_input.goal
        )
    )

    if existing_user:

        existing_user.username = (
            user_input.username
        )

        existing_user.age = (
            user_input.age
        )

        existing_user.weight = (
            user_input.weight
        )

        existing_user.goal = (
            user_input.goal
        )

        existing_user.intensity = (
            user_input.intensity
        )

        existing_user.original_plan = plan

        existing_user.updated_plan = None

        existing_user.nutrition_tip = (
            nutrition_tip
        )

        existing_user.last_feedback = None

        user = existing_user

    else:

        user = User(

            user_id=user_input.user_id,

            username=user_input.username,

            age=user_input.age,

            weight=user_input.weight,

            goal=user_input.goal,

            intensity=user_input.intensity,

            original_plan=plan,

            nutrition_tip=nutrition_tip,
        )

        db.add(user)

    db.commit()

    db.refresh(user)

    return templates.TemplateResponse(

        request=request,

        name="result.html",

        context=user_context(user),
    )


# ============================================================
# SUBMIT FEEDBACK
# ============================================================

@router.post(
    "/submit-feedback",
    response_class=HTMLResponse,
)
def submit_feedback(

    request: Request,

    user_id: str = Form(...),

    feedback: str = Form(...),

    db: Session = Depends(get_db),
):

    try:

        feedback_request = FeedbackRequest(

            user_id=user_id,

            feedback=feedback,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    user = db.scalar(

        select(User).where(
            User.user_id
            == feedback_request.user_id
        )
    )

    if not user:

        raise HTTPException(

            status_code=404,

            detail="User not found.",
        )

    # Use the latest plan as the starting point.
    base_plan = (
        user.updated_plan
        or user.original_plan
    )

    updated_plan = (
        gemini_service.update_workout_plan(

            original_plan=base_plan,

            feedback=feedback_request.feedback,

            goal=user.goal,

            intensity=user.intensity,
        )
    )

    user.updated_plan = updated_plan

    user.last_feedback = (
        feedback_request.feedback
    )

    user.nutrition_tip = (
        gemini_service.generate_nutrition_tip(
            user.goal
        )
    )

    db.commit()

    db.refresh(user)

    return templates.TemplateResponse(

        request=request,

        name="result.html",

        context=user_context(
            user,
            plan=updated_plan,
        ),
    )


# ============================================================
# ADMIN VIEW
# ============================================================

@router.get(
    "/view-all-users",
    response_class=HTMLResponse,
)
def view_all_users(

    request: Request,

    db: Session = Depends(get_db),
):

    users = db.scalars(

        select(User).order_by(
            User.created_at.desc()
        )
    ).all()

    return templates.TemplateResponse(

        request=request,

        name="all_users.html",

        context={
            "users": users,
            "app_name": "FitBuddy",
        },
    )


# ============================================================
# DELETE USER
# ============================================================

@router.post(
    "/delete-user/{user_id}"
)
def delete_user(

    user_id: str,

    db: Session = Depends(get_db),
):

    user = db.scalar(

        select(User).where(
            User.user_id == user_id
        )
    )

    if user:

        db.delete(user)

        db.commit()

    return RedirectResponse(

        url="/view-all-users",

        status_code=status.HTTP_303_SEE_OTHER,
    )


# ============================================================
# API HEALTH
# ============================================================

@router.get("/api/health")
def health():

    return {

        "status": "ok",

        "application": "FitBuddy",

        "gemini_configured":
            gemini_service.is_configured,
    }


# ============================================================
# API GENERATE WORKOUT
# ============================================================

@router.post(
    "/api/generate-workout"
)
def api_generate_workout(

    payload: UserInput,

    db: Session = Depends(get_db),
):

    plan = gemini_service.generate_workout(

        username=payload.username,

        age=payload.age,

        weight=payload.weight,

        goal=payload.goal,

        intensity=payload.intensity,
    )

    nutrition_tip = (
        gemini_service.generate_nutrition_tip(
            payload.goal
        )
    )

    user = db.scalar(

        select(User).where(
            User.user_id
            == payload.user_id
        )
    )

    if user:

        user.username = payload.username

        user.age = payload.age

        user.weight = payload.weight

        user.goal = payload.goal

        user.intensity = payload.intensity

        user.original_plan = plan

        user.updated_plan = None

        user.nutrition_tip = nutrition_tip

        user.last_feedback = None

    else:

        user = User(

            user_id=payload.user_id,

            username=payload.username,

            age=payload.age,

            weight=payload.weight,

            goal=payload.goal,

            intensity=payload.intensity,

            original_plan=plan,

            nutrition_tip=nutrition_tip,
        )

        db.add(user)

    try:

        db.commit()

        db.refresh(user)

    except IntegrityError as exc:

        db.rollback()

        raise HTTPException(

            status_code=409,

            detail="Could not save user.",
        ) from exc

    return {

        "message":
            "Workout plan generated successfully.",

        "user_id":
            user.user_id,

        "username":
            user.username,

        "goal":
            user.goal,

        "intensity":
            user.intensity,

        "workout_plan":
            plan,

        "nutrition_tip":
            nutrition_tip,
    }


# ============================================================
# API SUBMIT FEEDBACK
# ============================================================

@router.post(
    "/api/submit-feedback"
)
def api_submit_feedback(

    payload: FeedbackRequest,

    db: Session = Depends(get_db),
):

    user = db.scalar(

        select(User).where(
            User.user_id
            == payload.user_id
        )
    )

    if not user:

        raise HTTPException(

            status_code=404,

            detail="User not found.",
        )

    base_plan = (
        user.updated_plan
        or user.original_plan
    )

    updated_plan = (
        gemini_service.update_workout_plan(

            original_plan=base_plan,

            feedback=payload.feedback,

            goal=user.goal,

            intensity=user.intensity,
        )
    )

    user.updated_plan = updated_plan

    user.last_feedback = payload.feedback

    user.nutrition_tip = (
        gemini_service.generate_nutrition_tip(
            user.goal
        )
    )

    db.commit()

    db.refresh(user)

    return {

        "message":
            "Workout plan updated successfully.",

        "user_id":
            user.user_id,

        "feedback":
            payload.feedback,

        "updated_plan":
            updated_plan,

        "nutrition_tip":
            user.nutrition_tip,
    }


# ============================================================
# API ALL USERS
# ============================================================

@router.get("/api/users")
def api_users(
    db: Session = Depends(get_db),
):

    users = db.scalars(

        select(User).order_by(
            User.created_at.desc()
        )
    ).all()

    return [

        {

            "user_id":
                user.user_id,

            "username":
                user.username,

            "age":
                user.age,

            "weight":
                user.weight,

            "goal":
                user.goal,

            "intensity":
                user.intensity,

            "has_updated_plan":
                bool(user.updated_plan),

            "created_at":
                user.created_at.isoformat(),

            "updated_at":
                user.updated_at.isoformat(),
        }

        for user in users
    ]


# ============================================================
# API SINGLE USER
# ============================================================

@router.get(
    "/api/users/{user_id}"
)
def api_user(

    user_id: str,

    db: Session = Depends(get_db),
):

    user = db.scalar(

        select(User).where(
            User.user_id == user_id
        )
    )

    if not user:

        raise HTTPException(

            status_code=404,

            detail="User not found.",
        )

    return {

        "user_id":
            user.user_id,

        "username":
            user.username,

        "age":
            user.age,

        "weight":
            user.weight,

        "goal":
            user.goal,

        "intensity":
            user.intensity,

        "original_plan":
            user.original_plan,

        "updated_plan":
            user.updated_plan,

        "nutrition_tip":
            user.nutrition_tip,

        "last_feedback":
            user.last_feedback,

        "created_at":
            user.created_at.isoformat(),

        "updated_at":
            user.updated_at.isoformat(),
    }