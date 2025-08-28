# payment/views.py
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
import razorpay
import json
import hmac
import hashlib

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required(login_url="/accounts/login/")
def payment_page(request):
    if request.method == "POST":
        amount = 100  # 1 Rs = 100 paise
        
        print("=== CREATING ORDER ===")
        print(f"Amount: {amount}")
        print(f"Razorpay Key: {settings.RAZORPAY_KEY_ID}")
        
        try:
            order = client.order.create({
                "amount": amount,
                "currency": "INR",
                "payment_capture": 1  # Auto capture payment
            })
            
            print(f"Order created: {order}")
            
            return render(request, "payment/payment.html", {
                "order_id": order["id"],
                "amount": amount,
                "razorpay_key": settings.RAZORPAY_KEY_ID
            })
            
        except Exception as e:
            print(f"❌ Order creation failed: {e}")
            return render(request, "payment/payment.html", {
                "error": f"Order creation failed: {str(e)}"
            })
            
    return render(request, "payment/payment.html")


@csrf_exempt
def verify_payment(request):
    print(f"\n=== VERIFY_PAYMENT CALLED ===")
    print(f"Request method: {request.method}")
    print(f"Request POST data: {dict(request.POST)}")
    print(f"Request body: {request.body.decode('utf-8', errors='ignore')}")
    
    if request.method == "POST":
        # Get payment details
        payment_id = request.POST.get("razorpay_payment_id")
        order_id = request.POST.get("razorpay_order_id")
        signature = request.POST.get("razorpay_signature")
        
        print(f"Payment ID: {payment_id}")
        print(f"Order ID: {order_id}")
        print(f"Signature: {signature}")
        
        if not all([payment_id, order_id, signature]):
            error_msg = "Missing required parameters"
            print(f"ERROR: {error_msg}")
            return JsonResponse({"status": "failure", "error": error_msg})
        
        try:
            # Manual signature verification (more reliable)
            print("=== MANUAL SIGNATURE VERIFICATION ===")
            expected_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
                f"{order_id}|{payment_id}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            print(f"Expected signature: {expected_signature}")
            print(f"Received signature: {signature}")
            
            if expected_signature != signature:
                error_msg = "Signature verification failed"
                print(f"❌ {error_msg}")
                return JsonResponse({"status": "failure", "error": error_msg})
            
            print("✅ Signature verified successfully")
            
            # Fetch payment details
            print("=== FETCHING PAYMENT DETAILS ===")
            payment_details = client.payment.fetch(payment_id)
            print(f"Payment details: {json.dumps(payment_details, indent=2, default=str)}")
            
            payment_status = payment_details.get('status')
            print(f"Payment status: {payment_status}")
            
            # Check if payment is successful
            if payment_status in ['captured', 'authorized']:
                print("✅ Payment is successful!")
                
                # Store payment info in session
                request.session['payment_success'] = True
                request.session['payment_id'] = payment_id
                request.session['order_id'] = order_id
                request.session['amount'] = payment_details.get('amount', 100)
                
                return JsonResponse({
                    "status": "success",
                    "payment_id": payment_id,
                    "payment_status": payment_status,
                    "message": "Payment successful"
                })
            else:
                error_msg = f"Payment failed. Status: {payment_status}"
                print(f"❌ {error_msg}")
                return JsonResponse({"status": "failure", "error": error_msg})
                
        except razorpay.errors.SignatureVerificationError as e:
            error_msg = f"Signature verification failed: {str(e)}"
            print(f"❌ {error_msg}")
            return JsonResponse({"status": "failure", "error": error_msg})
            
        except Exception as e:
            error_msg = f"Verification failed: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"Exception type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({"status": "failure", "error": error_msg})
    
    error_msg = "Invalid request method"
    print(f"❌ {error_msg}")
    return JsonResponse({"status": "failure", "error": error_msg})


def success_page(request):
    print(f"\n=== SUCCESS PAGE ACCESSED ===")
    print(f"Session data: {dict(request.session)}")
    
    if not request.session.get('payment_success'):
        print("❌ No payment success flag in session, redirecting to payment page")
        return redirect('payment_page')
    
    print("✅ Payment success confirmed, showing success page")
    
    # Get payment details from session
    payment_details = {
        'payment_id': request.session.get('payment_id'),
        'order_id': request.session.get('order_id'),
        'amount': request.session.get('amount', 100)
    }
    
    # Clear session data
    for key in ['payment_success', 'payment_id', 'order_id', 'amount']:
        if key in request.session:
            del request.session[key]
    
    return render(request, "payment/success.html", payment_details)


def failure_page(request):
    print(f"\n=== FAILURE PAGE ACCESSED ===")
    return render(request, "payment/failure.html")