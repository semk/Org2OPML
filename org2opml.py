#! /usr/bin/env python
#
# Converts Emacs Org files to OPML so that Mindmaps can be generated
# using both Freemind and Mindnode
#
# @author: Sreejith K <sreejithemk@gmail.com>
# Created on 1 Aug 2013


import re
import os
import sys
import codecs
import xml.etree.ElementTree as ET
from xml.dom import minidom


class Node(object):

    """Represents a Node. Also stores the references to
    all its children which are also Node instances.
    """

    def __init__(self, level, text):
        self.level = level
        self.text = text
        self.children = []

    def add_child(self, node):
        """Add a chld Node.
        """
        self.children.append(node)


class OrgParser(object):

    # Regular expressions for parsing the metadata
    NODE_RE = re.compile('(?P<level>[*]+)\s+(?P<text>.*)')
    TITLE_RE = re.compile('TITLE\s*:\s+(?P<title>.*)')
    AUTHOR_RE = re.compile('AUTHOR\s*:\s+(?P<author>.*)')
    ROOT_RE = re.compile('ROOT\s*:\s+(?P<root>.*)')

    def __init__(self, org_file):
        self.org_file = org_file
        self.title = ''
        self.author = ''
        self.root_name = ''
        self.nodes = []
        self.prev_node = None
        with codecs.open(org_file, 'r', encoding='UTF-8') as f:
            self.content = f.readlines()

    def parse(self):
        """Parse the content line by line
        """
        for line in self.content:
            line = line.strip()
            if line.startswith('#+'):
                self.handle_meta(line[2:])
            elif line.startswith('*'):
                self.add_node(line)

    def handle_meta(self, line):
        """Parse the metadata
        """
        if line.startswith('TITLE'):
            match = self.TITLE_RE.search(line)
            if match:
                self.title = match.group('title')
        elif line.startswith('AUTHOR'):
            match = self.AUTHOR_RE.search(line)
            if match:
                self.author = match.group('author')
        elif line.startswith('ROOT'):
            match = self.ROOT_RE.search(line)
            if match:
                self.root_name = match.group('root')

    def add_node(self, line):
        """Create a node. Set the level and text. Assigns the parent Node
        """
        match = self.NODE_RE.match(line)
        if match:
            level = match.group('level').count('*')
            text = match.group('text')
            newnode = Node(level=level, text=text)

            if level == 1:
                try:
                    self.nodes[level - 1].append(newnode)
                except IndexError:
                    self.nodes.append([newnode])
            else:
                parent = self.nodes[level - 2][-1]
                parent.add_child(newnode)
                try:
                    self.nodes[level - 1].append(newnode)
                except IndexError:
                    self.nodes.append([newnode])

    def to_opml(self):
        """Export the parsed Node information to OPML format
        """
        skip_root = False
        # If there is only one root node. Make it as the root node in OPML
        if len(self.nodes) == 1:
            self.root_name = self.nodes[0].text
            skip_root = True

        root = ET.Element('opml', attrib={'version': '1.0'})
        head = ET.SubElement(root, 'head')
        title = ET.SubElement(head, 'title')
        title.text = self.title
        author = ET.SubElement(head, 'ownername')
        author.text = self.author
        body = ET.SubElement(root, 'body')
        outline = ET.SubElement(body, 'outline', attrib={
                                'text': self.root_name})

        # Recursively iterate the Node and construct the XML ElementTree
        def iterate_children(node, ol):
            for child in node.children:
                element = ET.SubElement(
                    ol, 'outline', attrib={'text': child.text})
                iterate_children(child, element)

        # Iterate through the root nodes represented by single *
        for root_node in self.nodes[0]:
            if not skip_root:
                ol = ET.SubElement(outline, 'outline', attrib={
                                   'text': root_node.text})
                iterate_children(root_node, ol)
            else:
                iterate_children(root_node, outline)

        opml_file = os.path.splitext(self.org_file)[0] + '.opml'

        # This code writes ugly XML
        # tree = ET.ElementTree(root)
        # tree.write(opml_file, encoding='UTF-8', xml_declaration=True)

        # Pretty print the XML into the file
        xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(encoding='UTF-8')
        with open(opml_file, 'w') as f:
            f.write(xmlstr)

        return opml_file


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: org2opml.py <input-org-file>'
        sys.exit(-2)

    p = OrgParser(sys.argv[1])
    p.parse()
    print 'Exporting to OPML: %s' % p.to_opml()
