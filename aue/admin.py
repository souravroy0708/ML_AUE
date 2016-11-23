from django.contrib import admin
from aue.models import Enquiry,EnquiryDetails

class EnquiryAdmin(admin.ModelAdmin):
    list_display = ('goal','url','ip_address','created_date')
    search_fields = ['ip_address','url','goal']
    list_filter = ('ip_address','url','goal')
admin.site.register(Enquiry,EnquiryAdmin)

class EnquiryDetailsAdmin(admin.ModelAdmin):
    list_display = ('content','url','parent_url','child_url','page_content')
    search_fields = ['url','content']
    list_filter = ('parent_url','child_url','page_content')
admin.site.register(EnquiryDetails,EnquiryDetailsAdmin)