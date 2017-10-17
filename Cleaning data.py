#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 22 22:34:11 2017

@author: fadhel.h
"""
import xml.etree.ElementTree as ET
import re
from collections import defaultdict


inputfile = 'CincinnatiRaw.xml' # The original file that will be cleaned 
finalfile = 'Cincinnati.xml'   # The updated file that will be used in the SQL
tree =  ET.ElementTree(file=inputfile)
root = tree.getroot()
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

# The list of expected road types (already updated)
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons","Plaza","Hill",'Ludlow','Way','Circle','Warner']

# The dict. that will update the road names to full names.(already updated)
mapping = { "St": "Street",
            'Ave': "Avenue",
            "avenue":"Avenue",
            'Rd.':'Road'
            }

# The function that will relpace the undesired part of the street name using the mapping dict.
def update_name(name, mapping):
    for k, v in mapping.iteritems():
        for word in name.split():
            if word == k:
                name = name.replace(k,v,1)
                break
    return name 

# The function that will check if the street is in the expected list or not.
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)
            return True
        else:
            return False
            
# The function that check if the key corresponds to a zip code or not.      
def is_postcode(elem):
    return(elem.attrib['k'] == "addr:postcode")

# The function that check if the key corresponds to a street or not.      
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

# The fucntion that will fix the problems
def fix(filename):
    street_types = defaultdict(set)
    street_names = []
    zip_codes = set()
    cleaned_dict = {}
    for elem in root:
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):    # check it is a street
                   if audit_street_type(street_types, tag.attrib['v']):  # check if it is has undesired charecters
                       street_names.append(tag.attrib['v'])
                       tag.set('v',update_name(tag.attrib['v'], mapping))  # then update the undesired value by a value from mapping
                elif is_postcode(tag):
                    if len(tag.attrib['v']) !=5:
                        zip_codes.add(tag.attrib['v'])
                    tag.set('v', tag.attrib['v'][0:5])   # if yes, then get the first 5 numbers only. Because for this particular data, if I get the first 5 numbers it will be the correct zip code.
    cleaned_dict["Zip codes"]=zip_codes
    cleaned_dict["Street names"]=street_names
# Then write a new XML file with the updaetd nodes.
    tree = ET.ElementTree(root)                  
    with open("Cincinnati.xml", "w") as f:
        tree.write(f)
    return street_types, cleaned_dict
st_types, cl_dict = fix(inputfile)

# To see what we have dealt with 
print " The street dict  \n" ,dict(st_types)
print "\n The cleaned data dict \n", dict(cl_dict)





# The function that will check and list any remaining erorrs that were not cleaned by the previous code.
def Check_update(filename):
    not_cinc_code = set()
    long_code=[]
    check_dict={}
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(filename, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                   if audit_street_type(street_types, tag.attrib['v']):
                       tag.set('v',update_name(tag.attrib['v'], mapping))
                elif is_postcode(tag):
                    if tag.attrib['v'][0:3] != '452':
                        not_cinc_code.add(tag.attrib['v'])
                    elif len(tag.attrib['v']) !=5:
                        long_code.append(tag.attrib['v'])
                     
    check_dict["Street types"]= street_types
    check_dict["Strang zip codes"] = not_cinc_code
    check_dict["Wrong written zip codes"]=long_code
    return check_dict

check_dict= Check_update(finalfile)

# To see if the cleaning was seccessful. Seccessful if the dict. are empety.       
print '\n Updated file dict \n', dict(check_dict)









