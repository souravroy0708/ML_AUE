"""sanchita URL Configuration

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
from django.conf.urls import patterns, include, url
from django.contrib import admin
from aue import views as aue_views
admin.site.site_header = 'Automated Usability Evaluation'
urlpatterns = [
    url(r'^admin/', admin.site.urls),   
	url(r'^get-search-result/$', aue_views.get_search_result, name='get-search-result'),
    url(r'$', aue_views.index, name='index'),   
]
