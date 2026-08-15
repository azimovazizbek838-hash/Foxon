from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Routers importi
from app.routers import auth, generate, history, payment

app = FastAPI(
    title="Foxon AI Music Mini App API",
    version="1.0.0",
    description="300 Telegram Stars to'lov tizimi va 35 ta musiqa limiti bilan AI generator"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(generate.router)
app.include_router(history.router)
app.include_router(payment.router)


USER_DATA_DB = {}
STAR_PAYMENT_PRICE = 300  
MAX_MUSIC_LIMIT = 35      
MAX_DURATION_SECONDS = 360 

class MusicGenerateRequest(BaseModel):
    prompt: str = Field(..., description="Musiqa stili")
    duration_seconds: int = Field(..., ge=15, le=360)

class PaymentVerifyRequest(BaseModel):
    telegram_payment_charge_id: str
    stars_amount: int


@app.get("/health")
async def health():
    return {"status": "ok", "app": "Foxon AI Music Backend"}


@app.post("/api/payment/verify-stars")
async def verify_stars_payment(
    data: PaymentVerifyRequest, 
    x_user_id: str = Header(..., alias="X-User-ID")
):
    if data.stars_amount < STAR_PAYMENT_PRICE:
        raise HTTPException(
            status_code=400, 
            detail=f"To'lov yetarsiz. Kamida {STAR_PAYMENT_PRICE} Telegram Stars talab qilinadi."
        )

    USER_DATA_DB[x_user_id] = {
        "has_paid": True,
        "remaining_tracks": MAX_MUSIC_LIMIT,
        "payment_id": data.telegram_payment_charge_id
    }

    return {
        "status": "success",
        "message": f"To'lov tasdiqlandi! Sizga {MAX_MUSIC_LIMIT} ta musiqa yaratish imkoniyati berildi.",
        "remaining_tracks": MAX_MUSIC_LIMIT
    }


@app.post("/api/generate-music")
async def generate_music(
    request: MusicGenerateRequest, 
    x_user_id: str = Header(..., alias="X-User-ID")
):
    user_info = USER_DATA_DB.get(x_user_id)

    if not user_info or not user_info.get("has_paid"):
        raise HTTPException(
            status_code=402, 
            detail="Musiqa yaratish uchun avval 300 Telegram Stars to'lovini amalga oshiring!"
        )

    if user_info.get("remaining_tracks", 0) <= 0:
        raise HTTPException(
            status_code=403, 
            detail="Musiqa yaratish limitiningiz (35 ta) tugagan."
        )

    if request.duration_seconds > MAX_DURATION_SECONDS:
        raise HTTPException(
            status_code=400, 
            detail="Musiqa davomiyligi eng uzog'i 6 daqiqa (360 soniya) bo'lishi mumkin."
        )

    user_info["remaining_tracks"] -= 1

    return {
        "status": "processing",
        "prompt": request.prompt,
        "duration_seconds": request.duration_seconds,
        "remaining_tracks": user_info["remaining_tracks"],
        "message": "Musiqa generatsiyasi boshlandi!"
    }
