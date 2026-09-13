import razorpay
from flask import current_app


def get_client():
    key_id = current_app.config["RAZORPAY_KEY_ID"]
    key_secret = current_app.config["RAZORPAY_KEY_SECRET"]
    if not key_id or not key_secret:
        raise RuntimeError(
            "Razorpay is not configured. Set RAZORPAY_KEY_ID and "
            "RAZORPAY_KEY_SECRET in your .env file."
        )
    return razorpay.Client(auth=(key_id, key_secret))


def create_razorpay_order(amount_rupees: float, receipt: str):
    """amount_rupees is converted to paise (smallest currency unit) as Razorpay requires."""
    client = get_client()
    amount_paise = int(round(amount_rupees * 100))
    return client.order.create(
        {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "payment_capture": 1,
        }
    )


def verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """
    Returns True if the signature is valid, False otherwise.
    This MUST be called on the backend before an order is marked as paid -
    never trust a "payment successful" flag sent directly from the frontend.
    """
    client = get_client()
    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )
        return True
    except razorpay.errors.SignatureVerificationError:
        return False
