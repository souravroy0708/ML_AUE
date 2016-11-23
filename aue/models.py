from django.db import models

COMMON_STATUS=(
              ('0','INACTIVE'),
              ('1','ACTIVE'),
              )

class BaseInfo(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=2,default='1',choices=COMMON_STATUS,help_text='Category Status')

    class Meta:
        abstract = True	

class Enquiry(BaseInfo):
    ip_address = models.CharField(max_length=128,null=True,blank=True,help_text='user ip address')
    url = models.TextField(null=True,blank=True,help_text='searched URL')
    goal = models.CharField(null=True,blank=True,max_length=128,help_text='User Goal')
    
    def __unicode__(self):
       return str(self.url)

class EnquiryDetails(BaseInfo):
    parent_url = models.CharField(null=True,blank=True,max_length=128,help_text='Parent URL')
    child_url = models.CharField(null=True,blank=True,max_length=128,help_text='Child URL')
    url = models.CharField(null=True,blank=True,max_length=128,help_text='URL')
    content = models.TextField(null=True,blank=True,help_text = "URL content")
    page_content = models.TextField(null=True,blank=True,help_text = "Page Content")
    
    class Meta:
      unique_together = ('parent_url','child_url','url','content')
      
    def __unicode__(self):
      return str(self.parent_url)



