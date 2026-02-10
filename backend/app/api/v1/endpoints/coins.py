"""
Coin API Endpoints
Routes for coin balance, earning, withdrawal, and prizes.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models import User, UserRole, PrizeCategory
from app.services.coin_service import CoinService


router = APIRouter(prefix="/coins", tags=["Coins"])


# ============================================================
# SCHEMAS
# ============================================================

class WithdrawalRequest(BaseModel):
    coin_amount: int = Field(..., ge=1000, description="Minimal 1000 coin")
    payment_method: str = Field(..., description="click, payme, uzum, bank_card")
    payment_details: str = Field(..., description="Telefon raqami yoki karta raqami")


class RedeemPrizeRequest(BaseModel):
    prize_id: UUID
    delivery_address: Optional[str] = None


class ProcessWithdrawalRequest(BaseModel):
    approve: bool
    rejection_reason: Optional[str] = None


class CreatePrizeRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    category: PrizeCategory = PrizeCategory.other
    coin_price: int = Field(..., ge=10)
    stock_quantity: int = Field(default=100, ge=0)
    image_url: Optional[str] = None
    is_digital: bool = False


class CoinBalanceResponse(BaseModel):
    current_balance: int
    total_earned: int
    total_spent: int
    total_withdrawn: int
    money_equivalent_uzs: int


# ============================================================
# STUDENT ENDPOINTS
# ============================================================

@router.get("/balance", response_model=CoinBalanceResponse, summary="Get Coin Balance")
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get student's coin balance."""
    service = CoinService(db)
    return service.get_balance(current_user.id)


@router.get("/transactions", summary="Get Transaction History")
async def get_transactions(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get coin transaction history."""
    service = CoinService(db)
    return service.get_transactions(current_user.id, limit)


@router.post("/daily-bonus", summary="Claim Daily Bonus")
async def claim_daily_bonus(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Claim daily login bonus (+5 coins)."""
    service = CoinService(db)
    return service.add_daily_bonus(current_user.id)


class GameRewardRequest(BaseModel):
    game_type: str = Field(..., description="math_monster, letter_memory, harf, etc.")
    is_win: bool = Field(default=True)
    score: int = Field(default=0, ge=0)


@router.post("/game-reward", summary="Award Coins for Game")
async def award_game_coins(
    request: GameRewardRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Award coins after a game is completed.
    +5 coins for win, 0 for loss.
    """
    service = CoinService(db)
    import uuid
    game_id = uuid.uuid4()
    return service.add_coins_for_game(current_user.id, game_id, request.is_win)


# ============================================================
# WITHDRAWAL ENDPOINTS
# ============================================================

@router.post("/withdraw", summary="Request Withdrawal")
async def request_withdrawal(
    request: WithdrawalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request coin withdrawal to real money.
    1000 coin = 1000 UZS
    Parents will receive the payment.
    """
    # Get parent ID from student profile
    from app.models import StudentProfile
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    
    if not student_profile or not student_profile.parent_id:
        raise HTTPException(status_code=400, detail="Ota-ona bog'lanmagan")
    
    service = CoinService(db)
    return service.request_withdrawal(
        student_id=current_user.id,
        parent_id=student_profile.parent_id,
        coin_amount=request.coin_amount,
        payment_method=request.payment_method,
        payment_details=request.payment_details
    )


@router.get("/withdrawals", summary="Get Withdrawal History")
async def get_withdrawal_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get withdrawal request history."""
    service = CoinService(db)
    return service.get_withdrawal_history(current_user.id)


# ============================================================
# PRIZE ENDPOINTS
# ============================================================

@router.get("/prizes", summary="Get Available Prizes")
async def get_prizes(db: Session = Depends(get_db)):
    """Get list of available prizes."""
    service = CoinService(db)
    return service.get_prizes()


@router.post("/prizes/redeem", summary="Redeem Prize")
async def redeem_prize(
    request: RedeemPrizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Redeem a prize with coins."""
    service = CoinService(db)
    return service.redeem_prize(
        student_id=current_user.id,
        prize_id=request.prize_id,
        delivery_address=request.delivery_address
    )


@router.get("/prizes/history", summary="Get Redemption History")
async def get_redemption_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get prize redemption history."""
    service = CoinService(db)
    return service.get_redemption_history(current_user.id)


# ============================================================
# ADMIN ENDPOINTS
# ============================================================

@router.post("/admin/process-withdrawal/{withdrawal_id}", summary="Process Withdrawal (Admin)")
async def process_withdrawal(
    withdrawal_id: UUID,
    request: ProcessWithdrawalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process a withdrawal request (approve or reject)."""
    if current_user.role != UserRole.moderator:
        raise HTTPException(status_code=403, detail="Faqat moderatorlar uchun")
    
    service = CoinService(db)
    return service.process_withdrawal(
        admin_user_id=current_user.id,
        withdrawal_id=withdrawal_id,
        approve=request.approve,
        rejection_reason=request.rejection_reason
    )


@router.post("/admin/prizes", summary="Create Prize (Admin)")
async def create_prize(
    request: CreatePrizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new prize."""
    if current_user.role != UserRole.moderator:
        raise HTTPException(status_code=403, detail="Faqat moderatorlar uchun")
    
    service = CoinService(db)
    return service.create_prize(
        admin_user_id=current_user.id,
        name=request.name,
        description=request.description,
        category=request.category,
        coin_price=request.coin_price,
        stock_quantity=request.stock_quantity,
        image_url=request.image_url,
        is_digital=request.is_digital
    )
