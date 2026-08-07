"""Edu API endpoints — classes, assignments, grade export."""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

import edu
from routes.auth import _get_user

router = APIRouter(prefix="/api/edu", tags=["edu"])


class CreateClassRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    university: str = Field(..., min_length=2, max_length=200)


class JoinClassRequest(BaseModel):
    invite_code: str


class CreateAssignmentRequest(BaseModel):
    class_id: str
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., max_length=2000)
    test_cases: list[dict] = Field(default_factory=list)
    mode: str = Field(default="battle")


class SubmitAssignmentRequest(BaseModel):
    assignment_id: str
    battle_id: str
    score: float = 0


# ── Classes ──────────────────────────────────────────────────────

@router.post("/classes")
async def create_class(req: CreateClassRequest, request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    cls = edu.create_class(user["id"], req.name, req.university)
    return cls


@router.post("/classes/join")
async def join_class(req: JoinClassRequest, request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    cls = edu.join_class(user["id"], req.invite_code)
    if not cls:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    return cls


@router.get("/classes/professor")
async def professor_classes(request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return edu.get_professor_classes(user["id"])


@router.get("/classes/student")
async def student_classes(request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return edu.get_student_classes(user["id"])


@router.get("/classes/{class_id}/students")
async def class_students(class_id: str, request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return edu.get_class_students(class_id)


# ── Assignments ───────────────────────────────────────────────────

@router.post("/assignments")
async def create_assignment(req: CreateAssignmentRequest, request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return edu.create_assignment(req.class_id, req.title, req.description, req.test_cases, req.mode)


@router.get("/classes/{class_id}/assignments")
async def class_assignments(class_id: str, request: Request):
    return edu.get_class_assignments(class_id)


@router.post("/assignments/submit")
async def submit_assignment(req: SubmitAssignmentRequest, request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return edu.submit_assignment(req.assignment_id, user["id"], req.battle_id, req.score)


@router.get("/assignments/{assignment_id}/leaderboard")
async def assignment_leaderboard(assignment_id: str):
    return edu.get_assignment_leaderboard(assignment_id)


# ── Grade export ──────────────────────────────────────────────────

@router.get("/classes/{class_id}/grades.csv")
async def export_grades(class_id: str, request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    csv_data = edu.export_grades_csv(class_id)
    return PlainTextResponse(csv_data, media_type="text/csv", headers={
        "Content-Disposition": f"attachment; filename=grades-{class_id}.csv"
    })
