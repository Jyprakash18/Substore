from aiohttp import web
import razorpay
import re
import hmac
import hashlib
from config import RAZORPAY_KEY_ID, RAZORPAY_SECRET_KEY
from bson import ObjectId
from database.database import temp_data, services_data, add_or_update_subscription
import pytz
from datetime import datetime, timedelta
from bot import *  # Make sure to import your bot client

IST = pytz.timezone("Asia/Kolkata")
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET_KEY))

routes = web.RouteTableDef()


# Root route for basic testing
@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.HTTPFound(location="https://t.me/madxmoviez")


# Function to verify Razorpay signature
def verify_signature(body, signature, secret):
    generated_signature = hmac.new(
        secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(generated_signature, signature)


@routes.get("/payment-success")
async def handle_payment_success(request):
    try:
        razorpay_payment_id = request.query.get("razorpay_payment_id")
        razorpay_payment_link_status = request.query.get("razorpay_payment_link_status")
        razorpay_payment_link_id = request.query.get("razorpay_payment_link_id")

        print("Received payment success parameters:", request.query)

        user_data = await temp_data.find_one({"order_id": razorpay_payment_link_id})

        if razorpay_payment_link_status != "paid":
            print(f"Payment not successfull")
            return web.Response(text="Not Paid", status=400)

        if not user_data:
            print(f"Reference ID {razorpay_payment_link_id} not found")
            return web.Response(text="Order not found", status=400)

        user_id = user_data["user_id"]
        service_id = user_data["service_id"]
        plan_duration = user_data["plan_duration"]

        # Fetch the service details
        service = await services_data.find_one({"_id": ObjectId(service_id)})
        if not service:
            print(f"Service ID {service_id} not found")
            return web.Response(text="Service not found", status=400)

        duration_match = re.match(r"(\d+)(year|month|week|day|hour|min)", plan_duration)
        if not duration_match:
            print(f"Invalid plan duration: {plan_duration}")
            return web.Response(text="Invalid plan duration", status=400)

        value, unit = duration_match.groups()
        value = int(value)

        # Calculate the expiry time based on the plan duration
        expiry_time = datetime.now(IST)
        if unit == "day":
            expiry_time += timedelta(days=value)
        elif unit == "week":
            expiry_time += timedelta(weeks=value)
        elif unit == "month":
            expiry_time += timedelta(days=value * 30)
        elif unit == "year":
            expiry_time += timedelta(days=value * 365)
        elif unit == "hour":
            expiry_time += timedelta(hours=value)
        elif unit == "min":
            expiry_time += timedelta(minutes=value)

        await add_or_update_subscription(
            user_id, service_id, plan_duration, razorpay_payment_id
        )

        # Redirecting the user (optional)
        redirect_url = f"https://t.me/MadxSubbot?start=serid_{service_id}"
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Payment Successful</title>
            <script>
                window.location.href = '{redirect_url}';
            </script>
        </head>
        <body>
            <p>If you are not redirected, <a href="{redirect_url}">click here</a>.</p>
        </body>
        </html>
        """

        return web.Response(text=html_response, content_type="text/html", status=200)

    except Exception as e:
        print(f"Error processing webhook: {e}")
        return web.Response(text="Failed to process webhook", status=500)
