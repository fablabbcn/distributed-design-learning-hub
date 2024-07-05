# Distributed Design Learning Hub Prototype

A collective second-brain for the distributed design network.

## Development

You'll need [Docker](https://www.docker.com/).

- Copy `env.example` to `.env` and adjust to taste.
- Copy `pre-commit.example` to `.git/hooks/pre-commit` to set up pre-commit checks
- Run `docker compose up`
- Run `scripts/test_ingest_pdfs.sh` to ingest some sample data.

The API will be avialable on port `5100`, [Elasticsearch](https://www.elastic.co/elasticsearch) on `9200`, and [Flower](https://flower.readthedocs.io/en/latest/) (for monitoring [Celery](https://docs.celeryq.dev/en/stable/#) jobs) on port `5557`, and the [Elasticvue](https://elasticvue.com/) Query / admin interface on port `8080`.

## Usage:

### Index a document:

```
$ curl --header "Content-Type: application/json" --request "POST" \
        --data "{\"url\": \"https://distributeddesign.eu/wp-content/uploads/2023/05/DDP_DrivingDesign.pdf\"}" \
        http://localhost:5010/index
```

### Query the Elasticsearch index:

```
$ curl --header "Content-Type: application/json" --request "GET" \
       --data "{\"query\": { \"match\": { \"text\": \"design\" }}}" \
       http://localhost:9200/_search

```
