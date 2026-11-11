from django.db import models
from django.contrib.auth.models import User
import uuid

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    referral_points = models.IntegerField(default=0)
    referral_code = models.CharField(max_length=15, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = f"3ENBA-{uuid.uuid4().hex[:4].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"حساب {self.user.username}"


# موديل إدارة منتجات وباقات الألعاب
class GameProduct(models.Model):
    GAME_CHOICES = [
        ('PUBG', 'PUBG Mobile'),
        ('FREEFIRE', 'Free Fire'),
        ('VALORANT', 'Valorant'),
        ('COD', 'Call of Duty'),
    ]

    game = models.CharField(max_length=20, choices=GAME_CHOICES, verbose_name="اللعبة")
    title = models.CharField(max_length=100, verbose_name="اسم الباقة (مثلاً: 100 جوهرة / العضوية الشهرية)")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر (USD)")
    is_special = models.BooleanField(default=False, verbose_name="هل هي من العروض الخاصة؟ (مثل تصريح بوياه)")
    product_image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="صورة الباقة (اختياري)")
    is_active = models.BooleanField(default=True, verbose_name="مفعلة للبيع")

    class Meta:
        verbose_name = "باقة لعبة"
        verbose_name_plural = "🎮 باقات ومنتجات الألعاب"

    def __str__(self):
        return f"{self.get_game_display()} - {self.title} (${self.price})"


class Order(models.Model):
    STATUS_CHOICES = [
        ('SUCCESS', 'ناجح'),
        ('PENDING', 'قيد الانتظار'),
        ('FAILED', 'فشل الدفع'),
    ]
    
    GAME_CHOICES = GameProduct.GAME_CHOICES

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_id = models.CharField(max_length=12, unique=True, blank=True)
    game = models.CharField(max_length=20, choices=GAME_CHOICES)
    player_id = models.CharField(max_length=50)
    quantity = models.CharField(max_length=100)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = f"#{uuid.uuid4().int % 100000}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"طلب {self.order_id} - اللعبة: {self.game}"


class DepositRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'قيد المراجعة ⏱️'),
        ('APPROVED', 'مقبول وتم الشحن ✅'),
        ('REJECTED', 'مرفوض ❌'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=100, default='فودافون كاش')
    sender_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم الهاتف المرسل")
    receipt_image = models.ImageField(upload_to='receipts/') 
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"إيداع بقيمة {self.amount}$ بواسطة {self.user.username}"


class PaymentMethodSetting(models.Model):
    method_type = models.CharField(max_length=100, verbose_name="نوع وسيلة الدفع (اكتبها بحرية)")
    provider_name = models.CharField(max_length=100, verbose_name="اسم صاحب الحساب / الشبكة")
    account_detail = models.CharField(max_length=255, verbose_name="رقم المحفظة / اسم المستخدم (ID) / الـ IBAN")
    is_active = models.BooleanField(default=True, verbose_name="تفعيل استقبال الأموال عليها")

    class Meta:
        verbose_name = "إعداد وسيلة دفع"
        verbose_name_plural = "⚙️ إعدادات وسائل الدفع"

    def __str__(self):
        return f"{self.method_type} - {self.provider_name}"


# ---------------------------------------------------------
# موديل طلبات الشحن بالحساب المباشر 🔐
# ---------------------------------------------------------
class AccountTopupOrder(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'قيد الانتظار ⏱️'),
        ('PROCESSING', 'جاري التنفيذ 🔄'),
        ('COMPLETED', 'مكتمل ✅'),
        ('REJECTED', 'مرفوض ❌'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account_topups', verbose_name="المستخدم")
    game = models.CharField(max_length=50, verbose_name="اللعبة المستهدفة")
    login_method = models.CharField(max_length=50, verbose_name="طريقة تسجيل الدخول")
    account_email = models.CharField(max_length=255, verbose_name="البريد / المعرف")
    account_password = models.CharField(max_length=255, verbose_name="كلمة المرور")
    phone_number = models.CharField(max_length=20, verbose_name="رقم الهاتف للتواصل")
    package_details = models.CharField(max_length=255, verbose_name="تفاصيل الباقة المطلوبة")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="حالة الطلب")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")

    class Meta:
        verbose_name = "طلب شحن بالحساب"
        verbose_name_plural = "🔐 طلبات الشحن بالحساب المباشر"

    def __str__(self):
        return f"طلب شحن حساب #{self.id} - {self.user.username} ({self.game})"


# موديل سوق التداول والوساطة المطور (P2P Marketplace)
class P2PListing(models.Model):
    CATEGORY_CHOICES = [
        ('ACCOUNT', 'حساب لعبة كامل 👤'),
        ('ITEM', 'عنصر / سكن / سلاح 🗡️'),
        ('SERVICE', 'خدمة / ترفيع لفل / بوست ⚡'),
    ]

    GAME_CHOICES = [
        ('PUBG', 'PUBG Mobile'),
        ('FREEFIRE', 'Free Fire'),
        ('VALORANT', 'Valorant'),
        ('COD', 'Call of Duty'),
    ]

    STATUS_CHOICES = [
        ('AVAILABLE', 'متاح للبيع 🟢'),
        ('PENDING', 'قيد الوساطة / محجوز 🟡'),
        ('SOLD', 'تم البيع ✅'),
    ]

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='p2p_listings', verbose_name="البائع")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='ACCOUNT', verbose_name="نوع العرض")
    game = models.CharField(max_length=20, choices=GAME_CHOICES, verbose_name="اللعبة")
    title = models.CharField(max_length=150, verbose_name="عنوان الإعلان (مثلاً: حساب فري فاير لفل 80)")
    description = models.TextField(verbose_name="تفاصيل الحساب أو العنصر")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر الأساسي (USD)")
    
    include_escrow_insurance = models.BooleanField(default=True, verbose_name="تفعيل وساطة وضمان المنصة (+$1.00 رسوم تأمين)")
    include_inspection = models.BooleanField(default=False, verbose_name="طلب فحص وتسليم إداري شامل بواسطة الإدارة (خدمة مميزة إضافية)")
    
    contact_info = models.CharField(max_length=100, blank=True, null=True, verbose_name="رابط أو وسيلة التواصل (واتساب / تيليجرام / آيدي)")
    image = models.ImageField(upload_to='p2p_images/', verbose_name="صورة توضيحية")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='AVAILABLE', verbose_name="حالة الإعلان")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "إعلان P2P"
        verbose_name_plural = "🤝 سوق الحسابات والتداول (P2P)"

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title} (${self.price})"


# موديل محادثات الوساطة والشات الداخلي لحماية المعاملات
class P2PChatMessage(models.Model):
    listing = models.ForeignKey(P2PListing, on_delete=models.CASCADE, related_name='messages', verbose_name="الإعلان المرتبط")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name="المرسل")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', verbose_name="المستلم")
    message = models.TextField(verbose_name="نص الرسالة")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "رسالة وساطة"
        verbose_name_plural = "💬 محادثات وسوق P2P"

    def __str__(self):
        return f"رسالة من {self.sender.username} إلى {self.receiver.username}"


# موديل صفقات التداول والوساطة المالية (Escrow Deal)
class P2PDeal(models.Model):
    DEAL_STATUS = [
        ('PENDING_PAYMENT', 'في انتظار تأمين المبلغ 🟡'),
        ('IN_PROGRESS', 'جارِ تسليم الحساب عبر الشات 🔄'),
        ('COMPLETED', 'تم التسليم وتحويل الفلوس للبائع ✅'),
        ('DISPUTED', 'مفتوح للنزاع / تدخل الأدمن ⚠️'),
        ('CANCELLED', 'تم إلغاء الصفقة واسترجاع الرصيد ❌'),
    ]

    listing = models.ForeignKey(P2PListing, on_delete=models.CASCADE, related_name='deals', verbose_name="الإعلان المرتبط")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_deals', verbose_name="المشتري")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_deals', verbose_name="البائع")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="إجمالي المبلغ المجمد")
    status = models.CharField(max_length=20, choices=DEAL_STATUS, default='IN_PROGRESS', verbose_name="حالة الصفقة")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "صفقة وساطة"
        verbose_name_plural = "🛡️ صفقات الوساطة المالية (Escrow)"

    def __str__(self):
        return f"صفقة #{self.id} للإعلان {self.listing.title} بقيمة {self.amount}$"


# موديل النزاعات والتدخل الإداري
class P2PDispute(models.Model):
    DISPUTE_STATUS = [
        ('OPEN', 'مفتوح / قيد التدخل الإداري 🟡'),
        ('RESOLVED_BUYER', 'تم الحل لصالح المشتري (استرجاع المبلغ) ✅'),
        ('RESOLVED_SELLER', 'تم الحل لصالح البائع (تحرير المبلغ) ✅'),
    ]

    deal = models.ForeignKey(P2PDeal, on_delete=models.CASCADE, related_name='disputes', verbose_name="الصفقة المتنازع عليها")
    opened_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opened_disputes', verbose_name="فتح النزاع بواسطة")
    reason = models.TextField(verbose_name="سبب النزاع والمشكلة بالتفصيل")
    status = models.CharField(max_length=20, choices=DISPUTE_STATUS, default='OPEN', verbose_name="حالة النزاع")
    admin_notes = models.TextField(blank=True, null=True, verbose_name="تقرير وقرار الأدمن الفاصل")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ فتح النزاع")

    class Meta:
        verbose_name = "نزاع وساطة"
        verbose_name_plural = "⚖️ نزاعات وشكاوى P2P (تدخل الأدمن)"

    def __str__(self):
        return f"نزاع على صفقة #{self.deal.id} بواسطة {self.opened_by.username}"


# موديل تقييمات السمعة للبائعين
class SellerReview(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received', verbose_name="البائع")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given', verbose_name="المشتري")
    deal = models.ForeignKey(P2PDeal, on_delete=models.SET_NULL, null=True, blank=True, related_name='review', verbose_name="الصفقة المرتبطة")
    rating = models.IntegerField(default=5, verbose_name="التقييم (من 1 إلى 5 نجوم)")
    comment = models.TextField(blank=True, null=True, verbose_name="تعليق المشتري")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التقييم")

    class Meta:
        verbose_name = "تقييم بائع"
        verbose_name_plural = "⭐ تقييمات وسمعة البائعين"

    def __str__(self):
        return f"تقييم {self.rating} ⭐ للبائع {self.seller.username}"


# موديل سجل الحركات المالية (Audit Log)
class TransactionHistory(models.Model):
    TRANSACTION_TYPES = (
        ('DEPOSIT', 'إيداع رصيد'),
        ('WITHDRAW', 'سحب رصيد'),
        ('ESCROW_LOCK', 'تجميد رصيد (شراء P2P)'),
        ('ESCROW_RELEASE', 'تحرير رصيد للبائع'),
        ('ESCROW_REFUND', 'استرجاع رصيد صفقة ملغاة'),
        ('INSPECTION_FEE', 'رسوم فحص وإشراف إداري شامل'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions', verbose_name="المستخدم")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, verbose_name="نوع الحركة")
    description = models.CharField(max_length=255, verbose_name="التفاصيل")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الحركة")

    class Meta:
        verbose_name = "سجل حركة مالية"
        verbose_name_plural = "📑 سجل الحركات المالية (Audit Log)"

    def __str__(self):
        return f"{self.get_transaction_type_display()} | {self.amount}$ | {self.user.username}"


# ---------------------------------------------------------
# نظام المسابقات والبطولات المجانية والمدفوعة 🏆 (مع بيانات الغرفة والواتساب)
# ---------------------------------------------------------
class Contest(models.Model):
    CONTEST_TYPES = [
        ('FREE', 'مسابقة مجانية 🎁'),
        ('PAID', 'مسابقة مدفوعة (تذكرة دخول للأشراف) 🎟️'),
    ]

    title = models.CharField(max_length=150, verbose_name="عنوان المسابقة")
    description = models.TextField(verbose_name="تفاصيل وشروط المسابقة")
    contest_type = models.CharField(max_length=10, choices=CONTEST_TYPES, default='FREE', verbose_name="نوع المسابقة")
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="سعر التذكرة / رسوم الإشراف (USD)")
    required_referral_points = models.IntegerField(default=10, verbose_name="نقاط الإحالة المطلوبة للاشتراك (للمجانية فقط)")
    
    # حقول بيانات الغرفة والتنبيهات (آمنة بدون أخطاء أصفار)
    room_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="رقم الغرفة (Room ID)")
    room_password = models.CharField(max_length=100, blank=True, null=True, verbose_name="باسورد الغرفة")
    whatsapp_channel_link = models.URLField(default="https://whatsapp.com/channel/0029VbAUvA23rZZkD3KECG1z", blank=True, null=True, verbose_name="رابط قناة/جروب الواتساب للتنبيهات")

    prize_description = models.CharField(max_length=255, verbose_name="وصف الجائزة (مثلاً: 1000 جوهرة أو 10$)")
    max_participants = models.IntegerField(default=100, verbose_name="الحد الأقصى للمشاركين")
    is_active = models.BooleanField(default=True, verbose_name="مسابقة نشطة حالياً")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "مسابقة"
        verbose_name_plural = "🏆 نظام المسابقات والبطولات"

    def __str__(self):
        return f"{self.title} ({self.get_contest_type_display()})"


class ContestParticipant(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='participants', verbose_name="المسابقة")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_contests', verbose_name="المشارك")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الانضمام")

    class Meta:
        unique_together = ('contest', 'user')
        verbose_name = "مشارك في مسابقة"
        verbose_name_plural = "👥 المشاركون في المسابقات"

    def __str__(self):
        return f"{self.user.username} - {self.contest.title}"