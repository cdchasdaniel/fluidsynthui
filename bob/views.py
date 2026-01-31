from django.shortcuts import render


def home(request):
    """Render the home page with site description."""
    return render(request, 'home.html')
