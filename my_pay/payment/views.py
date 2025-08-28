# payment/views.py
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods
import razorpay
import json
import hmac
import hashlib
import traceback

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required(login_url="/accounts/login/")
def payment_page(request):
    print(f"\n=== PAYMENT_PAGE VIEW CALLED ===")
    print(f"Method: {request.method}")
    print(f"User: {request.user}")
    
    if request.method == "POST":
        amount = 1000   # 1 Rs = 100 paise
        
        print(f"=== CREATING RAZORPAY ORDER ===")
        print(f"Amount: {amount}")
        
        try:
            order = client.order.create({
                "amount": amount,
                "currency": "INR",
                "payment_capture": 1,  # Auto capture
            })
            
            print(f"✅ Order created: {order['id']}")
            
            return render(request, "payment/payment.html", {
                "order_id": order["id"],
                "amount": amount,
                "razorpay_key": settings.RAZORPAY_KEY_ID
            })
            
        except Exception as e:
            error_msg = f"Order creation failed: {str(e)}"
            print(f"❌ {error_msg}")
            return render(request, "payment/payment.html", {"error": error_msg})
            
    return render(request, "payment/payment.html")


@csrf_exempt
def verify_payment(request):
    print(f"\n{'='*60}")
    print(f"🎯 VERIFY_PAYMENT ENDPOINT HIT!")
    print(f"{'='*60}")
    print(f"Method: {request.method}")
    print(f"Path: {request.path}")
    print(f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
    print(f"Content-Type: {request.content_type}")
    
    if request.method != "POST":
        error_msg = f"Invalid method: {request.method}"
        print(f"❌ {error_msg}")
        return JsonResponse({"status": "failure", "error": error_msg})
    
    # Check if this is just a test request
    if request.POST.get('test') == 'true':
        print("✅ This is a test request - endpoint is working!")
        return JsonResponse({"status": "success", "message": "Verify endpoint is working"})
    
    # Get payment details
    payment_id = request.POST.get("razorpay_payment_id")
    order_id = request.POST.get("razorpay_order_id")
    signature = request.POST.get("razorpay_signature")
    
    print(f"\n=== PAYMENT DATA RECEIVED ===")
    print(f"Payment ID: {payment_id}")
    print(f"Order ID: {order_id}")
    print(f"Signature present: {'Yes' if signature else 'No'}")
    print(f"All POST data: {dict(request.POST)}")
    
    # Validate required fields
    if not all([payment_id, order_id, signature]):
        missing = []
        if not payment_id: missing.append("razorpay_payment_id")
        if not order_id: missing.append("razorpay_order_id") 
        if not signature: missing.append("razorpay_signature")
        
        error_msg = f"Missing required parameters: {', '.join(missing)}"
        print(f"❌ {error_msg}")
        return JsonResponse({"status": "failure", "error": error_msg})
    
    try:
        print(f"\n=== SIGNATURE VERIFICATION ===")
        
        # Manual signature verification
        message = f"{order_id}|{payment_id}"
        expected_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        print(f"Expected: {expected_signature}")
        print(f"Received: {signature}")
        print(f"Match: {expected_signature == signature}")
        
        if expected_signature != signature:
            error_msg = "Signature verification failed"
            print(f"❌ {error_msg}")
            return JsonResponse({"status": "failure", "error": error_msg})
        
        print("✅ Signature verified!")
        
        # Fetch payment from Razorpay
        print(f"\n=== FETCHING PAYMENT FROM RAZORPAY ===")
        payment_details = client.payment.fetch(payment_id)
        
        payment_status = payment_details.get('status')
        print(f"Payment status: {payment_status}")
        print(f"Payment amount: {payment_details.get('amount')}")
        print(f"Captured: {payment_details.get('captured', False)}")
        
        # Check if payment is successful
        if payment_status in ['captured', 'authorized']:
            print(f"✅ Payment is successful! Status: {payment_status}")
            
            # Store in session
            request.session['payment_success'] = True
            request.session['payment_id'] = payment_id
            request.session['order_id'] = order_id
            request.session['amount'] = payment_details.get('amount', 100)
            
            print("✅ Session data stored")
            
            return JsonResponse({
                "status": "success",
                "payment_id": payment_id,
                "payment_status": payment_status,
                "message": "Payment verified successfully"
            })
        else:
            error_msg = f"Payment not successful. Status: {payment_status}"
            print(f"❌ {error_msg}")
            return JsonResponse({"status": "failure", "error": error_msg})
            
    except Exception as e:
        error_msg = f"Verification failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"Exception: {type(e).__name__}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({"status": "failure", "error": error_msg})


def success_page(request):
    print(f"\n=== SUCCESS PAGE ===")
    print(f"Payment success in session: {request.session.get('payment_success')}")
    
    if not request.session.get('payment_success'):
        print("❌ No payment success flag, redirecting")
        return redirect('payment_page')
    
    print("✅ Showing success page")
    
    # Get payment details
    payment_details = {
        'payment_id': request.session.get('payment_id'),
        'order_id': request.session.get('order_id'),
        'amount': request.session.get('amount', 100)
    }
    
    # Clear session
    for key in ['payment_success', 'payment_id', 'order_id', 'amount']:
        request.session.pop(key, None)
    
    return render(request, "payment/success.html", payment_details)


def failure_page(request):
    print(f"\n=== FAILURE PAGE ===")
    return render(request, "payment/failure.html")