from sqlalchemy.orm import Session
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from app.api import deps
from app.core.config import settings
from pydantic import BaseModel
from app.db.models import Map
from app.services.user import UserService

router = APIRouter()
stripe.api_key = settings.STRIPE_SECRET_KEY

class CheckoutRequest(BaseModel):
    map_id: int

@router.post("/create-session")
def create_checkout_session(
    request: CheckoutRequest, 
    current_user = Depends(deps.get_current_user),
    db = Depends(deps.get_db)
):
    try:
        map_item = db.query(Map).filter(Map.id == request.map_id).first()
       
        if not map_item:
            raise HTTPException(status_code=404, detail="Map not found")
        
        price_in_cents = int(map_item.map_price * 100) 
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=current_user.email,
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                           
                            'name': map_item.title, 
                            'description': map_item.description or f'Lifetime access to {map_item.title}',
                        },
                        'unit_amount': price_in_cents,
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            metadata={
                "user_id": str(current_user.id),
                "map_id": str(map_item.id)
            },
            success_url=f"{settings.FRONTEND_URL}/maps?success=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/maps?canceled=true",
        )
        
        return {"url": checkout_session.url}
    except HTTPException:
        raise
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e.user_message))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
        
WEBHOOK_SECRET = settings.STRIPE_WEBHOOK_SECRET 

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(deps.get_db)):
    """
    Stripe sends a POST request here when events happen (like a successful payment).
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except ValueError as e:
            
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
            
        raise HTTPException(status_code=400, detail="Invalid signature") 
    if event["type"] == "checkout.session.completed":  
        session_obj = event["data"]["object"]
        
        # StripeObject properties are accessed via brackets []
        # session_obj['metadata'] returns a standard dictionary
        metadata = session_obj['metadata']
        
        user_id = metadata['user_id']
        map_id = metadata['map_id']
        
        if user_id and map_id:            
            UserService.grant_user_map_access(db, int(user_id), int(map_id))
            print(f"Successfully unlocked Map {map_id} for User {user_id}")

        
    return {"status": "success"}