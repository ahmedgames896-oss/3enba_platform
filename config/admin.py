from django.contrib import admin
from django.utils.html import format_html
from config.models import (
    UserProfile, 
    Order, 
    DepositRequest, 
    PaymentMethodSetting, 
    GameProduct, 
    P2PListing,
    P2PDeal,
    P2PChatMessage,       # 💬 محادثات الوساطة
    P2PDispute,
    SellerReview,
    TransactionHistory,
    AccountTopupOrder,
    Contest,              # 🏆 المسابقات
    ContestParticipant    # 👥 المشاركون
)

@admin.register(P2PListing)
class P2PListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'game', 'category', 'price', 'include_escrow_insurance', 'status', 'created_at')
    list_editable = ('status', 'include_escrow_insurance')
    list_filter = ('game', 'category', 'status', 'include_escrow_insurance', 'created_at')
    search_fields = ('title', 'seller__username', 'contact_info')


@admin.register(P2PDeal)
class P2PDealAdmin(admin.ModelAdmin):
    list_display = ('id', 'listing', 'buyer', 'seller', 'amount', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'buyer__username', 'seller__username', 'listing__title')


# ---------------------------------------------------------
# لوحة تحكم محادثات الشات في P2P (قراءة فقط للحماية والأمان) 💬
# ---------------------------------------------------------
@admin.register(P2PChatMessage)
class P2PChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'listing', 'sender', 'receiver', 'short_message', 'created_at') # أضفنا عرض نص الرسالة المختصر
    list_filter = ('created_at', 'sender', 'listing')
    search_fields = ('sender__username', 'receiver__username', 'message', 'listing__title')
    readonly_fields = ('listing', 'sender', 'receiver', 'message', 'created_at')
    ordering = ('-created_at',)

    # دالة لعرض أول 50 حرف من الرسالة في الجدول الرئيسي عشان العين تقرأها بسرعة
    def short_message(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    short_message.short_description = 'نص الرسالة'


@admin.register(P2PDispute)
class P2PDisputeAdmin(admin.ModelAdmin):
    list_display = ('deal', 'opened_by', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'created_at')
    search_fields = ('deal__id', 'opened_by__username', 'reason')
    readonly_fields = ('deal', 'opened_by', 'created_at')


@admin.register(SellerReview)
class SellerReviewAdmin(admin.ModelAdmin):
    list_display = ('seller', 'buyer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('seller__username', 'buyer__username', 'comment')


@admin.register(TransactionHistory)
class TransactionHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__username', 'description')
    readonly_fields = ('user', 'amount', 'transaction_type', 'description', 'created_at')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'wallet_balance', 'referral_points', 'referral_code')
    search_fields = ('user__username', 'referral_code')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'game', 'player_id', 'amount_paid', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'game', 'created_at')
    search_fields = ('order_id', 'user__username', 'player_id')
    ordering = ('-created_at',)


@admin.register(DepositRequest)
class DepositRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_method', 'status', 'show_receipt', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    list_editable = ('status',)
    search_fields = ('user__username',)
    readonly_fields = ('show_receipt_large',)

    def show_receipt(self, obj):
        if obj.receipt_image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; border-radius: 5px; object-fit: cover;" />', obj.receipt_image.url)
        return "لا يوجد إيصال"
    show_receipt.short_description = 'صورة الإيصال'

    def show_receipt_large(self, obj):
        if obj.receipt_image:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" style="max-width: 300px; border: 2px solid #00ffcc; border-radius: 10px;" /></a><br><small>اضغط على الصورة لفتحها بحجمها الكامل</small>', obj.receipt_image.url)
        return "لا يوجد إيصال"
    show_receipt_large.short_description = 'معاينة الإيصال للمراجعة'

    def save_model(self, request, obj, form, change):
        if change and obj.status == 'APPROVED':
            original_obj = DepositRequest.objects.get(pk=obj.pk)
            if original_obj.status != 'APPROVED':
                profile = obj.user.profile
                profile.wallet_balance += obj.amount
                profile.save()
        super().save_model(request, obj, form, change)


@admin.register(PaymentMethodSetting)
class PaymentMethodSettingAdmin(admin.ModelAdmin):
    list_display = ('method_type', 'provider_name', 'account_detail', 'is_active')
    list_editable = ('is_active',)


@admin.register(GameProduct)
class GameProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'game', 'price', 'is_special', 'is_active')
    list_editable = ('price', 'is_active', 'is_special')
    list_filter = ('game', 'is_special', 'is_active')
    search_fields = ('title',)


@admin.register(AccountTopupOrder)
class AccountTopupOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'game', 'login_method', 'account_email', 'phone_number', 'status', 'created_at')
    list_filter = ('status', 'game', 'created_at')
    search_fields = ('account_email', 'phone_number', 'user__username')
    list_editable = ('status',)


# ---------------------------------------------------------
# لوحة تحكم المسابقات والبطولات 🏆
# ---------------------------------------------------------
@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ('title', 'contest_type', 'ticket_price', 'room_id', 'room_password', 'is_active', 'created_at')
    list_editable = ('ticket_price', 'room_id', 'room_password', 'is_active')
    list_filter = ('contest_type', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'room_id', 'room_password')
    ordering = ('-created_at',)


@admin.register(ContestParticipant)
class ContestParticipantAdmin(admin.ModelAdmin):
    list_display = ('contest', 'user', 'joined_at')
    list_filter = ('contest', 'joined_at')
    search_fields = ('user__username', 'contest__title')
    ordering = ('-joined_at',)