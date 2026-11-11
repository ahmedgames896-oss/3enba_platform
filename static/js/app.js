// قيم ترحيل العملات الأساسية (مبنية على سعر ثابت تجريبي)
const exchangeRates = {
    USD: 1,
    SAR: 3.75,
    EGP: 50
};
const basePriceUSD = 10; // السعر الثابت الأساسي للعملية بالتصميم

// فتح نافذة الشراء المنبثقة وضبط البيانات التفاعلية
function openOrderModal(gameName) {
    document.getElementById('modalGameName').innerText = gameName;
    document.getElementById('orderModal').classList.add('active');
    updatePrice();
}

// إغلاق النافذة المنبثقة
function closeOrderModal() {
    document.getElementById('orderModal').classList.remove('active');
    // إعادة تعيين الأزرار للحالة الطبيعية
    const payButton = document.getElementById('confirmPayBtn');
    payButton.disabled = false;
    payButton.innerHTML = "تأكيد الدفع";
}

// تحديث السعر تلقائياً بناءً على العملة المختارة
function updatePrice() {
    const selectedCurrency = document.getElementById('currencySelect').value;
    const rate = exchangeRates[selectedCurrency];
    const finalPrice = basePriceUSD * rate;
    
    document.getElementById('modalPrice').innerText = finalPrice.toFixed(2);
    document.getElementById('modalCurrency').innerText = selectedCurrency;
}

// محاكاة معالجة الدفع الآمنة (حظر الزر + الـ Spinner + معالجة الخطأ)
function submitPayment() {
    const playerIDInput = document.getElementById('playerID').value.trim();
    const payButton = document.getElementById('confirmPayBtn');

    // التحقق الفوري من إدخال البيانات
    if (!playerIDInput) {
        alert("من فضلك أدخل الـ ID الخاص باللاعب أولاً!");
        return;
    }

    /* تطبيق الشرط التقني الصارم: 
       تعطيل الزر بالكامل وتحويل النص لعلامة تحميل لمنع النقرات المتكررة */
    payButton.disabled = true;
    payButton.innerHTML = '<span class="spinner"></span> جاري معالجة طلبك...';

    // محاكاة إرسال البيانات للـ Server (تأخير 3 ثوانٍ)
    setTimeout(() => {
        // نسبة نجاح وفشل عشوائية لمحاكاة الحالتين للحقوق والتأكد من السيستم
        const isSuccess = Math.random() > 0.3; 

        if (isSuccess) {
            alert("🎯 تم شحن حسابك بنجاح! شكراً لك.");
            closeOrderModal();
        } else {
            alert("❌ فشلت عملية الدفع. تم تسجيل المشكلة في النظام لحفظ حقوقك، يرجى المحاولة لاحقاً.");
            payButton.disabled = false;
            payButton.innerHTML = "تأكيد الدفع";
        }
    }, 3000);
}