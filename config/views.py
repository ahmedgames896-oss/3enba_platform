from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.db import models
from decimal import Decimal

from .models import (
    UserProfile, 
    Order, 
    DepositRequest, 
    PaymentMethodSetting, 
    GameProduct, 
    P2PListing, 
    P2PChatMessage,
    P2PDeal,
    P2PDispute,
    SellerReview,
    TransactionHistory,
    AccountTopupOrder
)

# 0. دالة الصفحة الرئيسية
def home_view(request):
    active_methods = PaymentMethodSetting.objects.filter(is_active=True)
    return render(request, 'index.html', {
        'active_methods': active_methods
    })


# 1. دالة تسجيل الدخول وإنشاء الحساب الموحدة
@csrf_exempt
@never_cache
def auth_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        if 'username' in request.POST:
            username_input = request.POST.get('username')
            password_input = request.POST.get('password')
            
            user = authenticate(request, username=username_input, password=password_input)
            if user is None:
                try:
                    user_obj = User.objects.get(email=username_input)
                    user = authenticate(request, username=user_obj.username, password=password_input)
                except User.DoesNotExist:
                    user = None

            if user is not None:
                request.session.flush()
                login(request, user)
                messages.success(request, f"مرحباً بعودتك يا {user.username}! 👋")
                return redirect('dashboard')
            else:
                messages.error(request, 'بيانات الدخول خاطئة، يرجى التحقق.')
                
        elif 'reg_username' in request.POST:
            reg_username = request.POST.get('reg_username')
            reg_email = request.POST.get('reg_email')
            reg_password = request.POST.get('reg_password')
            ref_code_input = request.POST.get('referral_code')

            if User.objects.filter(username=reg_username).exists():
                messages.error(request, "اسم المستخدم هذا مسجل بالفعل!")
            elif User.objects.filter(email=reg_email).exists():
                messages.error(request, "البريد الإلكتروني مستخدم مسبقاً!")
            else:
                logout(request)
                request.session.flush()
                
                new_user = User.objects.create_user(username=reg_username, email=reg_email, password=reg_password)
                profile, created = UserProfile.objects.get_or_create(user=new_user)
                
                if ref_code_input:
                    try:
                        inviter_profile = UserProfile.objects.get(referral_code=ref_code_input.strip())
                        inviter_profile.referral_points += 10
                        inviter_profile.save()
                        messages.success(request, "تم تفعيل كود الإحالة بنجاح وحصل صديقك على 10 نقاط! 🎉")
                    except UserProfile.DoesNotExist:
                        pass
                
                login(request, new_user)
                request.session.cycle_key() 
                
                messages.success(request, "تم إنشاء حسابك بنجاح! أهلاً بك في 3enba. 🍇")
                return redirect('dashboard')
                
    return render(request, 'login.html')


# 2. دالة تسجيل الخروج
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('login')


# 3. دالة لوحة التحكم
@login_required(login_url='login')
@never_cache
def dashboard_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    user_deposits = DepositRequest.objects.filter(user=request.user).order_by('-created_at')
    
    active_deals = P2PDeal.objects.filter(
        models.Q(buyer=request.user) | models.Q(seller=request.user)
    ).filter(status__in=['IN_PROGRESS', 'DISPUTED']).order_by('-created_at')
    
    past_deals = P2PDeal.objects.filter(
        models.Q(buyer=request.user) | models.Q(seller=request.user)
    ).filter(status__in=['COMPLETED', 'CANCELLED']).order_by('-created_at')

    has_pending = user_orders.filter(status='PENDING').exists()
    
    context = {
        'profile': profile, 
        'orders': user_orders,
        'deposits': user_deposits,
        'has_pending': has_pending,
        'active_deals': active_deals,
        'past_deals': past_deals,
    }
    return render(request, 'dashboard.html', context)


# 4. دالة إنشاء الطلب
@csrf_exempt
@login_required(login_url='login')
def create_order_view(request):
    if request.method == 'POST':
        game_input = request.POST.get('service_name')
        player_id = request.POST.get('player_id')
        price_input = request.POST.get('price')
        
        game_map = {
            'Free Fire': 'FREEFIRE',
            'PUBG Mobile': 'PUBG',
            'Valorant': 'VALORANT',
            'Call of Duty Mobile': 'COD'
        }
        game_code = game_map.get(game_input, 'FREEFIRE')
        
        try:
            amount_paid = Decimal(price_input)
        except:
            messages.error(request, 'حدث خطأ غير متوقع في معالجة سعر الطلب.')
            return redirect('home')
            
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        if profile.wallet_balance >= amount_paid:
            profile.wallet_balance -= amount_paid
            profile.save()
            
            Order.objects.create(
                user=request.user,
                game=game_code,
                player_id=player_id,
                quantity="شحن مباشر للـ ID",
                amount_paid=amount_paid,
                status='PENDING'
            )
            messages.success(request, f'تم إرسال طلبك بنجاح! وتم خصم {amount_paid} USD من رصيدك، الطلب قيد المعالجة الآن. ⏱️')
            return redirect('dashboard')
        else:
            messages.error(request, 'عذراً! رصيد محفظتك الحالي غير كافٍ لإتمام عملية الشحن هذه. ❌')
            return redirect('home')
            
    return redirect('home')


# 5. دالة استقبال طلب إيداع (محدثة لتشمل رقم الهاتف المرسل 📱)
@csrf_exempt
@login_required(login_url='login')
def create_deposit_view(request):
    if request.method == 'POST':
        amount_input = request.POST.get('deposit_amount')
        payment_method = request.POST.get('payment_method')
        sender_phone = request.POST.get('sender_phone') # <--- استقبال رقم الهاتف المحول منه
        receipt_file = request.FILES.get('receipt_image')
        
        if amount_input and receipt_file:
            try:
                amount = Decimal(amount_input)
                DepositRequest.objects.create(
                    user=request.user,
                    amount=amount,
                    payment_method=payment_method,
                    sender_phone=sender_phone, # <--- حفظ الرقم في القاعدة
                    receipt_image=receipt_file
                )
                messages.success(request, "تم إرسال إيصال التحويل بنجاح! طلبك الآن قيد المراجعة الفورية من الإدارة. ⏱️")
            except:
                messages.error(request, "حدث خطأ أثناء معالجة القيمة المالية، يرجى كتابة مبلغ صحيح.")
        else:
            messages.error(request, "يرجى تعبئة كافة الحقول المطلوبة وإرفاق صورة الإيصال واضحة.")
            
    return redirect(request.META.get('HTTP_REFERER', '/'))


# 6. دالة عرض صفحة تفاصيل اللعبة وباقاتها وعروضها الخاصة
@login_required(login_url='login')
def game_store_view(request, game_code):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    normal_products = GameProduct.objects.filter(game=game_code, is_active=True, is_special=False)
    special_products = GameProduct.objects.filter(game=game_code, is_active=True, is_special=True)
    
    context = {
        'profile': profile,
        'game_code': game_code,
        'normal_products': normal_products,
        'special_products': special_products,
    }
    return render(request, 'game_store.html', context)


# 7. دالة عرض سوق التداول والوساطة (P2P Market)
@login_required(login_url='login')
@never_cache
def p2p_market_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    listings = P2PListing.objects.filter(status='AVAILABLE').order_by('-created_at')
    
    game_query = request.GET.get('game')
    category_query = request.GET.get('category')
    search_query = request.GET.get('q')
    
    if game_query:
        listings = listings.filter(game=game_query)
    if category_query:
        listings = listings.filter(category=category_query)
    if search_query:
        listings = listings.filter(title__icontains=search_query) | listings.filter(description__icontains=search_query)

    context = {
        'profile': profile,
        'listings': listings,
    }
    return render(request, 'p2p_market.html', context)


# 8. دالة إضافة إعلان جديد في سوق الـ P2P
@csrf_exempt
@login_required(login_url='login')
def create_p2p_listing_view(request):
    if request.method == 'POST':
        category = request.POST.get('category')
        game = request.POST.get('game')
        title = request.POST.get('title')
        description = request.POST.get('description')
        price_input = request.POST.get('price')
        contact_info = request.POST.get('contact_info')
        image = request.FILES.get('image')
        include_escrow = request.POST.get('include_escrow_insurance') == 'on'
        include_inspection = request.POST.get('include_inspection') == 'on'

        try:
            price = Decimal(price_input)
            P2PListing.objects.create(
                seller=request.user,
                category=category,
                game=game,
                title=title,
                description=description,
                price=price,
                include_escrow_insurance=include_escrow,
                include_inspection=include_inspection,
                contact_info=contact_info,
                image=image,
                status='AVAILABLE'
            )
            messages.success(request, "تم نشر إعلانك بنجاح في سوق التداول وأصبح مرئياً للمشترين! 🚀")
            return redirect('p2p_market')
        except Exception as e:
            messages.error(request, "حدث خطأ أثناء نشر الإعلان، يرجى التأكد من صحة البيانات المدخلة.")
            
    return redirect('p2p_market')


# 9. دالة فتح غرفة المحادثة والوساطة بين البائع والمشتري
@csrf_exempt
@login_required(login_url='login')
def p2p_chat_view(request, listing_id):
    listing = get_object_or_404(P2PListing, id=listing_id)
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.user == listing.seller:
        active_deal = P2PDeal.objects.filter(listing=listing).exclude(status='COMPLETED').first()
        receiver = active_deal.buyer if active_deal else None
    else:
        receiver = listing.seller
    
    if request.method == 'POST':
        message_text = request.POST.get('message')
        target_user_id = request.POST.get('receiver_id')
        
        target_user = None
        if target_user_id:
            try:
                target_user = User.objects.get(id=target_user_id)
            except User.DoesNotExist:
                pass
        
        if not target_user and receiver:
            target_user = receiver

        if message_text and target_user:
            P2PChatMessage.objects.create(
                listing=listing,
                sender=request.user,
                receiver=target_user,
                message=message_text
            )
            messages.success(request, "تم إرسال الرسالة بنجاح.")
            return redirect('p2p_chat', listing_id=listing.id)

    chat_messages = P2PChatMessage.objects.filter(listing=listing).filter(
        models.Q(sender=request.user) | models.Q(receiver=request.user)
    ).order_by('created_at')

    active_deal = P2PDeal.objects.filter(listing=listing).exclude(status='COMPLETED').first()

    context = {
        'profile': profile,
        'listing': listing,
        'chat_messages': chat_messages,
        'receiver': receiver,
        'active_deal': active_deal,
    }
    return render(request, 'p2p_chat.html', context)


# 10. دالة بدء صفقة الشراء وتجميد الرصيد (Escrow)
@csrf_exempt
@login_required(login_url='login')
def start_p2p_deal_view(request, listing_id):
    listing = get_object_or_404(P2PListing, id=listing_id, status='AVAILABLE')
    
    if request.user == listing.seller:
        messages.error(request, "لا يمكنك شراء إعلانك الخاص!")
        return redirect('p2p_market')
    
    buyer_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    fee = Decimal('1.00') if listing.include_escrow_insurance else Decimal('0.00')
    total_amount = listing.price + fee
    
    if buyer_profile.wallet_balance < total_amount:
        messages.error(request, f"رصيدك غير كافٍ لإتمام الصفقة. المطلوب: ${total_amount}")
        return redirect('p2p_chat', listing_id=listing.id)
    
    buyer_profile.wallet_balance -= total_amount
    buyer_profile.save()
    
    listing.status = 'PENDING'
    listing.save()
    
    deal = P2PDeal.objects.create(
        listing=listing,
        buyer=request.user,
        seller=listing.seller,
        amount=total_amount,
        status='IN_PROGRESS'
    )
    
    TransactionHistory.objects.create(
        user=request.user,
        amount=total_amount,
        transaction_type='ESCROW_LOCK',
        description=f"تجميد مبلغ لشراء إعلان P2P #{listing.id}"
    )
    
    P2PChatMessage.objects.create(
        listing=listing,
        sender=request.user,
        receiver=listing.seller,
        message=f"🛡️ نظام الوساطة: قام المشتري بتجميد مبلغ ${total_amount} بنجاح. يمكن للبائع تسليم بيانات الحساب الآن داخل هذا الشات وتحت إشراف المنصة."
    )
    
    messages.success(request, "تم تجميد المبلغ بنجاح لدى الوسيط، وبدأت الصفقة الرسمية داخل الشات!")
    return redirect('p2p_chat', listing_id=listing.id)


# 11. دالة تأكيد استلام الحساب وتحويل الفلوس للبائع
@csrf_exempt
@login_required(login_url='login')
def complete_p2p_deal_view(request, deal_id):
    deal = get_object_or_404(P2PDeal, id=deal_id, buyer=request.user, status='IN_PROGRESS')
    
    seller_profile, _ = UserProfile.objects.get_or_create(user=deal.seller)
    
    seller_payout = deal.listing.price
    seller_profile.wallet_balance += seller_payout
    seller_profile.save()
    
    TransactionHistory.objects.create(
        user=deal.seller,
        amount=seller_payout,
        transaction_type='ESCROW_RELEASE',
        description=f"استلام أرباح صفقة P2P #{deal.id}"
    )
    
    deal.status = 'COMPLETED'
    deal.save()
    
    listing = deal.listing
    listing.status = 'SOLD'
    listing.save()
    
    P2PChatMessage.objects.create(
        listing=listing,
        sender=request.user,
        receiver=listing.seller,
        message="✅ تم تأكيد استلام الحساب بنجاح بواسطة المشتري! وتحويل المستحقات المالية للبائع. شكراً لاستخدامكم 3enba."
    )
    
    messages.success(request, "تم تأكيد الاستلام بنجاح وتحويل المبلغ للبائع. مبروك الصفقة! 🎉")
    return redirect('p2p_market')


# 12. دالة فتح النزاع والتدخل الإداري (زر الأمان)
@csrf_exempt
@login_required(login_url='login')
def create_dispute_view(request, deal_id):
    deal = get_object_or_404(P2PDeal, id=deal_id)
    
    if request.user != deal.buyer and request.user != deal.seller:
        messages.error(request, "ليس لديك صلاحية للتدخل في هذه الصفقة.")
        return redirect('p2p_market')
    
    if request.method == 'POST':
        reason = request.POST.get('reason', 'لم يتم تحديد السبب بالتفصيل')
        
        P2PDispute.objects.create(
            deal=deal,
            opened_by=request.user,
            reason=reason,
            status='OPEN'
        )
        
        deal.status = 'DISPUTED'
        deal.save()
        
        P2PChatMessage.objects.create(
            listing=deal.listing,
            sender=request.user,
            receiver=deal.seller if request.user == deal.buyer else deal.buyer,
            message=f"🚨 تنبيه أمني: قام المستخدم ({request.user.username}) بطلب تدخل الإدارة وفتح نزاع رسمي على الصفقة. تم تجميد كافة العمليات لحين فحص الإدارة."
        )
        
        messages.warning(request, "تم إرسال بلاغك للإدارة بنجاح، تم تجميد الصفقة وسيتم مراجعتها قريباً.")
        return redirect('p2p_chat', listing_id=deal.listing.id)
        
    return redirect('p2p_chat', listing_id=deal.listing.id)


# 13. دالة معالجة شحن الحساب المباشر والتنبيه الأمني 🔐
@csrf_exempt
@login_required(login_url='login')
def account_topup_view(request):
    if request.method == 'POST':
        game = request.POST.get('game')
        login_method = request.POST.get('login_method')
        account_email = request.POST.get('account_email')
        account_password = request.POST.get('account_password')
        phone_number = request.POST.get('phone_number')
        package_details = request.POST.get('package_details')

        # حفظ طلب الشحن المباشر في قاعدة البيانات ليظهر للأدمن
        AccountTopupOrder.objects.create(
            user=request.user,
            game=game,
            login_method=login_method,
            account_email=account_email,
            account_password=account_password,
            phone_number=phone_number,
            package_details=package_details
        )
        messages.success(request, "تم إرسال طلب الشحن المباشر بنجاح! فريق الدعم سيتولى تنفيذه قريباً. ⏱️")
        return redirect('dashboard')

    return render(request, 'account_topup.html')
    # الاستيرادات (أضف Contest و ContestParticipant مع باقي الموديلات فوق):
from .models import (
    # ... الموديلات السابقة ...
    Contest,
    ContestParticipant
)

# ---------------------------------------------------------
# نظام المسابقات (عرض المسابقات + الانضمام وشراء التذاكر)
# ---------------------------------------------------------

# دالة عرض صفحة المسابقات
@login_required(login_url='login')
@never_cache
def contests_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    contests = Contest.objects.filter(is_active=True).order_by('-created_at')
    
    # معرفة المسابقات التي شارك فيها المستخدم مسبقاً
    user_joined_contests = ContestParticipant.objects.filter(user=request.user).values_list('contest_id', flat=True)

    context = {
        'profile': profile,
        'contests': contests,
        'user_joined_contests': user_joined_contests,
    }
    return render(request, 'contests.html', context)


# دالة الانضمام للمسابقة (مجانية أو مدفوعة مع خصم تذكرة المشرفين)
# دالة الانضمام للمسابقة (مع التحقق الذكي من نشر رابط الإحالة للمسابقات المجانية)
@csrf_exempt
@login_required(login_url='login')
def join_contest_view(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id, is_active=True)
    
    # التأكد من عدم الانضمام مسبقاً
    if ContestParticipant.objects.filter(contest=contest, user=request.user).exists():
        messages.warning(request, "أنت مشترك بالفعل في هذه المسابقة!")
        return redirect('contests')

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # إذا كانت المسابقة مجانية 🎁 -> نتحقق من نقاط الإحالة المطلوبة الخاصة بهذه المسابقة حصرياً
    if contest.contest_type == 'FREE':
        if profile.referral_points < contest.required_referral_points:
            # نحسب كم إحالة ناقصة أو نبهه بالعدد المطلوب
            messages.error(request, f"عذراً! هذه المسابقة تتطلب جمع {contest.required_referral_points} نقطة إحالة على الأقل (لديك {profile.referral_points} نقطة). انشر رابطك لجلب أصدقائك والاشتراك فوراً! 🚀")
            return redirect('contests')

    # 2. إذا كانت المسابقة مدفوعة 🎟️ -> نتحقق من رصيد المحفظة لتغطية تكاليف المشرفين
    elif contest.contest_type == 'PAID':
        if profile.wallet_balance < contest.ticket_price:
            messages.error(request, f"رصيدك غير كافٍ لشراء تذكرة هذه المسابقة. السعر المطلوب: ${contest.ticket_price} ❌")
            return redirect('contests')
        
        # خصم سعر التذكرة من المحفظة
        profile.wallet_balance -= contest.ticket_price
        profile.save()

        # تسجيل الحركة المالية في الـ Audit Log
        TransactionHistory.objects.create(
            user=request.user,
            amount=contest.ticket_price,
            transaction_type='ESCROW_LOCK',
            description=f"شراء تذكرة دخول مسابقة مدفوعة: {contest.title}"
        )

    # تسجيل الانضمام بنجاح
    ContestParticipant.objects.create(
        contest=contest,
        user=request.user
    )

    messages.success(request, f"تم انضمامك بنجاح إلى مسابقة '{contest.title}'! بالتوفيق 🏆")
    return redirect('contests')