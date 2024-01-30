
export function layerStyle(layerBaseName, sourceLayer, source, enablePointLayer) {

  var layers = []

  layers.push({
    id: `${layerBaseName}-polygon-fill`,
    "source-layer": sourceLayer,
    type: "fill",
    source: source,
    filter: [
      "match",
      ["geometry-type"],
      ["Polygon", "MultiPolygon"],
      true,
      false,
    ],
    paint: {
      'fill-color': "#6e7781",
      'fill-opacity': [
        'interpolate',
        ['linear'],
        ['get', 'count'],
        0,
        0,
        1,
        0.01,
        3000,
        0.3,
        4500,
        0.7,
        6000,
        1
    ]
    },
  });

  layers.push({
    id: `${layerBaseName}-polygon-line`,
    "source-layer": sourceLayer,
    type: "line",
    source: source,
    filter: [
      "match",
      ["geometry-type"],
      ["Polygon", "MultiPolygon"],
      true,
      false,
    ],
    paint: {
      'line-color': "#57606a",
      'line-opacity': [
        'interpolate',
        ['linear'],
        ['get', 'count'],
        0,
        0,
        1,
        0.1,
        4000,
        0.6,
        8000,
        1
    ]
    }
  });



  layers.push({
    id: `${layerBaseName}-polygon-fill-highlight`,
    "source-layer": sourceLayer,
    type: "fill",
    source: source,
    filter: [
      "match",
      ["geometry-type"],
      ["Polygon", "MultiPolygon"],
      true,
      false,
    ],
    paint: {
      'fill-outline-color': '#FFFFFF',
      'fill-color': '#eac54f',
      'fill-opacity': [
        "case",
        ["boolean", ["feature-state", "hover"], false],
        0.6,
        0
      ]
    }
  });

  layers.push({
    id: `${layerBaseName}-line-line`,
    "source-layer": sourceLayer,
    type: "line",
    source: source,
    filter: [
      "match",
      ["geometry-type"],
      ["LineString", "MultiLineString"],
      true,
      false,
    ],
    paint: {
      'line-color': "#54aeff",
      'line-opacity': [
        'interpolate',
        ['linear'],
        ['get', 'count'],
        0,
        0,
        1,
        0.1,
        1000,
        0.6,
        1200,
        1
    ],
    'line-width': [
      'interpolate',
      ['linear'],
      ['zoom'],
      0,
      1,
      4,
      1,
      7,
      2,
      12,
      4]
    }
  });

  layers.push({
    id: `${layerBaseName}-line-line-highlight`,
    "source-layer": sourceLayer,
    type: "line",
    source: source,
    filter: [
      "match",
      ["geometry-type"],
      ["LineString", "MultiLineString"],
      true,
      false,
    ],
    paint: {
      'line-color': '#eac54f',
      'line-width': 6,
      'line-opacity': [
        "case",
        ["boolean", ["feature-state", "hover"], false],
        0.6,
        0
      ]
    }
  });

  if (enablePointLayer) {
    layers.push({
      id: `${layerBaseName}-point-circle`,
      "source-layer": sourceLayer,
      type: "circle",
      source: source,
      filter: [
        "match",
        ["geometry-type"],
        ["Point", "MultiPoint"],
        true,
        false,
      ],
      paint: {
        'circle-color': "#30a14e",
        'circle-stroke-color': "#ffffff",
        'circle-stroke-width': 1,
        'circle-radius': [
          'interpolate',
          ['linear'],
          ['zoom'],
          0,
          1,
          4,
          1,
          7,
          2,
          11,
          3,
          20,
          12],
        'circle-stroke-opacity':[
          'interpolate',
          ['linear'],
          ['get', 'count'],
          0,
          0,
          1,
          0.3,
          10,
          0.5,
          200,
          1
        ],
        'circle-opacity': [
          'interpolate',
          ['linear'],
          ['get', 'count'],
          0,
          0,
          1,
          0.5,
          10,
          0.7,
          20,
          1
      ]
      }
    });

    layers.push({
      id: `${layerBaseName}-point-circle-highlight`,
      "source-layer": sourceLayer,
      type: "circle",
      source: source,
      filter: [
        "match",
        ["geometry-type"],
        ["Point", "MultiPoint"],
        true,
        false,
      ],
      paint: {
        'circle-color': '#eac54f',
        'circle-radius': 12,
        'circle-opacity': [
          "case",
          ["boolean", ["feature-state", "hover"], false],
          1,
          0
        ]
      }
    });
  }
  return layers
}




