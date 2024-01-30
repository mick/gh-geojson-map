## Github GeoJSON MAP

Also see blog post about this here: XXXXXXXXXXXX

This repo contains a script that process GitHub GeoJSON file contents from BigQuery to prepare it to be tiled and visualized on a map.

Assuming you have the data in a parquet files located at: `data/github-geojson-full/*.parquet`

You provide a path and format for output (fgb or parquet)

```bash
pipenv install
pipenv run python geojson.py data/github-features.parquet
```

Will generate

```bash
data/github-features_small.parquet
data/github-features_large.parquet
```

Splitting features into "small" and "large" (by polygon area or bbox area for linestrings)


DuckDB, because it uses it native parquet writer doesnt yet know how to write a geoparquet file, so we use `gpq` to convert it.

```bash
gpq convert data/github-features_large.parquet data/geoparquet/github-features_large.parquet
gpq convert data/github-features_small.parquet data/geoparquet/github-features_small.parquet
```

Then we can use `tippecanoe` to generate the pmtiles

```bash
gpq convert data/geoparquet/github-features_small.parquet --to=geojson | tippecanoe --force --maximum-tile-bytes=3000000 --maximum-tile-features=300000 -z12 -Z4 --drop-smallest-as-needed -P --base-zoom=12 --generate-ids --layer=github-geojson --output=data/tilesets/github-geojson-features-small.pmtiles

gpq convert data/geoparquet/github-features_large.parquet --to=geojson | tippecanoe --force --maximum-tile-bytes=3000000 --maximum-tile-features=300000 -z9 -Z0 --drop-smallest-as-needed -P --base-zoom=9 --generate-ids --layer=github-geojson-large --output=data/tilesets/github-geojson-features-large.pmtiles
```

In a future where tippecanoe can read geoparquet files and duckdb can write geoparquet this is gonna be even faster.


Now with pmtiles files, those can be served with the pmtiles cli or on cloudflare workers.

You can see this in action at XXXXXXXXXXX
