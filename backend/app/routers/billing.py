"""
Subscription billing via Stripe Checkout.

Nothing here will work until you fill in real values in your .env:
STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_ID_PREMIUM.
Create the Price in your Stripe Dashboard (Products > Add product,
recurring monthly/annual) and paste its price_... id into the env var.

Flow:
1. App calls POST /billing/create-checkout-session (auth required).
2. User is redirected to the returned Stripe-hosted checkout_url.
3. On success, Stripe calls your webhook (POST /billing/webhook) —
   point this at https://your-domain.example.com/billing/webhook in the
   Stripe Dashboard, and copy the signing secret into STRIPE_WEBHOOK_SECRET.
4. The webhook marks the user's subscription_tier as "premium".
"""
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import CheckoutSessionResponse

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(current_user: User = Depends(get_current_user)):
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PRICE_ID_PREMIUM:
        raise HTTPException(status_code=503, detail="Billing isn't configured yet — set Stripe env vars first.")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": settings.STRIPE_PRICE_ID_PREMIUM, "quantity": 1}],
        customer_email=current_user.email,
        client_reference_id=current_user.id,
        success_url=settings.BILLING_SUCCESS_URL,
        cancel_url=settings.BILLING_CANCEL_URL,
    )
    return CheckoutSessionResponse(checkout_url=session.url)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook secret not configured.")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        user_id = session_obj.get("client_reference_id")
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.subscription_tier = "premium"
            user.stripe_customer_id = session_obj.get("customer")
            db.commit()

    if event["type"] in ("customer.subscription.deleted", "customer.subscription.paused"):
        customer_id = event["data"]["object"].get("customer")
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.subscription_tier = "free"
            db.commit()

    return {"received": True}
