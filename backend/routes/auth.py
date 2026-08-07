"""Auth endpoints — register, login, guest, wallet."""
from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel, Field

import auth as auth_mod

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str = Field(..., max_length=200)
    username: str = Field(..., min_length=2, max_length=30)
    password: str = Field(..., min_length=6, max_length=100)


class LoginRequest(BaseModel):
    email: str
    password: str


class DepositRequest(BaseModel):
    amount_cents: int = Field(..., ge=100, le=1000000)  # $1 to $10,000


def _get_user(request: Request) -> dict | None:
    """Extract user from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    return auth_mod.get_user_from_token(token)


@router.post("/register")
async def register(req: RegisterRequest):
    user = auth_mod.register_user(req.email, req.username, req.password)
    if not user:
        raise HTTPException(status_code=409, detail="Email or username already taken")
    token = auth_mod.create_token(user["id"])
    return {"user": _public_user(user), "token": token}


@router.post("/login")
async def login(req: LoginRequest):
    user, token = auth_mod.login_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"user": _public_user(user), "token": token}


@router.get("/guest")
async def guest_login():
    token = auth_mod.create_guest_token()
    user = auth_mod.get_user_from_token(token)
    return {"user": _public_user(user), "token": token}


@router.get("/me")
async def me(request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _public_user(user)


@router.get("/balance")
async def balance(request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "balance_cents": user["balance_cents"],
        "balance_display": f"${user['balance_cents'] / 100:.2f}",
    }


@router.get("/transactions")
async def transactions(request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    txns = auth_mod.get_user_transactions(user["id"])
    return [{
        "id": t["id"],
        "type": t["type"],
        "amount_cents": t["amount_cents"],
        "amount_display": f"${abs(t['amount_cents']) / 100:.2f}",
        "description": t["description"],
        "created_at": t["created_at"],
    } for t in txns]


@router.post("/deposit")
async def deposit(req: DepositRequest, request: Request):
    """Simulated deposit (no Stripe for dev). Adds funds directly."""
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    new_balance = auth_mod.add_balance(
        user["id"], req.amount_cents,
        f"Deposit ${req.amount_cents / 100:.2f}",
    )
    return {"balance_cents": new_balance, "balance_display": f"${new_balance / 100:.2f}"}


def _public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "username": user["username"],
        "is_guest": bool(user["is_guest"]),
        "balance_cents": user["balance_cents"],
        "balance_display": f"${user['balance_cents'] / 100:.2f}",
        "created_at": user["created_at"],
    }
