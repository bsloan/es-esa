import sys, re, traceback
from elasticsearch import Elasticsearch
from xml.etree import cElementTree
from util import time_ms, list_files

es = Elasticsearch()


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print "usage: idx_docs </path/to/files/for/indexing/> [cutoff]"
        exit()
    use_cutoff_freq = False
    if len(sys.argv) == 3 and sys.argv[2].lower() == "cutoff":
        use_cutoff_freq = True
    for inp_file in list_files(sys.argv[1]):
        index_file(inp_file, use_cutoff_freq)


def index_file(filename, use_cutoff_freq=False):
    n_indexed = 0
    total_index_time = 0
    cutoff = 10
    max_clause = 1024

    print "indexing:", filename
    for event, elem in cElementTree.iterparse(open(filename)):
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
                        concepts = get_concepts(doc_title + ". " + abstract, max_clause, cutoff, doc_id,
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
    print "indexing [" + filename + "] complete. average time per document is " + str(avg_index_time) + "ms"


def get_concepts(text, max_clauses, cutoff, doc_id, cutoff_freq=False):
    if len(text.split()) > max_clauses:
        print "text for [" + doc_id + "] exceeds max clause count of " + str(max_clauses) + " - not adding concepts"
        return []

    concepts = []
    query = get_common_terms_query(cutoff, text) if cutoff_freq else get_match_query(cutoff, text)
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


def get_common_terms_query(cutoff, querystr):
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


def get_match_query(cutoff, querystr):
    return {
        "from": 0,
        "size": 10,
        "query": {
            "match": {
                "content": querystr
            }
        }
    }


if __name__ == "__main__":
    main()
