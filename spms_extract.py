# -*- coding: utf-8 -*-
"""
Runs with Python 3.5 (as part of Anaconda3-4.1.1-Windows-x86_64)
"""

from xml.etree import ElementTree
#from lxml import etree
import urllib.request
import plistlib
import sys
import datetime
import ssl
import os
import time
from xml.parsers import expat

# Set basic urls
#spms_base = 'https://oraweb.cern.ch/pls/ipac2017/'
spms_base = 'https://spms.kek.jp/pls/ibic18/'
spms_summary = spms_base + 'spms_summary.xml'
spms_session_data =  spms_base + 'xml2.session_data?sid='

# Date for conference
start_date = datetime.date(2017, 4, 29)

# empty dictionaries
authors = {}
rooms = {}
categories = {}
events = {}

## Add some static rooms
rooms["Registration"] = {
    "external_id" : "E",
    "title" : "Registration"
    }
rooms["Registration"] = {
    "external_id" : "F",
    "title" : "Meet the Editors"
    }
rooms["Registration"] = {
    "external_id" : "H",
    "title" : "Internet Café"
    }
rooms["Exhibition booths 1-100 & 137"] = {
    "external_id" : "C",
    "title" : "Exhibition booths 1-100 & 137"
    }
rooms["Exhibition booths 101-"] = {
    "external_id" : "D",
    "title" : "Exhibition booths 101-"
    }

# ** MAIN SCRIPT - No need to modify beyond this point ** 

# download summary to iterate through sessions
# Encoding says its Latin-1 in all XML, but in fact its UTF-8
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.urlopen(spms_summary, context=ctx)
filename = './sessions/spms_summary.xml'
try:
    st=os.stat(filename)    
    mtime=st.st_mtime
    age = time.time() - mtime
except:
    print("No cache file found, setting up")
    age = 601
if age > 600:
    f = open(filename,'wb')
    try:
        data = req.read().decode('utf-8')
    except:
        print("UTF-8 encoding failed, trying generic")
        data = req.read()
        pass
    f.write(data.encode('utf-8'))
    f.close()
    conference_element = ElementTree.fromstring(data)
else:
    f = open(filename,'rb')
    print(filename)
    data = f.read()
    conference_element = ElementTree.XML(data)
    f.close()

#parser = etree.XMLParser(recover=True)        
#conference_element = etree.fromstring(data, parser=parser)
#conference_element = ElementTree.fromstring(data)

# iterate through sessions
for session_element in conference_element:
    session_type = session_element.attrib['type']
    session_name_element = session_element.find('name')
    session_abbr = session_name_element.attrib['abbr']
    session_name = session_name_element.text
    
    # download session data
    print ("Working on session", session_abbr, session_type, session_name)
    if session_abbr == "SUSPF":
        print("Damaged xml exiting")
        continue
    req = urllib.request.urlopen(spms_session_data + session_abbr, context=ctx)
    #data = req.read().decode('utf-8')
    data = req.read()
    session_data_element = ElementTree.fromstring(data)
    
    session_time_element = session_data_element.find(".//date")
    session_time_btime = session_time_element.attrib['btime']
    session_time_btime = session_time_btime[:2]+'.'+session_time_btime[2:]
    session_time_etime = session_time_element.attrib['etime']
    session_time_etime = session_time_etime[:2]+'.'+session_time_etime[2:]
    seq = session_time_btime, session_time_etime
    session_time = "-".join(seq)
    date = session_data_element.find(".//date").text
    day = datetime.datetime.strptime(date, '%d-%b-%y').date()
    delta = day - start_date
    
    # Parse chairs
    chair_elements = session_data_element.findall(".//chairs/chair")
    for chair_element in chair_elements:
                author_id = chair_element.find(".//author_id").text
                fname = chair_element.find(".//fname").text
                lname = chair_element.find(".//lname").text
                #print(fname, lname)
                try:
                    city = chair_element.find(".//institutions/institute/full_name[@abbrev]").attrib['abbrev']
                except:
                    city = ""
                    pass
                institution =  chair_element.find(".//institutions/institute/full_name").text
                authors[author_id] = {
                    "external_id" : author_id,
                    "first" : fname,
                    "last" : lname,
                    "city" : city,
                    "institution" : institution
                }
    
    # Parse rooms
    location = session_data_element.find(".//location").text    
    rooms[location] = {
    "external_id" : location,
    "title" : location
    }
       
        
    #Figure out if this is a block session for posters or contributed or invited orals    
    paper_elements = session_data_element.findall(".//paper")
    if len(paper_elements) == 0:
        print ("No paper in session, will skip for now")
        events[session_abbr] = {
            "title" : session_name,
            "time" : session_time,
            "scheme_detail" : delta.days,
            #"room_id" : location,
            "type" : "Annat",
            #"external_id" : session_abbr,
            #"moderators_array" : list(map(lambda x: { "id" : x.find(".//author_id").text}, chair_elements))
        }        
    if len(paper_elements) == 1:
        print ("Only one paper in session, assuming its an invited")
        for paper_element in paper_elements:
            # parse authors
            coordinator_elements = paper_element.findall(".//coordinator")
            author_elements = paper_element.findall(".//contributor[@type='Primary Author']")
            speaker_elements = paper_element.findall(".//contributor[@type='Speaker']")
            coauthor_elements = paper_element.findall(".//contributor[@type='Co-Author']")
            allauthor_elements = coordinator_elements + author_elements + coauthor_elements
            paper_class = paper_element.find(".//main_class").text
            
            abstract = paper_element.find(".//abstract").text
            
            for author_element in allauthor_elements:
                author_id = author_element.find(".//author_id").text
                fname = author_element.find(".//fname").text
                lname = author_element.find(".//lname").text
                try:
                    city = author_element.find(".//institutions/institute/full_name[@abbrev]").attrib['abbrev']
                except:
                    #print(fname + " " + lname + " - No Abbreviation for institute available, setting string to null")
                    city = ""
                    pass
                institution =  author_element.find(".//institutions/institute/full_name").text
                    
                if not author_id in authors:
                    authors[author_id] = {
                        "external_id" : author_id,
                        "first" : fname,
                        "last" : lname,
                        "city" : city,
                        "institution" : institution
                        #"guest_speaker" : speaker
                    } 
                
            for speaker_element in speaker_elements:
                #print ("Found a speaker")
                author_id = speaker_element.find(".//author_id").text
                fname = speaker_element.find(".//fname").text
                lname = speaker_element.find(".//lname").text
                try:    
                    city = speaker_element.find(".//institutions/institute/full_name[@abbrev]").attrib['abbrev']
                except:
                    #print(fname + " "+ lname + " - No Abbreviation for institute available, setting string to null")
                    city = ""
                    pass
                institution = speaker_element.find(".//institutions/institute/full_name").text
                speaker = True

                authors[author_id] = {
                    "external_id" : author_id,
                    "first" : fname,
                    "last" : lname,
                    "city" : city,
                    "institution" : institution,
                    "guest_speaker" : speaker
                }
 
            # parse categories
            presentation_element = paper_element.find(".//code[@primary='Y']/../presentation")
            presentation_type = presentation_element.attrib['type']
            presentation_type_text = presentation_element.text
            #print (presentation_type_text)
            ptype = "notset"
            if presentation_type_text == "Contributed Oral":
                ptype = "FF"
            if presentation_type_text == "Invited Oral":
                ptype = "SY"
                paper_start = paper_element.find(".//code[@primary='Y']/../start_time").text
                paper_start_time = datetime.datetime.strptime(paper_start, '%H%M').time()
                tmp_datetime = datetime.datetime.combine(datetime.date(1, 1, 1), paper_start_time)
                paper_duration = paper_element.find(".//code[@primary='Y']/../duration").text
                timedelta = datetime.timedelta(minutes=int(paper_duration))
                talk_end = (tmp_datetime + timedelta).time()
                time_slot = str((paper_start_time.strftime("%H.%M"))) + '-' + str((talk_end.strftime("%H.%M")))
            if presentation_type_text == "Poster":
                ptype = "PU"
            
            # this needs to be change to reflect the MAIN CLASSIFICATIONS
            categories[paper_class] = {
                "external_id" : paper_class[:2],   
                "title" : paper_class[3:]
                
            }
                        
            # parse event (paper) details
            paper_code = paper_element.find(".//code[@primary='Y']").text
            paper_title = paper_element.find(".//title").text
            try:
                paper_start_time = paper_element.find(".//code[@primary='Y']/../start_time").text
            except:
                pass

            events[paper_code] = {
                "title" : paper_code + " - " + paper_title,
                "time" : time_slot,
                "scheme_detail" : delta.days,
                "room_id" : location,
                "type" : ptype,
                "category_array" : [{ "id" : paper_class[:2]}],    
                #"category_array" : [paper_class[:2]],
                "e_info" : presentation_type_text,
                #"external_block_id" : session_abbr,
                "authors_array" : list(map(lambda x: { "id" : x.find(".//author_id").text}, author_elements)),
                "co_authors_array" : list(map(lambda x: { "id" : x.find(".//author_id").text}, coauthor_elements)),
                "moderators_array" : list(map(lambda x: { "id" : x.find(".//author_id").text}, chair_elements)),
                "abstract_url" : "/" + paper_code + ".html",
                "external_id" : paper_code
            }
                        
            #Abstract file generation
            now = datetime.datetime.today().strftime("%Y%m%d-%H%M%S")

            filename = './abstracts/' + paper_code + '.html'
            f = open(filename,'wb')
            wrapper = """<!DOCTYPE html>
            <html lang="en">
             <head> 
              <meta http-equiv="X-UA-Compatible" content="IE=Edge,chrome=1" /> 
              <meta charset="UTF-8" /> 
              <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /> 
              <meta name="viewport" content="width=device-width, initial-scale=1.0" /> 
              <title>Preview</title> 
              <style>
                #table {
                    margin-left: auto;
                    margin-right: auto;
                }

                span {
                    padding-left: 0px;
                }

                p {
                    font-size: 10pt;
                }

                body {
                    font-family: -apple-system, Roboto, Arial;
                }

            </style> 
             </head> 
             <body id="body">    
              <div id="main_div"> 
               <h2 id="title">%s - %s</h2> 
               <p></p> 
               <h4>Abstract</h4> 
               <p id="abstract">%s</p> 
               <p></p> 
              </div>
             </body>
            </html>"""
   
            whole = wrapper % (paper_code, paper_title, abstract)
            f.write(whole.encode('utf-8'))
            f.close()
            
    if len(paper_elements) > 1:
        #reset caegory var
        #print("Resetting category arrays")
        cat = []
        print ("More than one paper in session")
        for paper_element in paper_elements:
            time_slot = ""
            # parse authors
            #coordinator_elements = session_element.findall(".//chair")
            author_elements = paper_element.findall(".//contributor[@type='Primary Author']")
            coauthor_elements = paper_element.findall(".//contributor[@type='Co-Author']")
            speaker_elements = paper_element.findall(".//contributor[@type='Speaker']")
            
            
            allauthor_elements = author_elements + coauthor_elements
            paper_class = paper_element.find(".//main_class").text
            abstract = paper_element.find(".//abstract").text
            
            #try:
            #    speaker_elements = paper_element.findall(".//contributor[@type='Speaker']")
            #except:                
            #    pass
            #if speaker_elements:
            #if paper_element.findall(".//contributor[@type='Speaker']"):
            #    speaker = True
            #else:
            #    speaker = False
            
            
            for author_element in allauthor_elements:
                author_id = author_element.find(".//author_id").text
                fname = author_element.find(".//fname").text
                lname = author_element.find(".//lname").text
                try:
                    #city = author_element.find(".//institutions/institute/town").text
                    city = author_element.find(".//institutions/institute/full_name[@abbrev]").attrib['abbrev']
                except:
                    #print(fname + " "+ lname + " - No Abbreviation for institute available, setting string to null")
                    city = ""
                    pass
                
                
                institution =  author_element.find(".//institutions/institute/full_name").text
                if not author_id in authors:
                    authors[author_id] = {
                        "external_id" : author_id,
                        "first" : fname,
                        "last" : lname,
                        "city" : city,
                        "institution" : institution
                        #"guest_speaker" : speaker
                    } 

            for speaker_element in speaker_elements:
                #print ("Found a speaker")
                author_id = speaker_element.find(".//author_id").text
                fname = speaker_element.find(".//fname").text
                lname = speaker_element.find(".//lname").text
                try:    
                    city = speaker_element.find(".//institutions/institute/full_name[@abbrev]").attrib['abbrev']
                except:
                    #print(fname + " "+ lname + " - No Abbreviation for institute available, setting string to null")
                    city = ""
                    pass
                institution = speaker_element.find(".//institutions/institute/full_name").text
                speaker = True

                authors[author_id] = {
                    "external_id" : author_id,
                    "first" : fname,
                    "last" : lname,
                    "city" : city,
                    "institution" : institution,
                    "guest_speaker" : speaker
                }
                
            # parse categories
            presentation_element = paper_element.find(".//code[@primary='Y']/../presentation")
            presentation_type = presentation_element.attrib['type']
            presentation_type_text = presentation_element.text
            
           
            
            if session_abbr == "SUSPSIK":
                presentation_element = paper_element.find(".//code[@primary='N']/../presentation")
                presentation_type = presentation_element.attrib['type']
                presentation_type_text = presentation_element.text
                
            
            ptype = "notset"
            if presentation_type_text.strip() == "Contributed Oral":
                ptype = "FF"
                paper_start = paper_element.find(".//code[@primary='Y']/../start_time").text
                paper_start_time = datetime.datetime.strptime(paper_start, '%H%M').time()
                tmp_datetime = datetime.datetime.combine(datetime.date(1, 1, 1), paper_start_time)
                paper_duration = paper_element.find(".//code[@primary='Y']/../duration").text
                timedelta = datetime.timedelta(minutes=int(paper_duration))
                talk_end = (tmp_datetime + timedelta).time()
                time_slot = str((paper_start_time.strftime("%H.%M"))) + '-' + str((talk_end.strftime("%H.%M")))
                #print("Contributed oral - setting category array")
                cat = [{ "id" : paper_class[:2]}]
                
            elif presentation_type_text == "Invited Oral":
                ptype = "FF"
                paper_start = paper_element.find(".//code[@primary='Y']/../start_time").text
                paper_start_time = datetime.datetime.strptime(paper_start, '%H%M').time()
                tmp_datetime = datetime.datetime.combine(datetime.date(1, 1, 1), paper_start_time)
                paper_duration = paper_element.find(".//code[@primary='Y']/../duration").text
                timedelta = datetime.timedelta(minutes=int(paper_duration))
                talk_end = (tmp_datetime + timedelta).time()
                time_slot = str((paper_start_time.strftime("%H.%M"))) + '-' + str((talk_end.strftime("%H.%M")))
                #print("Invited oral - setting category array")
                cat = [{ "id" : paper_class[:2]}]
                
            elif presentation_type_text == "Poster":
                ptype = "PU"            

            # Reflects the MAIN CLASSIFICATIONS, we should have sub as well
            categories[paper_class] = {
                "external_id" : paper_class[:2],   
                "title" : paper_class[3:]
                
            }
            
            # parse event (paper) details
            paper_code = paper_element.find(".//code[@primary='Y']").text
            paper_title = paper_element.find(".//title").text
            
            if time_slot == "":
                time_slot = session_time
                
            if session_abbr == "SUSPSIK":
                paper_scode = paper_element.find(".//code[@primary='N']").text
                paper_code = paper_scode
                presentation_element = paper_element.find(".//code[@primary='N']/../presentation")
                presentation_type = presentation_element.attrib['type']
                presentation_type_text = presentation_element.text
                #print("Suspik paper type:" + paper_code + " - " + ptype)
            
            events[paper_code] = {
                "title" : paper_code + " - " + paper_title,
                "time" : time_slot,
                "scheme_detail" : delta.days,
                "room_id" : location,
                "type" : ptype,
                "category_array" : [{ "id" : paper_class[:2]}],
                "e_info" : presentation_type_text,
                "external_block_id" : session_abbr,
                "authors_array" : list(map(lambda x: { "id" : x.find(".//author_id").text}, author_elements)),
                "co_authors_array" : list(map(lambda x: { "id" : x.find(".//author_id").text}, coauthor_elements)),
                #"moderators_array" : list(map(lambda x: { "id" : x.find(".//author_id").text}, chair_elements)),
                "abstract_url" : "/" + paper_code + ".html",
                "external_id" : paper_code
            }
            
            #Abstract file generation
            now = datetime.datetime.today().strftime("%Y%m%d-%H%M%S")

            filename = './abstracts/' + paper_code + '.html'
            f = open(filename,'wb')
            wrapper = """<!DOCTYPE html>
            <html lang="en">
             <head> 
              <meta http-equiv="X-UA-Compatible" content="IE=Edge,chrome=1" /> 
              <meta charset="UTF-8" /> 
              <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /> 
              <meta name="viewport" content="width=device-width, initial-scale=1.0" /> 
              <title>Preview</title> 
              <style>
                #table {
                    margin-left: auto;
                    margin-right: auto;
                }

                span {
                    padding-left: 0px;
                }

                p {
                    font-size: 10pt;
                }

                body {
                    font-family: -apple-system, Roboto, Arial;
                }

            </style> 
             </head> 
             <body id="body">    
              <div id="main_div"> 
               <h2 id="title">%s - %s</h2> 
               <p></p> 
               <h4>Abstract</h4> 
               <p id="abstract">%s</p> 
               <p></p> 
              </div>
             </body>
            </html>""" 
   
            whole = wrapper % (paper_code, paper_title, abstract)
            f.write(whole.encode('utf-8'))
            f.close()
             
            
        #print (cat)
        events[session_abbr] = {
            "title" : session_name,
            "time" : session_time,
            "scheme_detail" : delta.days,
            "room_id" : location,
            "type" : "BLOCK",
            "external_id" : session_abbr,
            "category_array" : cat,
            "moderators_array" : list(map(lambda x: { "id" : x.find(".//author_id").text}, chair_elements))
        }
config = {
    "Rooms" : list(map(lambda key : rooms.get(key), rooms)),
    "Categories" : list(map(lambda key : categories.get(key), categories)),
    "Authors" : list(map(lambda key : authors.get(key), authors))
 }

scheme = list(map(lambda key : events.get(key), events))

with open("config.plist", 'wb') as fp:
    
    plistlib.dump(config, fp)
    
with open("scheme.plist", 'wb') as fp:
    plistlib.dump(scheme, fp)
            
            
#            paper_code = paper_element.find(".//code[@primary='Y']").text
#            presentation_element = paper_element.find(".//code[@primary='Y']/../presentation")
#            presentation_type = presentation_element.attrib['type']
#            if presentation_type != 'Oral':
#                continue
#            paper_title = paper_element.find(".//title").text
#            print ("  Paper ", paper_code, presentation_type, paper_title)
      
#scheme.plist
#  title - Titel på eventet, som en sträng. <string>
#  time - Tid på dagen för eventet hh:mm-hh:mm, som en sträng. <string>
#  scheme_detail - dagen för eventet, som ett nummer. Startar kongressen 2017-03-14 så refererar 0 till 2017-03-14, 1 till 2017-03-15 osv. <integer>
#  room_id - platsen för eventet, ett id som refererar till platsen i config.plist <string>#
#  type - vilken typ av event. (Finns specificerat längre ner) <string>
# category_array - array med id som refererar till kategorierna i config.plist <array>
#  e_info - extra information, som en sträng. Stödjer html-taggar. <string>
#  authors_array, co_authors_array, moderators_array - array med id som refererar till personer (se Authors nedan) <array>
#  abstract_url - Absolut URL till html- eller pdf-dokument, som en sträng. <string>
#  external_block_id - referens till ert interna id om programpunkten är underordnad en annan programpunkt t.ex. fria föredrag. Som en sträng. <string>
#  external_id - ert interna id, som en sträng. <string>      

      
#config.plist
# external_id - author_id
#  first - fname
#  last - lname
#  city - institutions.institute.town
#  institution - institutions.institute.full_name.text

#Rooms <dictionary>
#  external_id - location.text
#  title - location.text

#Categories <dictionary>
#  id - papers.paper.program_codes.program_code.presentation.type
#  title - papers.paper.program_codes.program_code.presentation.text



