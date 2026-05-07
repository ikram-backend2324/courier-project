class LanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'lang' in request.GET:
            lang = request.GET['lang']
            if lang in ['en', 'ru', 'uz']:
                request.session['language'] = lang
        if 'language' not in request.session:
            request.session['language'] = 'en'
        return self.get_response(request)
