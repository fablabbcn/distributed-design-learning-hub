#!/bin/bash
while read url; do
 curl --header "Content-Type: application/json" --request "POST" --data "{\"url\": \"$url\"}" http://localhost:5010/index
done < data/pdf_fixtures.txt
