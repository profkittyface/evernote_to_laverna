#!/usr/bin/env python
import xml.etree.ElementTree as ET
import xml.dom.minidom
import psycopg2
import datetime
import re
import sys
import sqlite3

def evernote_date_to_epoch(evernote_date):
    time = datetime.datetime.strptime(evernote_date, '%Y%m%dT%H%M%SZ')
    return time.strftime('%s')

def strip_xml_tags(content):
    r = re.compile('''(?<=<en-note>).*(?=</en-note>)''')
    return r.findall(content)[0]

def load_evernote_enex(evernote_enex):
    ''' Takes evernote file and returns a list of dictionary notes'''
    tree = ET.parse(evernote_enex)
    root = tree.getroot()
    nlist = []
    for note in root:
        notedict = {}
        notedict['title'] = note[0].text
        content_string = note[1].text.encode('utf-8')
        content_string = content_string.replace('&nbsp;', '')
        try:
            minidom = ET.fromstring(content_string)
            notedict['content'] = minidom.text
        except:
            print("Error with note: {}".format(note[0].text))
            print("Note content: {}".format(content_string))
            notedict['content'] = content_string
        notedict['created'] = note[2].text
        notedict['updated'] = note[3].text
        nlist.append(notedict)
    return nlist

if __name__ == "__main__":
    # Get args
    if len(sys.argv) < 2:
        print("Need args, check code for info")
        sys.exit()

    enex_file = sys.argv[1]
    mode = sys.argv[2]

    if mode == 'pg':
        notes = load_evernote_enex(enex_file)
        conn = psycopg2.connect(host='localhost', dbname='evernote', user='bzzagent')
        c = conn.cursor()
        for note in notes:
            try:
                c.execute('insert into notes (title,content) values (%s,%s)', (note['title'],note['content']))
                c.connection.commit()
            except:
                print "Error with note: {}".format(note)
                print sys.exc_info()[0]
        c.connection.close()
    elif mode == 'sqlite3':
        conn = sqlite3.connect('evernote.sqlite3')
        c = conn.cursor()
        c.execute('DROP TABLE IF EXISTS notes')
        c.execute('''CREATE TABLE notes
            (ID INTEGER PRIMARY KEY AUTOINCREMENT, title text, content text, created datetime CURRENT_TIMESTAMP, updated datetime CURRENT_TIMESTAMP)''')
        for note in notes:
            title = note['title'].encode('utf-8')
            content = strip_xml_tags(note['content'].encode('utf-8'))
            print title
            print content

            c.execute("insert into notes (title,content) values (?,?)", (title,content))
            c.connection.commit()
        c.connection.close()
