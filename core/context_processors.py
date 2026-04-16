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
