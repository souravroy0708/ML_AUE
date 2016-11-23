from __future__ import division
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core import urlresolvers
from django.contrib import messages
from django.contrib.auth import authenticate, login as login_auth,logout
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
import httplib2
from BeautifulSoup import BeautifulSoup, SoupStrainer
import re
import urllib2
from fuzzywuzzy import process
import socket
import json
from datetime import datetime, timedelta,date
from aue.models import Enquiry,EnquiryDetails
from fuzzywuzzy import fuzz
import mechanize
import operator
import numpy
from pytldr.summarize.lsa import LsaSummarizer, LsaOzsoy, LsaSteinberger
summarizer = LsaSummarizer() 
import logging
logger = logging.getLogger(__name__)

def index(request):
    """
    Automated Usability Evaluation index page
    """
    #Total number of record to be display in search result
    no_record_count = [1,2,3,4]
    return render(request, 'aue/index.html', {"no_record_count":no_record_count})

#Here configure all html tag which you want replace from text
SEARCH_REPLACE_CONFIG = {'\n':' ','\t':' '}

def replace_html(text,config = SEARCH_REPLACE_CONFIG ):
    """
    Replace all html tag from our content for store only text
    """
    replaced_text = text
    try:
        for item,values in config.iteritems():
            replaced_text = text.replace(item,values)
    except:
        logger.exceptions("replace_html exception occur for TEXT --- {0} and CONFIG --- {1}".format(text,config))
    return replaced_text

def get_link(input_url=None):
    """
    To get inner link of given link
    """
    input_url = str(input_url)
    return_list = {}
    url_list = [] #contains all url list
    url_dict = {} #contains url and  key value pairs EX: {"http://vlabs.ac.in/index.html#aboutus","ABOUT"}
    try:
        http = httplib2.Http()
        status, response = http.request(input_url)
    except:
        response = []
        logger.exception("Invalid URL --- .".format(input_url))
        return response

    for link in BeautifulSoup(response, parseOnlyThese=SoupStrainer('a')):
        #Filter only link from web page(Given search url)
        try:
            content = ''.join(link.findAll(text=True))
            content = replace_html(content)
            content = ' '.join(content.split())
        except:
            content = ''
        
        if link.has_key('href'):
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
                    #In relative url add base url
                    url = "/".join([input_url,url])
                
                try: 
                    url = url.rstrip("/")
                    req = urllib2.Request(url)
                    urllib2.urlopen(req)
                    url_list.append(url)
                    url_dict[url] = content
                    logger.info("get_link Valid_Url URL --- {0} and CONTENT --- {1}".format(url,content))
                except:
                    logger.info("get_link Not_Valid_Url URL --- {0} and CONTENT --- {1}".format(url,content))  
                
            except:
                logger.exception("get_link Invalid_Url URL --- ".format(url))
    url_list = set(url_list)
    return_list['url_list'] = list(url_list)
    return_list['url_dict'] = url_dict
    return return_list

def get_lsa_matrix(goal_keyword_list,lsa_input_link_content):
    """get LSA matrix using numy"""
    keyword_length = len(goal_keyword_list)
    content_length = len(lsa_input_link_content)
    lsa_matrix = numpy.zeros((keyword_length, content_length))
    for i,keyword in enumerate(goal_keyword_list):
        for j,content in enumerate(lsa_input_link_content):
            word_present_count = content.lower().count(keyword.lower()) # computing goal_keyword_list frequencies
            try: 
                word_frequency = word_present_count/len(content.split())
            except:
                word_frequency = word_present_count

            lsa_matrix[i,j] = word_frequency

    for i in range(content_length): # normalize columns
        try:
            val = lsa_matrix[:keyword_length,i]/numpy.linalg.norm(lsa_matrix[:keyword_length,i])
        except:
            val = 0
            lsa_matrix[:keyword_length,i] = val

    return lsa_matrix

def get_lsa_score(lsa_matrix,numpy_query_input,link_choice_dict):
    """ make the query and print the result """
    logger.info("Inside LSA QUERY: LSA matrix {0}  with link choce {1}".format(lsa_matrix,link_choice_dict))
    numpy_query_input = numpy_query_input/numpy.linalg.norm(numpy_query_input) # normalize query vector
    lsa_score_result = {}
    for i,link in enumerate(link_choice_dict):
        lsa_score = numpy.dot(lsa_matrix[:len(numpy_query_input),i].T,numpy_query_input)
        content = link_choice_dict[link]
        lsa_score_result[link] = lsa_score
        print 'content:',content,'\n-LSA Score:',lsa_score

    return lsa_score_result
def get_list_from_dictonary(link_choice_dict=None,content=None):
    """
    get list of url for a particular content
    """
    url_list = []
    try:
        for item,values in link_choice_dict.iteritems():
            if values == content:
                item = item.strip()
                item = item.rstrip("/")
                url_list.append(str(item))
    except:
        logger.exceptions("get_list_from_dictonary Exception for CHOICE_DICTIONARY ---  {0} and CONTENT ---  {1} ".format(link_choice_dict,content))

    return url_list

def get_filter_link(link_choice_dict,goal=None,min_score=None,max_limit=4,type=0):
    """
    To get relevent link from list of link
    """
    if min_score:
        min_score = int(min_score)
    else:
        min_score = 50
    scored_link_list = []
    link_choice = link_choice_dict.values()
    scored_link_list_raw = process.extract(goal,link_choice,limit=max_limit)
    logger.info("STEP 3 : ------ FuzzyWuzzy Score details for GOAL ---  {0} with STATISTICS --- {1}".format(goal,scored_link_list_raw))
    try:
        if scored_link_list_raw:
            for i in list(scored_link_list_raw):
                link = i[0]
                if int(type) != 1:
                    score = i[1]
                    if int(score) >= min_score:
                        # link = link_choice_dict[link]
                        link_list = get_list_from_dictonary(link_choice_dict,link)
                        scored_link_list = scored_link_list + link_list
                    logger.info("PARTIAL : Final score is {0} of url list {1}  for goal {2} and url content {3}".format(score,link_list,goal,link))
                else:
                    score = fuzz.token_set_ratio(goal,link)
                    # if int(score) >= min_score:
                    link_list = get_list_from_dictonary(link_choice_dict,link)
                    scored_link_list = scored_link_list + link_list
                    logger.info("EXACT : Final score is {0} of url list {1}  for goal {2} and url content {3}".format(score,link_list,goal,link))
    except:
        logger.exception("Error occure in get_filter_link() function")
    scored_link_list = set(scored_link_list)
    scored_link_list = list(scored_link_list)
    lsa_input_link_list = link_choice_dict.keys()
    lsa_input_link_content = link_choice_dict.values()

    #LSA IMPLEMENTATION
    goal_keyword_list = goal.split()
    lsa_matrix = get_lsa_matrix(goal_keyword_list,lsa_input_link_content) 
    array_input = [1 for i in goal_keyword_list]
    numpy_query_input = numpy.array(array_input)
    lsa_score = get_lsa_score(lsa_matrix,numpy_query_input,link_choice_dict)
    sorted_lsa_score = sorted(lsa_score.items(), key=operator.itemgetter(1),reverse=True)
    lsa_link_list = [ lsa_link[0] for lsa_link in  sorted_lsa_score]
    logger.info("STEP 4 : ------ LSA Score details {0} ".format(sorted_lsa_score))
    #return scored_link_list
    return lsa_link_list


def get_search_result(request):
    """
    Function to get best possible url 
    """
    
    type = request.POST.get("type",0)
    min_score = request.POST.get("min_score",50)
    input_url = request.POST.get("input_url","")
    #Remove end slash for use search url as base url
    input_url = input_url.rstrip("/")
    input_goal = request.POST.get("input_goal","")
    #To get IP address of system
    try:
    	ip_address = socket.gethostbyname(socket.gethostname())
    except:
    	ip_address = ""
        logger.exception("Error in get system ip address")
    if input_url and input_goal:
    	try:
    		Enquiry.objects.create(ip_address=ip_address,url=input_url,goal=input_goal)    	
    	except:
            logger.exception("Error in insert enquiry data")

    logger.info("STEP 1 : ------ IP address {0} has searched URL {1} with GOAL {2}".format(ip_address,input_url,input_goal))
    #ALREADY STORED LINK    
    EXIST_URL = EnquiryDetails.objects.filter( (Q(parent_url__icontains=input_url) | Q(child_url__icontains=input_url) | Q(url__icontains=input_url)) , (Q(content__icontains=input_goal) |  Q(url__icontains=input_goal)) ).values_list('url','content').distinct()
    # EXIST_URL_dummy = EnquiryDetails.objects.all()[:10].values_list('url','content')
    # EXIST_URL = list(EXIST_URL) + list(EXIST_URL_dummy)
    logger.info("STEP 2 : ------  EXIST_URL List From DATA BASE --- {0} for URL --- {1} --- GOAL --- {2}".format(EXIST_URL,input_url,input_goal))
    EXIST_URL_LIST = []
    EXIST_URL_DICT = {}
    for url in EXIST_URL:
        if url[0] not in EXIST_URL_LIST:
            EXIST_URL_LIST.append(url[0])
            EXIST_URL_DICT[url[0]] = url[1]
    # if input_url in EXIST_URL_LIST and len(EXIST_URL_LIST) > 100:
    #PARSED_URL_LIST = ['http://vlabs.ac.in']
    PARSED_URL_LIST = ['http://vlabs.ac.in']
    if input_url in EXIST_URL_LIST or input_url in PARSED_URL_LIST:
        # link_list = EXIST_URL_LIST
        link_dict = EXIST_URL_DICT
    else:
        link_list_result = get_link(input_url)
        link_list = link_list_result["url_list"]
        link_dict = link_list_result["url_dict"]
        link_list = get_filter_link(link_dict,input_goal,30,9,1)
        invalid_link_list_fianl=[]
        # link_list = [] #For testing
        counter = 0
        for i in link_list:
            counter = counter +1
            invalid_link_list=[]
            link_list_inner = []
            irrelevent_link_list = []
            already_parsed_url_list = [input_url]
            if (i not in already_parsed_url_list or i not in invalid_link_list_fianl or irrelevent_link_list) and(len(link_list) <= 30 and counter <= 9):
                # link_list_inner_result = get_link(i)
                # link_list_inner = link_list_inner_result["url_list"]
                # link_dict.update(link_list_inner_result["url_dict"])
                try:
                    domain = input_url.split('//')[1]
                    domain_main = domain.split('.')[0]
                    serach_patern = r'\b%s\b' %(domain_main)
                    if re.search(serach_patern,i):   
                        logger.info("get_search_result Parsed_Url_Successfully  {0} . COUNTER {1}".format(i,counter))
                        link_list_inner_result = get_link(i)
                        link_list_inner = link_list_inner_result["url_list"]
                        link_dict.update(link_list_inner_result["url_dict"])
                        already_parsed_url_list.append(i)
                    else:
                        logger.exception("get_search_result Irrelevent_Link  {0} not match with domain name {1}. COUNTER {2}".format(i,domain_main,counter))
                        irrelevent_link_list.append(i)
                        continue;
                        link_list_inner=[i]
                except:
                    logger.exception("get_search_result Irrelevent_Link_Exception  {0} for extract inner url. COUNTER {1}".format(i,counter))
                    irrelevent_link_list.append(i)
                    continue;
                    link_list_inner=[i]
            else:
                logger.info("URL {0} not fulfill parse criteria".format(i))
            if link_list_inner:
                link_list_inner = get_filter_link(link_dict,input_goal,50,5,1)
                link_list = link_list+link_list_inner
            else:
                invalid_link_list.append(i)
                invalid_link_list_fianl=invalid_link_list_fianl+invalid_link_list
                link_list.remove(i)
            
    final_scored_link_list = get_filter_link(link_dict,input_goal,min_score,10,1)
    
    return_object = {"search_result":final_scored_link_list}
    return HttpResponse(json.dumps(return_object),
            content_type="application/json")
