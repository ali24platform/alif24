"""
Telegram Bot Service for Alif24 Platform

Full-featured Telegram bot with:
- Phone verification via OTP
- User notifications
- Commands: /start, /help, /myprofile, /mystats
- Webhook support
"""

import httpx
import logging
import asyncio
import secrets
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.phone_verification import PhoneVerification, TelegramUser
from app.models.rbac_models import User, StudentProfile

logger = logging.getLogger(__name__)


class TelegramBotService:
    """
    Telegram Bot Service
    Handles all Telegram bot interactions
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"

    async def _make_request(self, method: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make request to Telegram API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/{method}",
                    json=data or {}
                )
                result = response.json()
                
                if not result.get("ok"):
                    logger.error(f"Telegram API error: {result}")
                    
                return result
        except Exception as e:
            logger.error(f"Telegram request failed: {e}")
            return {"ok": False, "error": str(e)}

    # ============================================================
    # VERIFICATION METHODS
    # ============================================================
    
    async def send_verification_code(self, phone: str, lang: str = "uz") -> Dict[str, Any]:
        """Send verification code to user via Telegram"""
        try:
            # Multi-language messages
            messages = {
                "uz": {
                    "not_linked": "Ushbu telefon raqam Telegram botga ulanmagan. Iltimos, avval @Alif24Bot ga /start yozing.",
                    "code_sent": "Tasdiqlash kodi Telegram orqali yuborildi",
                    "send_error": "Telegram orqali xabar yuborishda xatolik",
                    "code_title": "🔐 *Tasdiqlash kodi*",
                    "your_code": "Sizning tasdiqlash kodingiz",
                    "expires": "Kod 5 daqiqa ichida amal qiladi",
                    "warning": "Bu kodni hech kimga bermang!"
                },
                "ru": {
                    "not_linked": "Этот номер телефона не привязан к Telegram боту. Пожалуйста, сначала напишите @Alif24Bot /start.",
                    "code_sent": "Код подтверждения отправлен через Telegram",
                    "send_error": "Ошибка отправки сообщения через Telegram",
                    "code_title": "🔐 *Код подтверждения*",
                    "your_code": "Ваш код подтверждения",
                    "expires": "Код действителен 5 минут",
                    "warning": "Никому не сообщайте этот код!"
                },
                "en": {
                    "not_linked": "This phone number is not linked to the Telegram bot. Please start @Alif24Bot with /start first.",
                    "code_sent": "Verification code sent via Telegram",
                    "send_error": "Error sending message via Telegram",
                    "code_title": "🔐 *Verification Code*",
                    "your_code": "Your verification code",
                    "expires": "Code expires in 5 minutes",
                    "warning": "Do not share this code with anyone!"
                }
            }
            t = messages.get(lang, messages["uz"])
            
            # Find Telegram user by phone
            tg_user = self.db.query(TelegramUser).filter(
                TelegramUser.phone == phone
            ).first()
            
            if not tg_user:
                return {
                    "success": False,
                    "message": t["not_linked"]
                }
            
            # Create verification code
            verification = PhoneVerification.create_for_phone(phone, expires_minutes=5)
            self.db.add(verification)
            self.db.commit()
            
            # Send code via Telegram (fixed newline escaping)
            message = f"{t['code_title']}\n\n{t['your_code']}: `{verification.code}`\n\n⏱ {t['expires']}\n\n⚠️ {t['warning']}"

            result = await self._make_request("sendMessage", {
                "chat_id": tg_user.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            })
            
            if result.get("ok"):
                return {
                    "success": True,
                    "message": t["code_sent"],
                    "expires_in": 300
                }
            else:
                logger.error(f"Telegram API error: {result}")
                return {
                    "success": False,
                    "message": t["send_error"]
                }
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"CRITICAL ERROR in send_verification_code: {e}\n{error_trace}")
            return {
                "success": False,
                "message": "Server xatoligi: Iltimos keyinroq urinib ko'ring"
            }
    
    def verify_code(self, phone: str, code: str, lang: str = "uz") -> Dict[str, Any]:
        """Verify the code entered by user"""
        # Multi-language messages
        messages = {
            "uz": {
                "not_found": "Tasdiqlash kodi topilmadi. Yangi kod so'rang.",
                "expired": "Tasdiqlash kodi muddati tugagan. Yangi kod so'rang.",
                "too_many": "Juda ko'p noto'g'ri urinishlar. Yangi kod so'rang.",
                "success": "Telefon raqam muvaffaqiyatli tasdiqlandi!",
                "wrong_code": "Noto'g'ri kod. {remaining} ta urinish qoldi."
            },
            "ru": {
                "not_found": "Код подтверждения не найден. Запросите новый код.",
                "expired": "Срок действия кода истёк. Запросите новый код.",
                "too_many": "Слишком много неверных попыток. Запросите новый код.",
                "success": "Номер телефона успешно подтверждён!",
                "wrong_code": "Неверный код. Осталось попыток: {remaining}."
            },
            "en": {
                "not_found": "Verification code not found. Please request a new code.",
                "expired": "Verification code expired. Please request a new code.",
                "too_many": "Too many incorrect attempts. Please request a new code.",
                "success": "Phone number successfully verified!",
                "wrong_code": "Incorrect code. {remaining} attempts remaining."
            }
        }
        t = messages.get(lang, messages["uz"])
        
        # Find latest verification for this phone
        verification = self.db.query(PhoneVerification).filter(
            PhoneVerification.phone == phone,
            PhoneVerification.verified == False
        ).order_by(PhoneVerification.created_at.desc()).first()
        
        if not verification:
            return {
                "success": False,
                "message": t["not_found"]
            }
        
        if verification.is_expired():
            return {
                "success": False,
                "message": t["expired"]
            }
        
        if not verification.can_attempt():
            return {
                "success": False,
                "message": t["too_many"]
            }
        
        if verification.verify(code):
            self.db.commit()
            return {
                "success": True,
                "message": t["success"]
            }
        else:
            self.db.commit()
            remaining = verification.max_attempts - verification.attempts
            return {
                "success": False,
                "message": t["wrong_code"].format(remaining=remaining)
            }
        
    # ============================================================
    # KEYBOARD MARKUPS
    # ============================================================
    
    def get_contact_keyboard(self) -> Dict[str, Any]:
        """Get keyboard with 'Share Contact' button"""
        return {
            "keyboard": [
                [{"text": "📱 Telefon raqamni yuborish", "request_contact": True}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": True
        }
    
    def get_main_keyboard(self) -> Dict[str, Any]:
        """Get main menu keyboard"""
        return {
            "keyboard": [
                [{"text": "👤 Mening Profilim"}, {"text": "📊 Statistikam"}],
                [{"text": "🏆 Reyting"}, {"text": "📞 Yordam"}]
            ],
            "resize_keyboard": True
        }

    # ============================================================
    # BOT COMMANDS
    # ============================================================
    
    async def handle_start(self, chat_id: str, user_info: Dict[str, Any], args: str = None) -> None:
        """Handle /start command"""
        # Check if user already exists
        tg_user = self.db.query(TelegramUser).filter(
            TelegramUser.telegram_chat_id == str(chat_id)
        ).first()
        
        if not tg_user:
            tg_user = TelegramUser(
                telegram_chat_id=str(chat_id),
                telegram_username=user_info.get("username"),
                telegram_first_name=user_info.get("first_name"),
                telegram_last_name=user_info.get("last_name"),
                last_interaction_at=datetime.utcnow()
            )
            self.db.add(tg_user)
            self.db.commit()
        
        # Check if they have a phone linked
        if tg_user.phone:
            platform_user = self.db.query(User).filter(
                User.phone == tg_user.phone
            ).first()
            
            msg = "👋 Assalomu alaykum!"
            if platform_user:
                msg = f"👋 Xush kelibsiz, {platform_user.first_name}!"
            
            await self._make_request("sendMessage", {
                "chat_id": chat_id,
                "text": f"{msg}\n\nQuyidagi menyudan foydalanishingiz mumkin:",
                "reply_markup": self.get_main_keyboard()
            })
            return
        
        # Request contact
        await self._make_request("sendMessage", {
            "chat_id": chat_id,
            "text": """👋 Assalomu alaykum! Alif24 Botga xush kelibsiz!

🚀 To'liq imkoniyatlardan foydalanish uchun telefon raqamingizni tasdiqlashingiz kerak.

Iltimos, pastdagi **"📱 Telefon raqamni yuborish"** tugmasini bosing.""",
            "reply_markup": self.get_contact_keyboard(),
            "parse_mode": "Markdown"
        })

    async def handle_contact(self, chat_id: str, contact: Dict[str, Any]) -> None:
        """Handle incoming contact"""
        phone = contact.get("phone_number", "")
        if not phone:
            return
            
        # Format phone (remove + if exists, ensure 998 context)
        # Telegram usually sends with +, but sometimes without
        if not phone.startswith("+"):
            phone = "+" + phone
            
        # Update TG user
        tg_user = self.db.query(TelegramUser).filter(
            TelegramUser.telegram_chat_id == str(chat_id)
        ).first()
        
        if tg_user:
            # Check if this phone is already linked to another TG account
            existing = self.db.query(TelegramUser).filter(
                TelegramUser.phone == phone,
                TelegramUser.telegram_chat_id != str(chat_id)
            ).first()
            
            if existing:
                await self._make_request("sendMessage", {
                    "chat_id": chat_id,
                    "text": "❌ Bu telefon raqam boshqa Telegram akkauntga ulangan."
                })
                return

            tg_user.phone = phone
            
            # Try to link with platform user
            platform_user = self.db.query(User).filter(User.phone == phone).first()
            if platform_user:
                tg_user.user_id = platform_user.id
                msg = f"✅ Raqam tasdiqlandi!\nSizning platformadagi hisobingiz topildi: {platform_user.first_name} {platform_user.last_name}"
            else:
                msg = "✅ Raqam saqlandi!\nHozircha platformada bu raqam bilan ro'yxatdan o'tmagansiz."
            
            self.db.commit()
            
            await self._make_request("sendMessage", {
                "chat_id": chat_id,
                "text": msg,
                "reply_markup": self.get_main_keyboard()
            })

    async def handle_help(self, chat_id: str) -> str:
        """Handle /help command"""
        return """📖 *Alif24 Bot Yordam*

Botdan foydalanish uchun quyidagi bo'limlarni tanlang:

👤 *Mening Profilim* - Shaxsiy ma'lumotlar
📊 *Statistikam* - O'qish ko'rsatkichlari
🏆 *Reyting* - Liderlar jadvali
📞 *Yordam* - Admin bilan bog'lanish

Muammo bo'lsa: +998 90 123 45 67"""

    async def handle_myprofile(self, chat_id: str) -> str:
        """Handle /myprofile command"""
        tg_user = self.db.query(TelegramUser).filter(
            TelegramUser.telegram_chat_id == str(chat_id)
        ).first()
        
        if not tg_user or not tg_user.phone:
            return "❌ Telefon raqamingiz ulanmagan. /start buyrug'ini yuboring."
        
        user = self.db.query(User).filter(User.phone == tg_user.phone).first()
        
        if not user:
             return f"""👤 *Profil (Mehmon)*
             
📱 Telefon: {tg_user.phone}
⚠️ Platformada ro'yxatdan o'tmagansiz."""
        
        profile_text = f"""👤 *Sizning Profilingiz*

📛 *{user.first_name} {user.last_name}*
🎭 Rol: {user.role.value.capitalize()}
📱 {user.phone}
⭐️ Status: Aktiv
"""
        return profile_text

    async def handle_mystats(self, chat_id: str) -> str:
        """Handle /mystats command"""
        tg_user = self.db.query(TelegramUser).filter(
            TelegramUser.telegram_chat_id == str(chat_id)
        ).first()
        
        if not tg_user or not tg_user.user_id:
             return "📊 Statistika ko'rish uchun avval ro'yxatdan o'ting."
        
        # Get student profile if exists
        student = self.db.query(StudentProfile).filter(
            StudentProfile.user_id == tg_user.user_id
        ).first()
        
        if student:
            return f"""📊 *Statistika*

🏆 Daraja: {student.level}
💰 Tanga: {student.total_coins}
⭐ Ball: {student.total_points}
🔥 Streak: {student.current_streak} kun
📚 Darslar: {student.total_lessons_completed}
"""
        return "📊 Statistika topilmadi."

    async def handle_phone_registration(self, chat_id: str, phone: str) -> None:
        """Handle manual phone input"""
        # Call valid format logic reuse
        contact = {"phone_number": phone}
        await self.handle_contact(chat_id, contact)

    # ============================================================
    # NOTIFICATION METHODS
    # ============================================================
    
    async def send_notification(
        self, 
        user_id: str, 
        message: str, 
        notification_type: str = "general"
    ) -> bool:
        """
        Send notification to user via Telegram
        """
        tg_user = self.db.query(TelegramUser).filter(
            TelegramUser.user_id == user_id
        ).first()
        
        if not tg_user or not tg_user.notifications_enabled:
            return False
        
        # Check specific notification type settings
        if notification_type == "achievement" and not tg_user.achievement_alerts_enabled:
            return False
        if notification_type == "report" and not tg_user.daily_report_enabled:
            return False
        
        result = await self._make_request("sendMessage", {
            "chat_id": tg_user.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        })
        
        return result.get("ok", False)

    async def send_achievement_notification(
        self, 
        user_id: str, 
        achievement_name: str, 
        achievement_description: str
    ) -> bool:
        """Send achievement notification"""
        message = f"""🏆 *Yangi yutuq!*

🎖 *{achievement_name}*

{achievement_description}

Tabriklaymiz! Davom eting! 💪"""
        
        return await self.send_notification(user_id, message, "achievement")

    async def send_daily_report(
        self, 
        user_id: str, 
        stats: Dict[str, Any]
    ) -> bool:
        """Send daily progress report"""
        message = f"""📊 *Kunlik hisobot - {datetime.now().strftime('%d.%m.%Y')}*

⏱ O'qish vaqti: {stats.get('time_spent', 0)} daqiqa
📚 Darslar: {stats.get('lessons_completed', 0)}
🎮 O'yinlar: {stats.get('games_played', 0)}
💰 Tangalar: +{stats.get('coins_earned', 0)}
⭐ Ballar: +{stats.get('points_earned', 0)}

{stats.get('recommendation', "Ajoyib ish! Davom eting!")}"""
        
        return await self.send_notification(user_id, message, "report")

    async def send_new_lesson_notification(
        self, 
        user_ids: List[str], 
        lesson_title: str, 
        lesson_description: str
    ) -> int:
        """Send notification about new lesson to multiple users"""
        message = f"""📚 *Yangi dars!*

📖 *{lesson_title}*

{lesson_description}

Hoziroq boshlang! 🚀"""
        
        sent_count = 0
        for user_id in user_ids:
            if await self.send_notification(user_id, message, "lesson"):
                sent_count += 1
        
        return sent_count 

    # ============================================================
    # QUIZ METHODS
    # ============================================================

    async def send_daily_quiz_to_all(self) -> int:
        """Send a random quiz question to all users"""
        # 1. Get a random active question
        import random
        from app.models.quiz import QuizQuestion, QuizAttempt
        
        questions = self.db.query(QuizQuestion).filter(QuizQuestion.is_active == True).all()
        if not questions:
            return 0
            
        question = random.choice(questions)
        
        # 2. Get all telegram users
        users = self.db.query(TelegramUser).filter(TelegramUser.notifications_enabled == True).all()
        
        sent_count = 0
        for user in users:
            # Check if already attempted this question
            existing_attempt = self.db.query(QuizAttempt).filter(
                QuizAttempt.user_id == user.user_id,
                QuizAttempt.question_id == question.id
            ).first()
            
            if existing_attempt:
                continue
                
            # Send question with inline buttons
            keyboard = {
                "inline_keyboard": [
                    [{"text": opt, "callback_data": f"quiz:{question.id}:{idx}"}]
                    for idx, opt in enumerate(question.options)
                ]
            }
            
            message = f"🧠 *Kunlik Savol*\n\n{question.question_text}\n\nJavobni tanlang:"
            
            await self._make_request("sendMessage", {
                "chat_id": user.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "reply_markup": keyboard
            })
            sent_count += 1
            
        return sent_count

    async def handle_callback_query(self, callback_query: Dict[str, Any]) -> None:
        """Handle inline button clicks"""
        query_id = callback_query.get("id")
        chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
        data = callback_query.get("data", "")
        
        if not data.startswith("quiz:"):
            await self._make_request("answerCallbackQuery", {"callback_query_id": query_id})
            return
            
        # Parse data: quiz:question_id:option_index
        parts = data.split(":")
        if len(parts) != 3:
            return
            
        question_id = parts[1]
        try:
            option_index = int(parts[2])
        except ValueError:
            return

        # Verify answer
        from app.models.quiz import QuizQuestion, QuizAttempt
        from app.models.user import User
        from app.models.rbac_models import StudentProfile
        
        question = self.db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
        if not question:
            await self._make_request("answerCallbackQuery", {
                "callback_query_id": query_id,
                "text": "Savol topilmadi"
            })
            return
            
        tg_user = self.db.query(TelegramUser).filter(TelegramUser.telegram_chat_id == str(chat_id)).first()
        if not tg_user or not tg_user.user_id:
            await self._make_request("answerCallbackQuery", {
                "callback_query_id": query_id,
                "text": "Avval ro'yxatdan o'ting"
            })
            return

        # Check existing attempt
        existing = self.db.query(QuizAttempt).filter(
            QuizAttempt.user_id == tg_user.user_id,
            QuizAttempt.question_id == question_id
        ).first()
        
        if existing:
            await self._make_request("answerCallbackQuery", {
                "callback_query_id": query_id,
                "text": "Siz allaqachon javob bergansiz!",
                "show_alert": True
            })
            return

        is_correct = (option_index == question.correct_option_index)
        coins = question.coins_reward if is_correct else 0
        
        # Save attempt
        attempt = QuizAttempt(
            user_id=tg_user.user_id,
            question_id=question_id,
            chosen_option_index=option_index,
            is_correct=is_correct,
            coins_earned=coins
        )
        self.db.add(attempt)
        
        # Award coins if correct
        if is_correct:
            student = self.db.query(StudentProfile).filter(StudentProfile.user_id == tg_user.user_id).first()
            if student:
                student.total_coins += coins
                student.total_points += 5
        
        self.db.commit()
        
        # Respond
        response_text = "✅ To'g'ri javob! +10 tanga" if is_correct else f"❌ Noto'g'ri. To'g'ri javob: {question.options[question.correct_option_index]}"
        
        await self._make_request("answerCallbackQuery", {
            "callback_query_id": query_id,
            "text": "Javob qabul qilindi"
        })
        
        await self._make_request("sendMessage", {
            "chat_id": chat_id,
            "text": response_text
        })

    # ============================================================
    # WEBHOOK HANDLER
    # ============================================================
    
    async def process_update(self, update: Dict[str, Any]) -> Optional[str]:
        """
        Process incoming Telegram update
        """
        # 1. Handle Callback Queries (Inline Buttons)
        if "callback_query" in update:
            await self.handle_callback_query(update["callback_query"])
            return "Callback processed"

        # 2. Handle Messages
        message = update.get("message")
        if not message:
            return None
        
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        contact = message.get("contact")
        user_info = message.get("from", {})
        
        if not chat_id:
            return None
        
        # Update last interaction
        tg_user = self.db.query(TelegramUser).filter(
            TelegramUser.telegram_chat_id == str(chat_id)
        ).first()
        if tg_user:
            tg_user.last_interaction_at = datetime.utcnow()
            self.db.commit()
        
        response_text = None

        # HANDLE CONTACT
        if contact:
            await self.handle_contact(chat_id, contact)
            return "Contact processed"

        # HANDLE COMMANDS & MENU TEXT
        if text.startswith("/start"):
            args = text.replace("/start", "").strip()
            await self.handle_start(chat_id, user_info, args)
        elif text == "/help" or text == "📞 Yordam":
            response_text = await self.handle_help(chat_id)
        elif text == "/myprofile" or text == "👤 Mening Profilim":
            response_text = await self.handle_myprofile(chat_id)
        elif text == "/mystats" or text == "📊 Statistikam":
            response_text = await self.handle_mystats(chat_id)
        elif text == "🏆 Reyting":
            response_text = "🏆 Reyting tez orada ishga tushadi!"
        elif text == "/quiz" or text == "🧠 Quiz":
            count = await self.send_daily_quiz_to_all()
            if count == 0:
                response_text = "⚠️ Hozircha savollar yo'q yoki hammaga yuborib bo'lindi."
            else:
                response_text = f"✅ {count} ta foydalanuvchiga savol yuborildi."
        elif text.startswith("+998"):
            await self.handle_phone_registration(chat_id, text)
        else:
            # Echo or ignore if unknown, but send menu if exists
            if tg_user and tg_user.phone:
                 response_text = "Quyidagi menyudan tanlang:"
            else:
                 response_text = "Iltimos, telefon raqamingizni yuboring (/start)"
        
        if response_text:
            # Determine keyboard
            markup = self.get_main_keyboard() if (tg_user and tg_user.phone) else self.get_contact_keyboard()
            
            await self._make_request("sendMessage", {
                "chat_id": chat_id,
                "text": response_text,
                "parse_mode": "Markdown",
                "reply_markup": markup
            })
        
        return response_text

    async def set_webhook(self, webhook_url: str) -> bool:
        """Set webhook URL for receiving updates"""
        result = await self._make_request("setWebhook", {
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query"]
        })
        return result.get("ok", False)

    async def delete_webhook(self) -> bool:
        """Delete webhook (for polling mode)"""
        result = await self._make_request("deleteWebhook")
        return result.get("ok", False)

    async def get_bot_info(self) -> Dict[str, Any]:
        """Get bot information"""
        result = await self._make_request("getMe")
        return result.get("result", {})
