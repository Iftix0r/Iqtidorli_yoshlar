def csp(request):
    """
    Makes the CSP nonce available in the template contexts.
    """
    return {'csp_nonce': getattr(request, 'csp_nonce', '')}
