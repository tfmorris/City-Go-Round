import time
import logging
from google.appengine.ext import db

from ..forms import AddAppForm
from ..utils.view import render_to_response, redirect_to, not_implemented, render_image_response, redirect_to_url
from ..utils.image import crop_and_resize_image_to_square
from ..utils.transitapp import requires_valid_slug
from ..models import TransitApp, TransitAppStats
from ..constants import TRANSIT_APP_IMAGE_WIDTH, TRANSIT_APP_IMAGE_HEIGHT

def gallery(request):    
    template_vars = {
        'transit_app_count': TransitAppStats.get_transit_app_count(),
        'transit_apps': TransitApp.all().fetch(10), # TODO DAVEPECK: replace with something better
    }
        
    return render_to_response(request, 'app/gallery.html', template_vars)
    
@requires_valid_slug
def details(request, transit_app):
    template_vars = {
        'transit_app': transit_app,
    }    
    return render_to_response(request, 'app/details.html', template_vars)
    
@requires_valid_slug
def screenshot(request, transit_app):
    if transit_app.has_screen_shot:
        return render_image_response(request, transit_app.screen_shot)
    return redirect_to_url("/images/default-transit-app.png")

def add_form(request):
    # TODO davepeck
    if request.method == 'POST':
        form = AddAppForm(request.POST, request.FILES)
        if form.is_valid():         
            application = TransitApp()            
            application.slug = form.transit_app_slug
            application.title = form.cleaned_data['title']
            application.description = form.cleaned_data['description']
            application.url = db.Link(form.cleaned_data['url'])
            application.author_name = form.cleaned_data['author_name']
            application.author_email = db.Email(form.cleaned_data['author_email'])
            application.long_description = db.Text(form.cleaned_data['long_description'])
            application.tags = form.tag_list
            application.screen_shot = None
            
            # Process the image, resizing if necessary, and failing silently if something goes wrong.
            screen_shot_file = request.FILES.get('screen_shot', None)
            if screen_shot_file:
                screen_shot_bytes = crop_and_resize_image_to_square(screen_shot_file.read(), TRANSIT_APP_IMAGE_WIDTH, TRANSIT_APP_IMAGE_HEIGHT)
                if screen_shot_bytes:
                    application.screen_shot = db.Blob(screen_shot_bytes)
                    
            # Store it in the database
            try:
                application.put()
            except db.TimeoutException:
                application.put()
                
            # Increment our counter
            TransitAppStats.increment_transit_app_count()
            
            # Done!
            return redirect_to('apps_add_success')
    else:
        form = AddAppForm()        
    return render_to_response(request, 'app/add-form.html', {'form': form})
    
def add_success(request):
    return render_to_response(request, 'app/add-success.html')
