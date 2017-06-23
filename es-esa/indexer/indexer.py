import mwparserfromhell
import traceback
import settings
import re
import sys
reload(sys)
sys.setdefaultencoding("utf-8")  # FIXME
from xml.etree import cElementTree
from elasticsearch import Elasticsearch, RequestsHttpConnection
from util import time_ms, list_files
from aws_requests_auth.aws_auth import AWSRequestsAuth
from aws_requests_auth import boto_utils


auth = AWSRequestsAuth(aws_host=settings.AWS_ELASTICSEARCH_HOST, aws_region=settings.AWS_ELASTICSEARCH_REGION,
                       aws_service="es", **boto_utils.get_credentials())
es = Elasticsearch(host=settings.AWS_ELASTICSEARCH_HOST, port=settings.AWS_ELASTICSEARCH_PORT,
                   connection_class=RequestsHttpConnection, http_auth=auth)


class DocumentIndexer(object):
    def index_file(self, inp, use_cutoff_freq=False):
        raise NotImplementedError("Not implemented")


class WikipediaIndexer(DocumentIndexer):
    def index_file(self, inp, use_cutoff_freq=False):
        context = cElementTree.iterparse(open(inp), events=("start", "end"))
        context = iter(context)
        event, root = context.next()

        for event, elem in context:
            if event == "end" and elem.tag == "{http://www.mediawiki.org/xml/export-0.10/}page":
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
            root.clear()


class RepecIndexer(DocumentIndexer):
    def index_file(self, inp, use_cutoff_freq=False):
        n_indexed = 0
        total_index_time = 0
        cutoff = 10
        max_clause = 1024

        print "indexing:", inp
        for event, elem in cElementTree.iterparse(open(inp)):
            if elem.tag == "{http://www.openarchives.org/OAI/2.0/oai_dc/}dc":
                doc_title = elem.findtext("{http://purl.org/dc/elements/1.1/}title")
                doc_id = elem.findtext("{http://purl.org/dc/elements/1.1/}identifier")

                if doc_title and doc_id:  # document id and title are required
                    doc_title = doc_title.replace("\n", " ")
                    doc_id = re.sub("http.+//", "", doc_id)
                    doc = {
                        "id": doc_id,
                        "title": doc_title,
                        "index_time": time_ms()
                    }
                    started = time_ms()

                    abstract = elem.findtext("{http://purl.org/dc/elements/1.1/}description")
                    if abstract:
                        doc["abstract"] = abstract
                        try:
                            concepts = self.get_concepts(doc_title + ". " + abstract, max_clause, cutoff, doc_id,
                                                    cutoff_freq=use_cutoff_freq)
                            if concepts:
                                doc["concepts"] = concepts  # TODO: trim to the top n concepts over a certain score?
                        except:
                            print "failed to retrieve concepts for document [" + doc_id + "] - skipping"
                            traceback.print_exc()

                    result = es.index(index="document", doc_type="abstract", id=doc_id, body=doc)
                    # TODO: count failures?
                    elapsed = time_ms() - started
                    total_index_time += elapsed
                    print "indexed document [" + doc_id + "] in " + str(elapsed) + "ms"
                    n_indexed += 1

        # indexing complete for this file - show average indexing time
        avg_index_time = total_index_time / n_indexed
        print "indexing [" + inp + "] complete. average time per document is " + str(avg_index_time) + "ms"

    def get_concepts(self, text, max_clauses, cutoff, doc_id, cutoff_freq=False):
        if len(text.split()) > max_clauses:
            print "text for [" + doc_id + "] exceeds max clause count of " + str(max_clauses) + " - not adding concepts"
            return []

        concepts = []
        query = self.get_common_terms_query(cutoff, text) if cutoff_freq else self.get_match_query(cutoff, text)
        for hit in es.search(index="wikipedia", doc_type="article", body=query, request_timeout=30)["hits"]["hits"]:
            score = hit["_score"]
            id = hit["_id"]
            title = hit["_source"]["page_title"]
            if "(disambiguation)" in title.lower():  # TODO: should be ignored during Wikipedia index build
                print "skipping disambiguation article:", title
            else:
                concept = {}
                concept["score"] = score
                concept["id"] = id
                concept["concept"] = title
                concepts.append(concept)
        return concepts

    def get_common_terms_query(self, cutoff, querystr):
        return {
            "from": 0,
            "size": cutoff,
            "query": {
                "common": {
                    "content": {
                        "query": querystr,
                        "cutoff_frequency": 0.0003,
                        "low_freq_operator": "or",
                        "minimum_should_match": {
                            "low_freq": 3,
                            "high_freq": 10
                        }
                    }
                }
            }
        }

    def get_match_query(self, cutoff, querystr):
        return {
            "from": 0,
            "size": 10,
            "query": {
                "match": {
                    "content": querystr
                }
            }
        }


def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print "usage: indexer </path/to/files/for/indexing/> <indexer> [cutoff]"
        exit()
    use_cutoff_freq = False
    if len(sys.argv) == 4 and sys.argv[3].lower() == "cutoff":
        use_cutoff_freq = True
    idxr = getattr(sys.modules[__name__], sys.argv[2])()
    for inp_file in list_files(sys.argv[1]):
        idxr.index_file(inp_file, use_cutoff_freq)


if __name__ == "__main__":
    main()
