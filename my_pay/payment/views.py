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
    print(f"User authenticated: {request.user.is_authenticated}")
    
    if request.method == "POST":
        amount = 100   # 1 Rs = 100 paise
        
        print(f"=== CREATING RAZORPAY ORDER ===")
        print(f"Amount: {amount}")
        print(f"Razorpay Key ID: {settings.RAZORPAY_KEY_ID}")
        print(f"Razorpay Key Secret: {settings.RAZORPAY_KEY_SECRET[:10]}...")
        
        try:
            order_data = {
                "amount": amount,
                "currency": "INR",
                "payment_capture": 1,  # Auto capture
                "notes": {
                    "user_id": str(request.user.id),
                    "username": request.user.username,
                }
            }
            
            print(f"Order data: {order_data}")
            order = client.order.create(order_data)
            
            print(f"✅ Order created successfully:")
            print(f"Order ID: {order['id']}")
            print(f"Order Status: {order['status']}")
            print(f"Order Amount: {order['amount']}")
            print(f"Full order response: {json.dumps(order, indent=2, default=str)}")
            
            context = {
                "order_id": order["id"],
                "amount": amount,
                "razorpay_key": settings.RAZORPAY_KEY_ID
            }
            
            print(f"Template context: {context}")
            
            return render(request, "payment/payment.html", context)
            
        except Exception as e:
            error_msg = f"Order creation failed: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"Exception type: {type(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            
            return render(request, "payment/payment.html", {
                "error": error_msg
            })
            
    print("Rendering payment form (GET request)")
    return render(request, "payment/payment.html")


@csrf_exempt
@require_http_methods(["POST"])
def verify_payment(request):
    print(f"\n" + "="*50)
    print(f"=== VERIFY_PAYMENT ENDPOINT HIT ===")
    print(f"="*50)
    print(f"Timestamp: {json.dumps(str(__import__('datetime').datetime.now()), default=str)}")
    print(f"Request method: {request.method}")
    print(f"Request path: {request.path}")
    print(f"Request META (partial): {dict(list(request.META.items())[:10])}")
    print(f"Content type: {request.content_type}")
    print(f"Content length: {len(request.body) if request.body else 0}")
    
    # Log all POST data
    print(f"\n=== REQUEST DATA ===")
    print(f"POST data keys: {list(request.POST.keys())}")
    for key, value in request.POST.items():
        if 'signature' in key.lower():
            print(f"{key}: {value[:20]}...{value[-10:] if len(value) > 30 else value}")
        else:
            print(f"{key}: {value}")
    
    # Get payment details
    payment_id = request.POST.get("razorpay_payment_id")
    order_id = request.POST.get("razorpay_order_id")
    signature = request.POST.get("razorpay_signature")
    
    print(f"\n=== EXTRACTED PAYMENT DATA ===")
    print(f"Payment ID: {payment_id}")
    print(f"Order ID: {order_id}")
    print(f"Signature present: {'Yes' if signature else 'No'}")
    print(f"Signature length: {len(signature) if signature else 0}")
    
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
        
        # Create expected signature
        message = f"{order_id}|{payment_id}"
        print(f"Message to sign: {message}")
        print(f"Secret key (first 10 chars): {settings.RAZORPAY_KEY_SECRET[:10]}...")
        
        expected_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        print(f"Expected signature: {expected_signature}")
        print(f"Received signature: {signature}")
        print(f"Signatures match: {expected_signature == signature}")
        
        if expected_signature != signature:
            error_msg = "Signature verification failed - signatures don't match"
            print(f"❌ {error_msg}")
            return JsonResponse({"status": "failure", "error": error_msg})
        
        print("✅ Signature verified successfully")
        
        # Fetch payment details from Razorpay
        print(f"\n=== FETCHING PAYMENT DETAILS FROM RAZORPAY ===")
        print(f"Payment ID to fetch: {payment_id}")
        
        payment_details = client.payment.fetch(payment_id)
        
        print(f"Payment details received:")
        print(f"Payment status: {payment_details.get('status')}")
        print(f"Payment amount: {payment_details.get('amount')}")
        print(f"Payment currency: {payment_details.get('currency')}")
        print(f"Payment method: {payment_details.get('method')}")
        print(f"Payment captured: {payment_details.get('captured')}")
        print(f"Full payment details: {json.dumps(payment_details, indent=2, default=str)}")
        
        payment_status = payment_details.get('status')
        captured = payment_details.get('captured', False)
        
        print(f"\n=== PAYMENT STATUS CHECK ===")
        print(f"Status: {payment_status}")
        print(f"Captured: {captured}")
        
        # Check if payment needs to be captured
        if payment_status == 'authorized' and not captured:
            print(f"=== CAPTURING PAYMENT ===")
            try:
                capture_amount = payment_details.get('amount')
                print(f"Capturing amount: {capture_amount}")
                
                capture_response = client.payment.capture(payment_id, capture_amount)
                print(f"Capture response: {json.dumps(capture_response, indent=2, default=str)}")
                
                payment_status = 'captured'
                print("✅ Payment captured successfully")
                
            except Exception as capture_error:
                error_msg = f"Payment capture failed: {str(capture_error)}"
                print(f"❌ {error_msg}")
                print(f"Capture error traceback: {traceback.format_exc()}")
                return JsonResponse({"status": "failure", "error": error_msg})
        
        # Final status check
        if payment_status in ['captured', 'authorized']:
            print(f"\n=== SUCCESS - SETTING SESSION DATA ===")
            
            # Store success data in session
            request.session['payment_success'] = True
            request.session['payment_id'] = payment_id
            request.session['order_id'] = order_id
            request.session['amount'] = payment_details.get('amount', 100)
            request.session['payment_method'] = payment_details.get('method')
            
            print(f"Session data set:")
            print(f"- payment_success: True")
            print(f"- payment_id: {payment_id}")
            print(f"- order_id: {order_id}")
            print(f"- amount: {payment_details.get('amount', 100)}")
            
            success_response = {
                "status": "success",
                "payment_id": payment_id,
                "order_id": order_id,
                "payment_status": payment_status,
                "amount": payment_details.get('amount'),
                "message": "Payment verification successful"
            }
            
            print(f"✅ Sending success response: {success_response}")
            return JsonResponse(success_response)
            
        else:
            error_msg = f"Payment not successful. Status: {payment_status}"
            print(f"❌ {error_msg}")
            return JsonResponse({"status": "failure", "error": error_msg})
            
    except razorpay.errors.BadRequestError as e:
        error_msg = f"Razorpay Bad Request: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({"status": "failure", "error": error_msg})
        
    except razorpay.errors.ServerError as e:
        error_msg = f"Razorpay Server Error: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({"status": "failure", "error": error_msg})
        
    except Exception as e:
        error_msg = f"Verification failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"Exception type: {type(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({"status": "failure", "error": error_msg})


def success_page(request):
    print(f"\n=== SUCCESS PAGE ACCESSED ===")
    print(f"Session keys: {list(request.session.keys())}")
    print(f"Payment success flag: {request.session.get('payment_success')}")
    
    if not request.session.get('payment_success'):
        print("❌ No payment success flag in session, redirecting to payment page")
        return redirect('payment_page')
    
    print("✅ Payment success confirmed, showing success page")
    
    # Get payment details from session
    payment_details = {
        'payment_id': request.session.get('payment_id'),
        'order_id': request.session.get('order_id'),
        'amount': request.session.get('amount', 100),
        'payment_method': request.session.get('payment_method')
    }
    
    print(f"Payment details for template: {payment_details}")
    
    # Clear session data
    for key in ['payment_success', 'payment_id', 'order_id', 'amount', 'payment_method']:
        if key in request.session:
            del request.session[key]
    
    print("Session data cleared")
    
    return render(request, "payment/success.html", payment_details)


def failure_page(request):
    print(f"\n=== FAILURE PAGE ACCESSED ===")
    return render(request, "payment/failure.html")