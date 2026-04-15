from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from .models import MarketItem, MarketOrder, Notification
from .utils import award_xp


def market_view(request):
    category = request.GET.get('cat', '')
    qs = MarketItem.objects.filter(is_active=True)
    if category:
        qs = qs.filter(category=category)

    # Foydalanuvchi buyurtmalari
    my_orders = []
    if request.user.is_authenticated:
        my_orders = list(
            MarketOrder.objects.filter(user=request.user)
            .select_related('item').order_by('-created_at')[:10]
        )

    return render(request, 'market/list.html', {
        'items':      qs,
        'categories': MarketItem.CATEGORIES,
        'selected':   category,
        'my_orders':  my_orders,
    })


@login_required
def market_buy(request, pk):
    item = get_object_or_404(MarketItem, pk=pk, is_active=True)
    user = request.user

    if request.method != 'POST':
        return render(request, 'market/confirm.html', {'item': item})

    # Tekshiruvlar
    if not item.in_stock():
        messages.error(request, "Bu mahsulot tugagan.")
        return redirect('market')

    if user.score < item.price:
        messages.error(request, f"Balingiz yetarli emas. Kerak: {item.price}, sizda: {user.score}.")
        return redirect('market')

    # Allaqachon kutilayotgan buyurtma bormi?
    if MarketOrder.objects.filter(user=user, item=item, status='pending').exists():
        messages.info(request, "Bu mahsulot uchun buyurtmangiz allaqachon kutilmoqda.")
        return redirect('market')

    with transaction.atomic():
        # Ball ayirish
        user.score -= item.price
        user.save(update_fields=['score'])

        # Buyurtma yaratish
        order = MarketOrder.objects.create(
            user=user, item=item, price_paid=item.price
        )

        # Stokni kamaytirish
        if item.stock > 0:
            item.stock -= 1
            item.save(update_fields=['stock'])

        # Bildirishnoma
        Notification.objects.create(
            user=user, notif_type='score',
            text=f"'{item.title}' uchun buyurtmangiz qabul qilindi! -{item.price} ball",
            link='/market/',
        )

    messages.success(request, f"Buyurtma qabul qilindi! Admin tez orada tasdiqlaydi.")
    return redirect('market')


@login_required
def my_orders(request):
    orders = MarketOrder.objects.filter(user=request.user).select_related('item')
    return render(request, 'market/orders.html', {'orders': orders})
