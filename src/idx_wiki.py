import mwparserfromhell
import traceback
import sys, os
from elasticsearch import Elasticsearch
from xml.etree import cElementTree
from util import list_files, time_ms

es = Elasticsearch()


def main():
    if len(sys.argv) != 2:
        print "usage: idx_wiki </path/to/files/for/indexing/>"
        exit()
    for inp_file in list_files(sys.argv[1]):
        if not inp_file.endswith("bz2"):
            print "Processing file:", inp_file
            process_file(inp_file)


def process_file(inp):
    global es
    for event, elem in cElementTree.iterparse(open(inp)):

        if elem.tag == "{http://www.mediawiki.org/xml/export-0.10/}page":
            page_id = elem.findtext("{http://www.mediawiki.org/xml/export-0.10/}id")
            page_title = elem.findtext("{http://www.mediawiki.org/xml/export-0.10/}title")
            revision = elem.find("{http://www.mediawiki.org/xml/export-0.10/}revision")
            redirect = elem.find("{http://www.mediawiki.org/xml/export-0.10/}redirect")
            namespace = elem.findtext("{http://www.mediawiki.org/xml/export-0.10/}ns")

            if redirect is not None:
                print "skipping redirect:", page_title
                continue

            if revision is not None and page_title is not None and namespace == "0":
                markup = revision.findtext("{http://www.mediawiki.org/xml/export-0.10/}text")
                try:
                    wikitext = mwparserfromhell.parse(markup).strip_code()
                except:
                    print "FAILED to parse wiki markup - skipping:"
                    print traceback.print_exc()
                if page_id and page_title and wikitext:
                    now = time_ms()
                    doc = {"id": page_id, "page_title": page_title, "content": wikitext, "index_time": now}
                    print es.index(index="wikipedia", doc_type="article", id=page_id, body=doc)  # TODO check failure
            else:
                print "skipping article:", page_title
            elem.clear()


if __name__ == "__main__":
    main()
