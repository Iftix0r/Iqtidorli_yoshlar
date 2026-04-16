def csp(request):
    return {'csp_nonce': getattr(request, 'csp_nonce', '')}


def drawer_links(request):
    links = [
        ('/talents/',     'users',          'Iqtidorlar'),
        ('/leaderboard/', 'bar-chart-2',    'Reyting'),
        ('/courses/',     'graduation-cap', 'Kurslar'),
        ('/contests/',    'trophy',         'Tanlovlar'),
        ('/jobs/',        'briefcase',      'Ish O\'rinlari'),
        ('/resources/',   'book-open',      'Resurslar'),
        ('/messages/',    'message-circle', 'Xabarlar'),
    ]
    return {'drawer_links': links}


def global_chats(request):
    if not request.user.is_authenticated:
        return {'last_chats': []}
    # Faqat inbox sahifasida kerak — boshqa joylarda DB query qilmasin
    if not request.path.startswith('/messages'):
        return {'last_chats': []}
    from django.db.models import Q
    from .models import User
    user = request.user
    contacts = User.objects.filter(
        Q(sent_messages__receiver=user) |
        Q(received_messages__sender=user)
    ).distinct().exclude(pk=user.pk)[:5]
    return {'last_chats': contacts}
