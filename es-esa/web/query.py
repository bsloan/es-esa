boost_script = "score = _score; concepts = _source.concepts; for (concept in concepts) { queryConcept = queryConcepts.find { it.id == concept.id }; if (queryConcept) { score += (queryConcept.score * concept.score); } }; return score;"


def get_concept_query(q):
    return {
        "from": 0,
        "size": 10,
        "min_score": 0.5,  # TODO: parameterize min score
        "_source": {
            "include": "page_title"
        },
        "query": {
            "match": {
                "content": q
            }
        }
    }


def get_match_query(offset, size, q):
    return {
        "from": offset,
        "size": size,
        "query": {
            "multi_match": {
                "query": q,
                "fields": ["title", "abstract"]
            }
        }
    }


def get_expanded_query(offset, size, q, concepts):
    return {
        "from": offset,
        "size": size,
        "query": {
            "bool": {
                "should": [{
                    "multi_match": {
                        "query": q,
                        "fields": ["title", "abstract"]
                    }
                }, {
                    "terms": {
                        "concepts.id": [concept["id"] for concept in concepts],
                        # "boost": 0.6  TODO: un-boost concept terms query?
                    }
                }]
            }
        }
    }


def get_boosted_query(offset, size, q, concepts):
    return {
        "from": offset,
        "size": size,
        "query": {
            "function_score": {
                "boost_mode": "replace",
                "query": {
                    "multi_match": {
                        "query": q,
                        "fields": ["title", "abstract"]
                    }
                },
                "script_score": {
                    "script": boost_script,
                    "params": {
                        "queryConcepts": concepts
                    }
                }
            }
        }
    }


def get_boosted_expanded_query(offset, size, q, concepts):
    return {
        "from": offset,
        "size": size,
        "query": {
            "function_score": {
                "boost_mode": "replace",
                "query": {
                    "bool": {
                        "should": [{
                            "multi_match": {
                                "query": q,
                                "fields": ["title", "abstract"]
                            }
                        }, {
                            "terms": {
                                "concepts.id": concepts
                                # "boost": 0.6  TODO: un-boost concept terms query?
                            }
                        }]
                    }
                },
                "script_score": {
                    "script": boost_script,
                    "params": {
                        "queryConcepts": concepts
                    }
                }
            }
        }
    }
