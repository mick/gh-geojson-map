import {layerStyle} from './mapstyles.js'
import maplibregl from "maplibre-gl";

import Alpine from 'alpinejs';
window.Alpine = Alpine

Alpine.data('main', () => ({
  features: [],
  sidebar: false,
  highlightFeatureID: null,
  init() {
    var map = new maplibregl.Map({
      container: "map",
      minZoom: 2,
      center: [-122.486052, 37.830348],
      style: {
          "version": 8,
          "name": "VTile preview",
          "layers": [
              {
                  "id": "background",
                  "type": "background",
                  "paint": {
                      "background-color": "#ffffff",
                  }
              }
          ],
          "sources": {
              "github-geojson-large": {
                  "type": "vector",
                  "url": "https://tiles.simplemap.dev/github-geojson-features-large.json"
              },
              "github-geojson-small": {
                "type": "vector",
                "url": "https://tiles.simplemap.dev/github-geojson-features-small.json"
            }
          }
      },
      zoom: 8,
      hash: true,
    })

    map.on("load", () => {
      map.showTileBoundaries = false;

      layerStyle("large", "github-geojson-large", "github-geojson-large", false).forEach(layer => {
        map.addLayer(layer)
      })
      layerStyle("small", "github-geojson", "github-geojson-small", true).forEach(layer => {
        map.addLayer(layer)
      })
      map.on('click', this.featuresClick.bind(this))

    })
    this.map = map

  },
  toggleSidebar() {
      this.sidebar = ! this.sidebar
  },
  featuresClick (e) {
    this.sidebar = true;
    this.highlightFeatureID = null
    this.map.removeFeatureState({source: 'github-geojson-large', sourceLayer: 'github-geojson-large'})
    this.map.removeFeatureState({source: 'github-geojson-small', sourceLayer: 'github-geojson'})

    const features = this.map.queryRenderedFeatures(
      e.point,
      {layers: ['large-polygon-fill', 'large-line-line', 'small-polygon-fill', 'small-line-line', 'small-point-circle']}
      );

    var featureList = features.map(f => {

      if ((f.geometry.type.indexOf('Point') === -1) && (f.properties.area === 0)) {
        f.properties.area = Infinity
      }
        return {
            id: f.id,
            geomType: f.geometry.type,
            count: f.properties.count,
            repos: f.properties.repos.split(','),
            paths: f.properties.paths.split(','),
            area: f.properties.area ,
        }
    })

    featureList = featureList.sort((a, b) => a.area - b.area)


    this.features =featureList;
  },
  highlight(featId) {
    this.highlightFeatureID = featId
    this.map.removeFeatureState({source: 'github-geojson-small', sourceLayer: 'github-geojson'})
    this.map.removeFeatureState({source: 'github-geojson-large', sourceLayer: 'github-geojson-large'})
    this.map.setFeatureState({source: 'github-geojson-small', sourceLayer: 'github-geojson', id: featId}, {hover: true})
    this.map.setFeatureState({source: 'github-geojson-large', sourceLayer: 'github-geojson-large', id: featId}, {hover: true})
  }
}))
Alpine.start()