def language_context(request):
    lang = request.session.get('language', 'en')
    return {'current_language': lang}
