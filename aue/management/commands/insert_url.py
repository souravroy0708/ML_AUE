import httplib2
from BeautifulSoup import BeautifulSoup, SoupStrainer
import re
import urllib2
from fuzzywuzzy import process
import json
from pytldr.summarize.lsa import LsaSummarizer, LsaOzsoy, LsaSteinberger

from django.core.management.base import BaseCommand, CommandError
from aue.models import EnquiryDetails

import logging
logger = logging.getLogger(__name__)

#Here configure all html tag which you want replace from text
SEARCH_REPLACE_CONFIG = {'\n':' ','\t':' '}
summarizer = LsaSummarizer() 
# def replace_html(text,config = SEARCH_REPLACE_CONFIG ):
#     """
#     Replace all html tag from our content for store only text
#     """
#     replaced_text = text
#     try:
#         for item,values in config.iteritems():
#             replaced_text = text.replace(item,values)
#     except:
#         logger.exceptions("replace_html exception occur for text {0} and config {1}".format(text,config))
#     return replaced_text

def get_link(parent_url=None,input_url=None):
    """
    To get inner link of given link
    """
    return_list = []

    try:
        http = httplib2.Http()
        status, response = http.request(input_url)
    except:
        response = []
        logger.exception("get_link Invalid_Url {0} ".format(input_url))
        return response
    print "input_url --------",input_url,"--------response ----------",response
    content = ""
    for link in BeautifulSoup(response, parseOnlyThese=SoupStrainer('a')):
        try:
            content = ''.join(link.findAll(text=True))
            content = ' '.join(content.split())
        except:
            content = ''
        if link.has_key('href') or link.has_key('src'):
            url = link['href']
            try:
                summary = summarizer.summarize(url) 
                summary = ' '.join(summary) 
                if summary:
                    summary_content = str(content) +" || " + str(summary)
                else:
                    summary_content = content
                logger.info("URL --- {0} content ------ {1}  summary ------ {2} summary and content ------ {3}".format(url,content,summary,summary_content))
                content =summary_content
                
            except:
                logger.error("URL --- {0} have eror to get summarize".format(url))


            if not content:
                logger.info("URL --- {0} dont have any content. CONTENT {1}".format(url,content))
                continue

            try:
                if re.match('^http', url):
                    url = url 
                else:
                    url = "/".join([parent_url,url])

                req = urllib2.Request(url)
                try: 
                    #urllib2.urlopen(req)
                    try:
                        url = url.rstrip("/")
                        EnquiryDetails.objects.get_or_create(parent_url=parent_url,child_url=input_url,url=url,content=conten,page_content=response)
                        return_list.append(url)
                        logger.info("get_link Url_Parsed ------------------- url {0} parent_url {1} child_url {2} and content {3}".format(url,parent_url,input_url,content))
                    except:
                        logger.exception("get_link Insert_error ------------------- in EnquiryDetails for values parent_url {0} child_url {1} url {2} and content {content}".format(parent_url,input_url,url,content))
                    	
                except:
                    logger.info("get_link Invalid_Inner_Url {0} ".format(url))
            except:
                logger.info("get_link Invalid_Url_Without_Http {0} ".format(url))
        else:
            #save main page
            EnquiryDetails.objects.get_or_create(parent_url=parent_url,child_url=input_url,url=input_url,content=content,page_content=response)



    return_list = set(return_list)
    return list(return_list)

def get_search_result(input_url=None):
    """
    Function to get best possible url 
    """
    logger.info("get_search_result Now input url {0} ".format(input_url))
    link_list = get_link(input_url,input_url)
    logger.info("get_search_result First_Link_Result Total_Count {0} and List_Items {1} ".format(len(link_list),link_list))
    invalid_link_list_fianl=[]
    link_list_inner_final = []
    irrelevent_link_list = []
    already_parsed_url_list = [input_url]
    counter = 0 
    for i in link_list:
    #if i not in already_parsed_url_list or i not in invalid_link_list_fianl or irrelevent_link_list:
        counter = counter +1
        link_list_inner =[]

        try:
            logger.info("get_search_result Parsed_Url_Successfully  {0} . COUNTER {1}".format(i,counter))
            link_list_inner = get_link(input_url,i)
            already_parsed_url_list.append(i)

            # domain = input_url.split('//')[1]
            # domain_main = domain.split('.')[0]
            # serach_patern = r'\b%s\b' %(domain_main)
            # if re.search(serach_patern,i):   
            #     logger.info("get_search_result Parsed_Url_Successfully  {0} . COUNTER {1}".format(i,counter))
            #     link_list_inner = get_link(input_url,i)
            #     already_parsed_url_list.append(i)
            # else:
            #     logger.exception("get_search_result Irrelevent_Link  {0} not match with domain name {1}. COUNTER {2}".format(i,domain_main,counter))
            #     irrelevent_link_list.append(i)
            #     continue;
            #     link_list_inner=[i]
        except:
            logger.exception("get_search_result Irrelevent_Link_Exception  {0} for extract inner url. COUNTER {1}".format(i,counter))
            irrelevent_link_list.append(i)
            continue;
            link_list_inner=[i]
        if link_list_inner:
            link_list_inner_final = link_list_inner_final + link_list_inner
            link_list = link_list_inner_final
            link_list = set(link_list_inner_final)
            link_list = list(link_list)
        else:
            logger.info("get_search_result Return_Empty_List  {0} . COUNTER {1}".format(i,counter))
            invalid_link_list_fianl.append(i)
            try:
                link_list.remove(i)
                logger.info("get_search_result Return_Empty_List  {0} . COUNTER {1}".format(i,counter))
            except:
                logger.exception("get_search_result Return_Empty_List_Exception  {0} . COUNTER {1}".format(i,counter)) 
    # else:
    #     logger.info("get_search_result Already_parsed_or_invalid_link_irrelevent_link {0} ".format(i))
    # logger.info("get_search_result invalid_link_list_fianl  {0} for url {1} . COUNTER {2}".format(invalid_link_list_fianl,input_url,counter))
    # logger.info("get_search_result Return_Inner_List  {0} for url {1} . COUNTER {2}".format(link_list_inner,input_url,counter))
    # logger.info("get_search_result Total_Count of url  {0} . COUNTER {1}".format(len(link_list),counter))

    # logger.info("get_search_result irrelevent_link_list  {0} and Total_Count {1} for url {2} . COUNTER {3}".format(irrelevent_link_list,len(irrelevent_link_list),input_url,counter))
    # logger.info("get_search_result link_list_inner_final  {0} and Total_Count {1} for url {2} . COUNTER {3}".format(link_list_inner_final,len(link_list_inner_final),input_url,counter))
    # logger.info("get_search_result already_parsed_url_list  {0} and Total_Count {1} for url {2} . COUNTER {3}".format(already_parsed_url_list,len(already_parsed_url_list),input_url,counter))
    # logger.info("get_search_result link_list  {0} for url {1} . COUNTER {2}".format(link_list,input_url,counter))
    
class Command(BaseCommand):
    help = 'Insert all url of a website'

    def add_arguments(self, parser):
        parser.add_argument('input_url', nargs='+', )

    def handle(self, *args, **options):
        for input_url in options['input_url']:
    	    input_url = input_url.rstrip("/")
            logger.info("Input Url {0} ".format(input_url))
	    search_result = get_search_result(input_url)
