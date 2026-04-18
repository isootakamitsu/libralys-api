import os
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8501")

def create_checkout_session(amount_yen, request_id, proposal_id, user_id):

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "jpy",
                "product_data": {
                    "name": f"鑑定依頼申込み金（案件#{request_id}）"
                },
                "unit_amount": int(amount_yen),
            },
            "quantity": 1,
        }],
        success_url=f"{APP_BASE_URL}/?checkout=success",
        cancel_url=f"{APP_BASE_URL}/?checkout=cancel",
        metadata={
            "request_id": str(request_id),
            "proposal_id": str(proposal_id),
            "user_id": str(user_id),
        }
    )

    return session
def refund_payment(payment):
    stripe.Refund.create(
        payment_intent=payment.stripe_payment_intent
    )