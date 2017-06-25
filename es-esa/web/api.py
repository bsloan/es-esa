from time import time
from collections import OrderedDict
from flask import request, jsonify
from elasticsearch import Elasticsearch, RequestsHttpConnection
from query import *
from flask import Blueprint, current_app
from error import BadRequest
from aws_requests_auth.aws_auth import AWSRequestsAuth
from aws_requests_auth import boto_utils


search_api = Blueprint("search_api", __name__)


def init_elasticsearch():
    auth = AWSRequestsAuth(aws_host=current_app.config["AWS_ELASTICSEARCH_HOST"],
                           aws_region=current_app.config["AWS_ELASTICSEARCH_REGION"],
                           aws_service="es", **boto_utils.get_credentials())
    return Elasticsearch(host=current_app.config["AWS_ELASTICSEARCH_HOST"],
                         port=current_app.config["AWS_ELASTICSEARCH_PORT"],
                         connection_class=RequestsHttpConnection, http_auth=auth)


def time_ms():
    return int(round(time() * 1000))


@search_api.route("/search")
def search():
    es = init_elasticsearch()
    q = request.args.get("q")
    size = request.args.get("size")
    offs = request.args.get("from")
    boost = request.args.get("boost")
    expand = request.args.get("expand")
    debug = request.args.get("debug")
    now = time_ms()

    if not size:
        size = 10
    if not offs:
        offs = 0
    if not q:
        raise BadRequest("Query string is required", status_code=400)

    concepts_query = None
    concepts = []
    threshold = 1  # TODO: parameterize query term threshold
    if len(q.split()) > threshold:
        concepts_query = get_concept_query(q)
        concepts = [{"concept": concept["_source"]["page_title"], "score": concept["_score"], "id": concept["_id"]}
                    for concept in es.search(index="wikipedia", doc_type="article", body=concepts_query)["hits"]["hits"]
                    if concept["_score"] >= 0.5]  # TODO: parameterize cutoff score

    if len(concepts) == 0:  # skip expansion and boosting if there are no query concepts to work with
        boost = None
        expand = None

    if boost is not None and expand is not None:
        main_query = get_boosted_expanded_query(offs, size, q, concepts)
    elif boost is not None:
        main_query = get_boosted_query(offs, size, q, concepts)
    elif expand is not None:
        main_query = get_expanded_query(offs, size, q, concepts)
    else:
        main_query = get_match_query(offs, size, q)

    search_args = {"index": "document", "doc_type": "abstract", "body": main_query}
    response = OrderedDict()
    if debug is not None:
        response["concepts_query"] = concepts_query
        response["main_query"] = main_query
        search_args["explain"] = debug

    docs_results = es.search(**search_args)
    elapsed = time_ms() - now
    response["query_time_ms"] = elapsed
    response["query_concepts"] = concepts
    response["hits"] = docs_results["hits"]["hits"]
    return jsonify(response)


@search_api.errorhandler(BadRequest)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
