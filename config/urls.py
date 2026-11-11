from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from config.views import (
    account_topup_view,          # دالة صفحة الشحن بالحساب المباشر 🔐
    home_view, 
    auth_view, 
    logout_view, 
    dashboard_view, 
    create_order_view, 
    create_deposit_view,
    game_store_view,             # دالة صفحة المتجر
    p2p_market_view,             # دالة سوق التداول والوساطة
    create_p2p_listing_view,     # دالة إنشاء إعلان جديد
    p2p_chat_view,               # دالة شات الوساطة الداخلي 💬
    start_p2p_deal_view,         # دالة بدء الصفقة وتجميد الرصيد 🛡️
    complete_p2p_deal_view,      # دالة تأكيد الاستلام وتحويل المال للبائع ✅
    create_dispute_view,         # دالة فتح النزاع والتدخل الإداري 🚨
    contests_view,               # 🏆 دالة صفحة المسابقات
    join_contest_view,           # 🚀 دالة الانضمام للمسابقة الجديدة
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    
    # صفحة المسابقات والبطولات 🏆
    path('contests/', contests_view, name='contests'),
    path('contests/join/<int:contest_id>/', join_contest_view, name='join_contest'), # <--- الرابط المفقود تم إضافته بنجاح
    
    # صفحة الشحن بالحساب المباشر والتنبيه الأمني 🔐
    path('account-topup/', account_topup_view, name='account_topup'),
    
    # صفحة المتجر الديناميكية للألعاب (فري فاير، ببجي، إلخ)
    path('store/<str:game_code>/', game_store_view, name='game_store'),
    
    # مسارات سوق التداول والوساطة (P2P Market) والشات الداخلي والصفقات
    path('p2p-market/', p2p_market_view, name='p2p_market'),
    path('p2p-market/create/', create_p2p_listing_view, name='create_p2p_listing'),
    path('p2p-market/chat/<int:listing_id>/', p2p_chat_view, name='p2p_chat'),
    
    # مسارات صفقات الوساطة المالية وتجميد الرصيد (Escrow) والنزاعات
    path('p2p-market/deal/start/<int:listing_id>/', start_p2p_deal_view, name='start_p2p_deal'),
    path('p2p-market/deal/complete/<int:deal_id>/', complete_p2p_deal_view, name='complete_p2p_deal'),
    path('p2p-market/deal/dispute/<int:deal_id>/', create_dispute_view, name='create_dispute'),
    
    path('dashboard/', dashboard_view, name='dashboard'),
    path('create-order/', create_order_view, name='create_order'),
    path('create-deposit/', create_deposit_view, name='create_deposit'),
    
    path('login/', auth_view, name='login'),
    path('register/', auth_view, name='register'),
    path('logout/', logout_view, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)