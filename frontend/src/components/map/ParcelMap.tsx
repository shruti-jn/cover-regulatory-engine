import { useEffect, useRef } from "react";
import maplibregl, { GeoJSONSource, LngLatBoundsLike, Map, StyleSpecification } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

type ParcelGeometry = {
  type: "Polygon";
  coordinates: number[][][];
};

type ParcelMapProps = {
  geometry: ParcelGeometry | null;
  accuracyFlag: string | null;
};

const EMPTY_STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [
    {
      id: "background",
      type: "background",
      paint: {
        "background-color": "#eef2ee",
      },
    },
  ],
};

export function ParcelMap({ geometry, accuracyFlag }: ParcelMapProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) {
      return;
    }

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: EMPTY_STYLE,
      center: [-118.256, 34.047],
      zoom: 15,
      attributionControl: false,
    });

    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.on("load", () => {
      map.addSource("parcel", {
        type: "geojson",
        data: emptyFeatureCollection(),
      });
      map.addLayer({
        id: "parcel-fill",
        type: "fill",
        source: "parcel",
        paint: {
          "fill-color": "#7b9fb5",
          "fill-opacity": 0.24,
        },
      });
      map.addLayer({
        id: "parcel-outline",
        type: "line",
        source: "parcel",
        paint: {
          "line-color": "#486879",
          "line-width": 2,
        },
      });
      map.addSource("setback", {
        type: "geojson",
        data: emptyFeatureCollection(),
      });
      map.addLayer({
        id: "setback-outline",
        type: "line",
        source: "setback",
        paint: {
          "line-color": "#c46d4a",
          "line-width": 1.5,
          "line-dasharray": [2, 2],
        },
      });
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) {
      return;
    }

    const syncSources = () => {
      const parcelSource = map.getSource("parcel") as GeoJSONSource | undefined;
      const setbackSource = map.getSource("setback") as GeoJSONSource | undefined;
      if (!parcelSource || !setbackSource) {
        return;
      }

      if (!geometry) {
        parcelSource.setData(emptyFeatureCollection());
        setbackSource.setData(emptyFeatureCollection());
        return;
      }

      const parcelFeature = {
        type: "Feature" as const,
        geometry,
        properties: {
          accuracy_flag: accuracyFlag ?? "UNKNOWN",
        },
      };
      parcelSource.setData({
        type: "FeatureCollection",
        features: [parcelFeature],
      });
      setbackSource.setData({
        type: "FeatureCollection",
        features: [createInsetFeature(geometry)],
      });
      map.fitBounds(getBounds(geometry.coordinates[0]), {
        padding: 64,
        duration: 0,
      });
    };

    if (map.isStyleLoaded()) {
      syncSources();
    } else {
      map.once("load", syncSources);
    }
  }, [geometry, accuracyFlag]);

  return (
    <div className="parcel-map-frame">
      <div ref={mapContainerRef} className="parcel-map-canvas" />
      {!geometry ? <div className="map-empty-state">Parcel geometry will appear here after lookup.</div> : null}
    </div>
  );
}

function emptyFeatureCollection() {
  return {
    type: "FeatureCollection" as const,
    features: [],
  };
}

function createInsetFeature(geometry: ParcelGeometry) {
  const ring = geometry.coordinates[0];
  const centroidLng = ring.reduce((sum, [lng]) => sum + lng, 0) / ring.length;
  const centroidLat = ring.reduce((sum, [, lat]) => sum + lat, 0) / ring.length;

  const inset = ring.map(([lng, lat]) => [
    centroidLng + (lng - centroidLng) * 0.84,
    centroidLat + (lat - centroidLat) * 0.84,
  ]);

  return {
    type: "Feature" as const,
    geometry: {
      type: "Polygon" as const,
      coordinates: [inset],
    },
    properties: {},
  };
}

function getBounds(ring: number[][]): LngLatBoundsLike {
  let minLng = ring[0][0];
  let minLat = ring[0][1];
  let maxLng = ring[0][0];
  let maxLat = ring[0][1];

  for (const [lng, lat] of ring) {
    minLng = Math.min(minLng, lng);
    minLat = Math.min(minLat, lat);
    maxLng = Math.max(maxLng, lng);
    maxLat = Math.max(maxLat, lat);
  }

  return [
    [minLng, minLat],
    [maxLng, maxLat],
  ];
}
