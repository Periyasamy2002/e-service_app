from .models import Page

def admin_pages(request):
    """
    Provides the list of custom dynamic pages to all templates.
    This is primarily used for rendering the sidebar menu in the admin site.
    """
    # We can restrict this query to only run for admin-related paths if desired
    if request.path.startswith('/adminsite/'):
        return {'pages': Page.objects.all()}
    return {'pages': []}