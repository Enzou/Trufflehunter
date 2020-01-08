import datetime
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List


class XesReader():
    def __init__(self):
        pass

    def read(self, xes_file: Path) -> List:
        # tree = ET.parse('financial_log.xes')
        tree = ET.parse(xes_file)
        root = tree.getroot()

        ns = {'xes': 'http://www.xes-standard.org/'}
        for trace in root.findall('xes:trace', ns):
            caseid = ''
            for string in trace.findall('xes:string', ns):
                if string.attrib['key'] == 'concept:name':
                    caseid = string.attrib['value']
            for event in trace.findall('xes:event', ns):
                task = ''
                user = ''
                event_type = ''
                for string in event.findall('xes:string', ns):
                    if string.attrib['key'] == 'concept:name':
                        task = string.attrib['value']
                    if string.attrib['key'] == 'org:resource':
                        user = string.attrib['value']
                    if string.attrib['key'] == 'lifecycle:transition':
                        event_type = string.attrib['value']
                timestamp = ''
                for date in event.findall('xes:date', ns):
                    if date.attrib['key'] == 'time:timestamp':
                        timestamp = date.attrib['value']
                        timestamp = datetime.datetime.strptime(timestamp[:-10], '%Y-%m-%dT%H:%M:%S')
                print(';'.join([caseid, task, event_type, user, str(timestamp)]))