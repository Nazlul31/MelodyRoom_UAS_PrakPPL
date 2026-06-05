def nav_context(request):
    return {
        'current_path': request.path,
    }
