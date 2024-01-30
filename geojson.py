import json
import sys
import math
import duckdb
from duckdb.typing import VARCHAR
import shapely
from shapely.geometry import shape, box
from pyproj import Geod
from pathlib import Path

geod = Geod(ellps="WGS84")


def validate_geometry(feature:dict) -> tuple[dict|None, float]:
    try:
        s = shape(feature['geometry'])
        s = shapely.force_2d(s)

    except Exception as e:
        # print(f"Invalid geometry for feature: {e}")
        return None, 0

    if s.is_empty:
        # print("Empty geometry for feature")
        return None, 0

    if not s.is_valid:
        # print("Invalid geometry for feature")
        return None, 0
    if s.geom_type == 'GeometryCollection':
        # print("GeometryCollection not supported")
        return None, 0
    try:
        geom = s.__geo_interface__
    except Exception as e:
        # print(f"Failed to convert to geo_interface: {e}")
        return None, 0

    area = 0
    if s.geom_type in ['Polygon','MultiPolygon']:
        area = abs(geod.geometry_area_perimeter(s)[0]) / 1000
    elif s.geom_type in ['LineString', 'MultiLineString']:
        bounds_geom = box(s.bounds[0], s.bounds[1], s.bounds[2], s.bounds[3])
        area = abs(geod.geometry_area_perimeter(bounds_geom)[0]) / 1000

    if math.isnan(area):
        area = 0

    return geom, round(area)

def extract_valid_features(geojson:str) -> str | None:
    valid_features = []
    try:
        gj = json.loads(geojson)
    except json.decoder.JSONDecodeError:
        # print(f"Failed to parse geojson: {repo_name} {github_path}")
        return None
    if not isinstance(gj, dict):
        # print(f"Didnt find a dict in : {repo_name} {github_path}, found {type(gj)}")
        return None
    gj_type = gj.get('type')
    if gj_type == 'FeatureCollection':
        features = gj.get('features')
        if features is None:
            # print(f"Didnt find features in : {repo_name} {github_path}")
            return None
        for feature in features:
            if not isinstance(feature, dict):
                # print(f"Didnt find a dict for feature in : {repo_name} {github_path}, found {type(feature)}")
                continue
            if feature.get('geometry') is None:
                # print(f"Didnt find geometry for feature in : {repo_name} {github_path}")
                continue
            valid_geom, area = validate_geometry(feature)
            if valid_geom is None:
                continue
            feature['geometry'] = valid_geom
            # if feature.get('properties') is None:
            feature['properties'] = {
                'area': area
            }
            if feature.get('id') is not None:
                del feature['id']

            valid_features.append(json.dumps(feature))
    elif gj_type == 'Feature':
        if gj.get('geometry') is None:
            # print(f"Didnt find geometry for feature in : {repo_name} {github_path}")
            return None
        valid_geom, area = validate_geometry(gj)
        if valid_geom is None:
            return None
        gj['geometry'] = valid_geom
        # if gj.get('properties') is None:
        gj['properties'] = {
            'area': area
        }
        if gj.get('id') is not None:
            del gj['id']
        valid_features.append(json.dumps(gj))

    elif gj_type in ['Point', 'LineString', 'Polygon', 'MultiPoint', 'MultiLineString', 'MultiPolygon']:
        feat = {
            'type': 'Feature',
            'geometry': gj,
            'properties': {},
        }
        valid_geom, area = validate_geometry(feat)
        if valid_geom is None:
            return None
        feat['geometry'] = valid_geom
        feat['properties'] = {
            'area': area
        }
        valid_features.append(json.dumps(feat))
    else:
        # print('Unknown geojson type: {}'.format(gj_type))
        pass
    return json.dumps(valid_features)



def main() ->None:
    # km2
    large_geom_size = 1_000_000_000

    con = duckdb.connect(database='github-geojson.duckdb', read_only=False)
    con.install_extension('spatial')
    con.load_extension('spatial')
    con.execute("PRAGMA enable_progress_bar")
    con.create_function("extract_geojson", extract_valid_features, [VARCHAR], VARCHAR)

    [_, features_output_file_path] = sys.argv

    github_contents_cte = """
        github_contents AS (
        SELECT * FROM "data/github-geojson-full/*.parquet" WHERE content is not null
        )
    """


    feature_count_query = f"""
        WITH {github_contents_cte}
        SELECT count(*) FROM github_contents
    """
    res = con.execute(feature_count_query)
    res_count = res.fetchone()
    if res_count is None:
        print("No geojson files found")
        return
    else:
        res_count = res_count[0]
        print(f"Found {res_count} geojson files")


    extract_geojson_cte = """
        extract_geojson AS (
            SELECT
            json_array_length(json(extract_geojson(content))) as feature_count,
            repo_name, path, unnest(json_extract_string(extract_geojson(content), '$[*]')) as geojson
            FROM github_contents
        )
    """

    query_base = f"""
            WITH {github_contents_cte},
            {extract_geojson_cte},
            parsed_geoms AS (
                 SELECT
                    ST_AsWKB(ST_Normalize(ST_GeomFromGeoJSON(json_extract_string(geojson, '$.geometry')))) as geom,
                    cast(json_extract_string(geojson, '$.properties.area') as int64) as area,
                    array_to_string(array_agg(repo_name), ',') as repos,
                    array_to_string(array_agg(path), ',') as paths,
                    count(*) as count
                FROM extract_geojson
                GROUP BY 1, 2
            )
    """

    output_path = Path(features_output_file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix == '.parquet':
        format_options = "WITH (FORMAT PARQUET)"
    elif output_path.suffix == '.fgb':
        format_options = "WITH (FORMAT GDAL, DRIVER 'FlatGeobuf', LAYER_CREATION_OPTIONS 'SPATIAL_INDEX=NO')"
    else:
        raise Exception(f"Unknown output file format: {output_path.suffix}")

    parsed_geoms_query = f"""
        {query_base}
        select * from parsed_geoms where geom is not null
    """
    parsed_features_output_file_path = str(output_path.parent / f"{output_path.stem}_parsed.parquet")
    copy_table_parsed = f"""
        COPY  ({parsed_geoms_query}) TO '{parsed_features_output_file_path}'
        WITH (FORMAT PARQUET)
    """
    con.execute(copy_table_parsed)
    print(f"Saved parsed features to {parsed_features_output_file_path}")


    large_geoms_query = f"""
        SELECT
            geom as geometry, * EXCLUDE(geom)
        FROM "{parsed_features_output_file_path}" WHERE area > {large_geom_size} and geom is not null
    """
    large_features_output_file_path = str(output_path.parent / f"{output_path.stem}_large{output_path.suffix}")
    copy_table_large = f"""
        COPY  ({large_geoms_query}) TO '{large_features_output_file_path}'
        {format_options}
    """
    con.execute(copy_table_large)
    print(f"Saved large features to {large_features_output_file_path}")

    small_geoms_query = f"""
        SELECT
            geom as geometry, * EXCLUDE(geom)
        FROM "{parsed_features_output_file_path}" WHERE area <= {large_geom_size} and geom is not null
    """
    small_features_output_file_path = str(output_path.parent / f"{output_path.stem}_small{output_path.suffix}")

    copy_table_small = f"""
        COPY  ({small_geoms_query}) TO '{small_features_output_file_path}'
        {format_options}
    """
    con.execute(copy_table_small)
    print(f"Saved small features to {small_features_output_file_path}")

    con.close()

if __name__ == '__main__':
    main()