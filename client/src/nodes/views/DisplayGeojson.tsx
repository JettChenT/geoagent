import {
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
  GeoJSON,
  GeoJSONProps,
} from "react-leaflet";

import { ContextData } from "../ContextNode";

function RenderFeature({ feature }: { feature: any }) {
  const { geometry, properties } = feature;
  if (!geometry) {
    return null;
  }
  switch (geometry.type) {
    case "Point":
      return (
        <Marker position={[geometry.coordinates[0], geometry.coordinates[1]]}>
          <Popup>point</Popup>
        </Marker>
      );
    default:
      return null;
  }
}

export default function DisplayGeojson({ data }: { data: ContextData }) {
  if (!data.auxiliary.geojson) {
    return null;
  }
  const gjson = data.auxiliary.geojson;
  return (
    <MapContainer
      bounds={gjson.properties.bounds}
      className="h-48"
      scrollWheelZoom={false}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors"
      />
      <GeoJSON data={gjson} />
    </MapContainer>
  );
}
