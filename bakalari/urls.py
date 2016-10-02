"""SchoolTools URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include

from bakalari import newsfeed
from bakalari import views

urlpatterns = [
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^dashboard/content$', views.dashboard_content, name='dashboard_content'),
    url(r'^subject/content/(?P<subject_name>([-\w]+))$', views.subject_content, name='subject_content'),
    url(r'^subject/(?P<subject_name>([-\w]+))$', views.subject, name='subject'),
    url(r'^feed', newsfeed.RSSFeed(), name='feed'),
    url(r'^notifications$', views.notifications, name='notifications'),
    url(r'^register_pushbullet$', views.notifications_register_pushbullet, name='register_pushbullet'),
    url(r'^privacy_policy$', views.privacy_policy, name='privacy_policy'),
    url(r'^login.aspx$', views.baka_proxy),
    url(r'^', views.index, name='index'),
]
