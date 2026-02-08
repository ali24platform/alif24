"""
Coin Service - Business logic for Coin system
1000 coin = 1000 UZS
Coins can be earned through lessons, games, quizzes, and olympiads.
Coins can be converted to real money or redeemed for prizes.
"""
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.errors import BadRequestError, NotFoundError, ForbiddenError
from app.models import (
    StudentProfile, ParentProfile,
    StudentCoin, CoinTransaction, CoinWithdrawal, Prize, PrizeRedemption,
    TransactionType, WithdrawalStatus, PrizeCategory
)


class CoinService:
    """Service for coin operations"""
    
    COIN_TO_UZS_RATE = 1  # 1 coin = 1 so'm
    MIN_WITHDRAWAL = 1000  # Minimal yechib olish
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============================================================
    # COIN BALANCE
    # ============================================================
    
    def get_balance(self, student_id: UUID) -> Dict:
        """Get student's coin balance."""
        coin_balance = self._get_or_create_balance(student_id)
        
        return {
            "current_balance": coin_balance.current_balance,
            "total_earned": coin_balance.total_earned,
            "total_spent": coin_balance.total_spent,
            "total_withdrawn": coin_balance.total_withdrawn,
            "money_equivalent_uzs": coin_balance.current_balance * self.COIN_TO_UZS_RATE
        }
    
    def get_transactions(self, student_id: UUID, limit: int = 50) -> List[Dict]:
        """Get transaction history."""
        coin_balance = self._get_or_create_balance(student_id)
        
        transactions = self.db.query(CoinTransaction).filter(
            CoinTransaction.student_coin_id == coin_balance.id
        ).order_by(CoinTransaction.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": str(t.id),
                "type": t.type.value,
                "amount": t.amount,
                "description": t.description,
                "created_at": t.created_at.isoformat()
            }
            for t in transactions
        ]
    
    # ============================================================
    # EARN COINS
    # ============================================================
    
    def add_coins_for_lesson(self, student_id: UUID, lesson_id: UUID) -> Dict:
        """Award coins for completing a lesson. +10 coins."""
        return self._add_coins(
            student_id, 
            10, 
            TransactionType.lesson_complete,
            f"Darsni tugatish uchun",
            lesson_id, 
            "lesson"
        )
    
    def add_coins_for_game(self, student_id: UUID, game_id: UUID, is_win: bool) -> Dict:
        """Award coins for playing a game. +5 coins for win."""
        if not is_win:
            return {"coins_earned": 0, "message": "O'yin tugadi"}
        
        return self._add_coins(
            student_id, 
            5, 
            TransactionType.game_win,
            f"O'yinni yutish uchun",
            game_id, 
            "game"
        )
    
    def add_coins_for_quiz(self, student_id: UUID, correct_count: int) -> Dict:
        """Award coins for quiz. +2 coins per correct answer."""
        amount = correct_count * 2
        if amount == 0:
            return {"coins_earned": 0, "message": "To'g'ri javob yo'q"}
        
        return self._add_coins(
            student_id, 
            amount, 
            TransactionType.quiz_correct,
            f"{correct_count} ta to'g'ri javob uchun"
        )
    
    def add_daily_bonus(self, student_id: UUID) -> Dict:
        """Award daily login bonus. +5 coins."""
        # Check if already received today
        coin_balance = self._get_or_create_balance(student_id)
        today = datetime.utcnow().date()
        
        existing = self.db.query(CoinTransaction).filter(
            and_(
                CoinTransaction.student_coin_id == coin_balance.id,
                CoinTransaction.type == TransactionType.daily_bonus,
                CoinTransaction.created_at >= datetime.combine(today, datetime.min.time())
            )
        ).first()
        
        if existing:
            return {"coins_earned": 0, "message": "Bugun bonus allaqachon olingan"}
        
        return self._add_coins(
            student_id, 
            5, 
            TransactionType.daily_bonus,
            "Kunlik bonus"
        )
    
    # ============================================================
    # WITHDRAWAL (COIN TO MONEY)
    # ============================================================
    
    def request_withdrawal(
        self,
        student_id: UUID,
        parent_id: UUID,
        coin_amount: int,
        payment_method: str,
        payment_details: str
    ) -> Dict:
        """
        Request coin withdrawal to real money.
        1000 coin = 1000 UZS
        """
        if coin_amount < self.MIN_WITHDRAWAL:
            raise BadRequestError(f"Minimal yechib olish: {self.MIN_WITHDRAWAL} coin")
        
        coin_balance = self._get_or_create_balance(student_id)
        
        if coin_balance.current_balance < coin_amount:
            raise BadRequestError("Yetarli coin mavjud emas")
        
        # Calculate money
        money_amount = coin_amount * self.COIN_TO_UZS_RATE
        
        # Create withdrawal request
        withdrawal = CoinWithdrawal(
            student_coin_id=coin_balance.id,
            coin_amount=coin_amount,
            money_amount=money_amount,
            parent_id=parent_id,
            payment_method=payment_method,
            payment_details=payment_details,
            status=WithdrawalStatus.pending
        )
        
        # Deduct coins
        coin_balance.current_balance -= coin_amount
        coin_balance.total_withdrawn += coin_amount
        
        # Record transaction
        transaction = CoinTransaction(
            student_coin_id=coin_balance.id,
            type=TransactionType.withdrawal,
            amount=-coin_amount,
            description=f"Pul yechib olish so'rovi: {money_amount} so'm"
        )
        
        self.db.add(withdrawal)
        self.db.add(transaction)
        self.db.commit()
        
        return {
            "message": "Yechib olish so'rovi yaratildi",
            "withdrawal_id": str(withdrawal.id),
            "coin_amount": coin_amount,
            "money_amount_uzs": money_amount,
            "status": "pending"
        }
    
    def get_withdrawal_history(self, student_id: UUID) -> List[Dict]:
        """Get withdrawal history for student."""
        coin_balance = self._get_or_create_balance(student_id)
        
        withdrawals = self.db.query(CoinWithdrawal).filter(
            CoinWithdrawal.student_coin_id == coin_balance.id
        ).order_by(CoinWithdrawal.created_at.desc()).all()
        
        return [
            {
                "id": str(w.id),
                "coin_amount": w.coin_amount,
                "money_amount_uzs": w.money_amount,
                "status": w.status.value,
                "payment_method": w.payment_method,
                "created_at": w.created_at.isoformat(),
                "processed_at": w.processed_at.isoformat() if w.processed_at else None
            }
            for w in withdrawals
        ]
    
    # ============================================================
    # PRIZE REDEMPTION
    # ============================================================
    
    def get_prizes(self, active_only: bool = True) -> List[Dict]:
        """Get available prizes."""
        query = self.db.query(Prize)
        if active_only:
            query = query.filter(Prize.is_active == True, Prize.stock_quantity > 0)
        
        prizes = query.order_by(Prize.coin_price).all()
        
        return [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "category": p.category.value,
                "image_url": p.image_url,
                "coin_price": p.coin_price,
                "stock_quantity": p.stock_quantity,
                "is_digital": p.is_digital
            }
            for p in prizes
        ]
    
    def redeem_prize(
        self,
        student_id: UUID,
        prize_id: UUID,
        delivery_address: Optional[str] = None
    ) -> Dict:
        """Redeem a prize with coins."""
        coin_balance = self._get_or_create_balance(student_id)
        
        prize = self.db.query(Prize).filter(Prize.id == prize_id).first()
        if not prize:
            raise NotFoundError("Yutiq topilmadi")
        
        if not prize.is_active:
            raise BadRequestError("Bu yutiq hozir mavjud emas")
        
        if prize.stock_quantity <= 0:
            raise BadRequestError("Bu yutiq tugagan")
        
        if coin_balance.current_balance < prize.coin_price:
            raise BadRequestError("Yetarli coin mavjud emas")
        
        # Check delivery address for physical prizes
        if not prize.is_digital and not delivery_address:
            raise BadRequestError("Jismoniy yutuqlar uchun manzil kerak")
        
        # Deduct coins
        coin_balance.current_balance -= prize.coin_price
        coin_balance.total_spent += prize.coin_price
        
        # Reduce stock
        prize.stock_quantity -= 1
        
        # Create redemption
        redemption = PrizeRedemption(
            student_coin_id=coin_balance.id,
            prize_id=prize_id,
            coin_spent=prize.coin_price,
            delivery_address=delivery_address
        )
        
        # Record transaction
        transaction = CoinTransaction(
            student_coin_id=coin_balance.id,
            type=TransactionType.prize_redemption,
            amount=-prize.coin_price,
            description=f"Yutiq: {prize.name}",
            reference_id=prize_id,
            reference_type="prize"
        )
        
        self.db.add(redemption)
        self.db.add(transaction)
        self.db.commit()
        
        return {
            "message": "Yutiq muvaffaqiyatli sotib olindi!",
            "prize_name": prize.name,
            "coins_spent": prize.coin_price,
            "is_digital": prize.is_digital,
            "remaining_balance": coin_balance.current_balance
        }
    
    def get_redemption_history(self, student_id: UUID) -> List[Dict]:
        """Get prize redemption history."""
        coin_balance = self._get_or_create_balance(student_id)
        
        redemptions = self.db.query(PrizeRedemption).filter(
            PrizeRedemption.student_coin_id == coin_balance.id
        ).order_by(PrizeRedemption.created_at.desc()).all()
        
        return [
            {
                "id": str(r.id),
                "prize_name": r.prize.name,
                "coin_spent": r.coin_spent,
                "delivery_status": r.delivery_status,
                "created_at": r.created_at.isoformat()
            }
            for r in redemptions
        ]
    
    # ============================================================
    # ADMIN FUNCTIONS
    # ============================================================
    
    def process_withdrawal(
        self,
        admin_user_id: UUID,
        withdrawal_id: UUID,
        approve: bool,
        rejection_reason: Optional[str] = None
    ) -> Dict:
        """Process withdrawal request (admin only)."""
        withdrawal = self.db.query(CoinWithdrawal).filter(
            CoinWithdrawal.id == withdrawal_id
        ).first()
        
        if not withdrawal:
            raise NotFoundError("So'rov topilmadi")
        
        if withdrawal.status != WithdrawalStatus.pending:
            raise BadRequestError("Bu so'rov allaqachon ko'rib chiqilgan")
        
        if approve:
            withdrawal.status = WithdrawalStatus.completed
        else:
            withdrawal.status = WithdrawalStatus.rejected
            withdrawal.rejection_reason = rejection_reason
            
            # Refund coins
            coin_balance = withdrawal.student_coin
            coin_balance.current_balance += withdrawal.coin_amount
            coin_balance.total_withdrawn -= withdrawal.coin_amount
            
            # Record refund transaction
            transaction = CoinTransaction(
                student_coin_id=coin_balance.id,
                type=TransactionType.admin_adjustment,
                amount=withdrawal.coin_amount,
                description=f"Yechib olish rad etildi: {rejection_reason}"
            )
            self.db.add(transaction)
        
        withdrawal.processed_by = admin_user_id
        withdrawal.processed_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "message": "Tasdiqlandi" if approve else "Rad etildi",
            "status": withdrawal.status.value
        }
    
    def create_prize(
        self,
        admin_user_id: UUID,
        name: str,
        description: str,
        category: PrizeCategory,
        coin_price: int,
        stock_quantity: int,
        image_url: Optional[str] = None,
        is_digital: bool = False
    ) -> Dict:
        """Create a new prize (admin only)."""
        prize = Prize(
            name=name,
            description=description,
            category=category,
            coin_price=coin_price,
            stock_quantity=stock_quantity,
            image_url=image_url,
            is_digital=is_digital
        )
        
        self.db.add(prize)
        self.db.commit()
        
        return {
            "message": "Yutiq yaratildi",
            "prize_id": str(prize.id),
            "name": prize.name
        }
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def _get_or_create_balance(self, student_id: UUID) -> StudentCoin:
        """Get or create coin balance for student."""
        # First find the student profile
        student_profile = self.db.query(StudentProfile).filter(
            StudentProfile.user_id == student_id
        ).first()
        
        if not student_profile:
            raise NotFoundError("O'quvchi profili topilmadi")
        
        coin_balance = self.db.query(StudentCoin).filter(
            StudentCoin.student_id == student_profile.id
        ).first()
        
        if not coin_balance:
            coin_balance = StudentCoin(student_id=student_profile.id)
            self.db.add(coin_balance)
            self.db.commit()
            self.db.refresh(coin_balance)
        
        return coin_balance
    
    def _add_coins(
        self,
        student_id: UUID,
        amount: int,
        transaction_type: TransactionType,
        description: str,
        reference_id: Optional[UUID] = None,
        reference_type: Optional[str] = None
    ) -> Dict:
        """Add coins and record transaction."""
        coin_balance = self._get_or_create_balance(student_id)
        
        coin_balance.total_earned += amount
        coin_balance.current_balance += amount
        
        transaction = CoinTransaction(
            student_coin_id=coin_balance.id,
            type=transaction_type,
            amount=amount,
            description=description,
            reference_id=reference_id,
            reference_type=reference_type
        )
        
        self.db.add(transaction)
        self.db.commit()
        
        return {
            "coins_earned": amount,
            "new_balance": coin_balance.current_balance,
            "message": f"+{amount} coin qo'shildi!"
        }
