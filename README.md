# Distributed Design Learning Hub Prototype

A collective second-brain for the distributed design network.

See the live site [here](https://learn.distributeddesign.eu).

## Development

You'll need [Docker](https://www.docker.com/).

- Copy `env.example` to `.env` and adjust to taste.
- Copy `pre-commit.example` to `.git/hooks/pre-commit` to set up pre-commit checks
- Run `docker compose up`: the web application will be served locally on port `5010`.
- Run `scripts/ingest_documents.sh` to ingest the document library.
- Run `scripts/clear_query_cache.sh` to delete all cached query summaries, so they are regenerated with the current language model. Cached summaries also expire on their own after `REDIS_QUERY_CACHE_TIMEOUT` seconds (60 days by default).
- Run `docker compose exec app pre-commit run --all-files` to run all linters and test suite.
- If you get permissions errors when committing to git, or running tests, override the `uid` build argument on the `app` container in a `compose.local.yml` file, giving the UID of your local user.
