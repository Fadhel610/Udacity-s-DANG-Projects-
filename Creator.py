#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 30 19:54:12 2017

@author: fadhel.h
"""

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

OSM_PATH = "Cincinnati.xml"  # Takes the updated file

# These CSV files will be later tables in the data base
NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

# To check if there are propblems in the inputs 
LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# Importing the desired schema from the other file
SCHEMA = schema.schema

NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  
    
    if element.tag == 'node' :
        node_attribs['id']=element.attrib['id']
        node_attribs['user']=element.attrib['user']
        node_attribs['uid']=element.attrib['uid']
        node_attribs['version']=element.attrib['version']
        node_attribs['lat']=element.attrib['lat']
        node_attribs['lon']=element.attrib['lon']
        node_attribs['timestamp']=element.attrib['timestamp']
        node_attribs['changeset']=element.attrib['changeset']
        for i in element.findall('tag'):
    # matching between the raw file  elements and the fields in th CSV files.
            if re.search(LOWER_COLON, i.get('k')) is not None:
                tags.append({'id':element.attrib['id'],
               'key':i.get('k').split(':',1)[1],
               'value':i.get('v'),
               'type':i.get('k').split(':',1)[0] })
    # Ignoring the problematic fields 
            elif re.search(PROBLEMCHARS, i.get('k')) is not None:
                pass
            
            else:
                tags.append({'id':element.attrib['id'],
               'key':i.get('k'),
               'value':i.get('v'),
                'type': 'regular'})
        
        return {'node': node_attribs, 'node_tags': tags}
    
    elif element.tag == 'way':
        way_attribs['id'] = element.attrib['id']
        way_attribs['user'] = element.attrib['user']
        way_attribs['uid']=element.attrib['uid']
        way_attribs['version']=element.attrib['version']
        way_attribs['timestamp']=element.attrib['timestamp']
        way_attribs['changeset']=element.attrib['changeset']
        for i in element.findall('tag'):
            if re.search(LOWER_COLON, i.get('k')) is not None:
                tags.append({'id':element.attrib['id'],
               'key':i.get('k').split(':',1)[1],
               'value':i.get('v'),
               'type':i.get('k').split(':',1)[0] })
            
            elif re.search(PROBLEMCHARS, i.get('k')) is not None:
                pass
            else:
                tags.append({'id':element.attrib['id'],
               'key':i.get('k'),
               'value':i.get('v'),
                'type': 'regular'})
        pos=0
        for i in element.findall('nd'):
            way_nodes.append({'id':element.attrib['id'],
            'node_id': i.get('ref'),
            'position':pos})
            pos+=1
        pos=0
    
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}
 


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])



process_map(OSM_PATH, validate=True)
