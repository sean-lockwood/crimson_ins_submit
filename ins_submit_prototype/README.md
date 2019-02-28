CRDS Submission tool for INS scientists
=======================================

This site uses Django, a Python package for web development.  Django has a
bit of a learning curve, and some of the tutorials just dive in without
giving you the Big Picture of what the package is doing for you.  One of
the best explanations I've seen is in the Mozilla Django tutorial, especially
this section:
[What does Django code look like?](https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Introduction#What_does_Django_code_look_like).
Otherwise, I used tutorials by Corey Schafer, of which
[this](https://www.youtube.com/watch?v=UmljXZIypDc)
is the first.

To use the code, clone this repository and then, from the top-level directory
of the project (in which there should be a file named manage.py), type

% python manage.py runserver

This will start a simple server that is used to serve up the Django page.

In your browser, enter the URL [http://127.0.0.1:8000/submit_reference_file/](http://127.0.0.1:8000/submit_reference_file/)

This gets handled by the file ins_submit/urls.py in the first line of
urlpatterns:

    path('submit_reference_file/', include('submit_reference_file.urls')),

This delegates the URL of the SITE (ins_submit) to the APPLICATION (submit_reference_file).

We can look in the file ins_submit/submit_reference_file/urls.py to see that the path with
an empty string in the submit_reference_file application is handled by the entry 'index'
in views.py:

    from django.shortcuts import render
    
    from django.http import HttpResponse
    from django.template import loader
    
    # Create your views here.
    
    def index(request):
        template = loader.get_template('submit_reference_file/index.html')
        return HttpResponse(template.render({}, request))

This delegates the work of displaying the page to a template.  This is stored in

ins_submit/submit_reference_file/templates/submit_reference_file/index.html

This is the file that actually contains the html that gets rendered when we load this
page.

The file index.html was created by hand modeled extensively on the file

crds-server/sources/interactive/templates/batch_submit_reference_input.html

and doesn't actually do anything, but potentialy the items in double braces can get
passed to a handler routine that will live in the submit_reference_file/models.py
file.
