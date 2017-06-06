#!/bin/bash

curl -X PUT 'https://search-es-esa-mmwke2z5lwruewstytctb4e6ka.us-east-1.es.amazonaws.com/document/' -d '{
    "settings" : {
        "index" : {
            "number_of_shards" : 1, 
            "number_of_replicas" : 0 
        }
    }
}'

curl -X PUT "https://search-es-esa-mmwke2z5lwruewstytctb4e6ka.us-east-1.es.amazonaws.com/document/_mapping/abstract" -d@document_mapping.json 
