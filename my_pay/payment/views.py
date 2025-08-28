# payment/views.py
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
import razorpay
import json

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required(login_url="/accounts/login/")
def payment_page(request):
    if request.method == "POST":
        amount = 100   # 1 Rs = 100 paise
        
        print("=== CREATING ORDER ===")
        print(f"Amount: {amount}")
        print(f"Razorpay Key: {settings.RAZORPAY_KEY_ID}")
        
        order = client.order.create({
            "amount": amount,
            "currency": "INR",
        })
        
        print(f"Order created: {order}")
        
        return render(request, "payment/payment.html", {
            "order_id": order["id"],
            "amount": amount,
            "razorpay_key": settings.RAZORPAY_KEY_ID
        })
    return render(request, "payment/payment.html")


@csrf_exempt
def verify_payment(request):
    print(f"\n=== VERIFY_PAYMENT CALLED ===")
    print(f"Request method: {request.method}")
    print(f"Request POST data: {dict(request.POST)}")
    print(f"Request headers: {dict(request.headers)}")
    
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
        
        # Verification parameters
        params_dict = {
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        }
        
        try:
            print("=== STEP 1: SIGNATURE VERIFICATION ===")
            client.utility.verify_payment_signature(params_dict)
            print("✅ Signature verified successfully")
            
            print("=== STEP 2: FETCH PAYMENT DETAILS ===")
            payment_details = client.payment.fetch(payment_id)
            print(f"Payment details: {json.dumps(payment_details, indent=2, default=str)}")
            
            payment_status = payment_details.get('status')
            print(f"Current payment status: {payment_status}")
            
            if payment_status == 'authorized':
                print("=== STEP 3: CAPTURING PAYMENT ===")
                try:
                    capture_response = client.payment.capture(payment_id, 100)
                    print(f"Capture response: {json.dumps(capture_response, indent=2, default=str)}")
                    payment_status = 'captured'  # Update status after capture
                except Exception as capture_error:
                    print(f"❌ Capture failed: {capture_error}")
                    return JsonResponse({"status": "failure", "error": f"Capture failed: {str(capture_error)}"})
            
            if payment_status == 'captured':
                print("✅ Payment captured successfully!")
                request.session['payment_success'] = True
                return JsonResponse({
                    "status": "success",
                    "payment_id": payment_id,
                    "payment_status": payment_status
                })
            else:
                error_msg = f"Payment not captured. Status: {payment_status}"
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
    if 'payment_success' in request.session:
        del request.session['payment_success']
    
    return render(request, "payment/success.html")


def failure_page(request):
    print(f"\n=== FAILURE PAGE ACCESSED ===")
    return render(request, "payment/failure.html")