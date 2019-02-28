from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^submission/$', views.submission_list, name='submission_list'),
    url(r'^submission/(?P<id>[0-9]+)/$', views.submission_detail, name='submission_detail'),
    url(r'^submission/most_recent/$', views.most_recent, name='most_recent'),
    url(r'^submission/new/$', views.submission_new, name='submission_new'),
]
