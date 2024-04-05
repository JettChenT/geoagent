import {
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
  GeoJSON,
  GeoJSONProps,
} from "react-leaflet";

import { toast } from "@/components/ui/use-toast";
import { Copy, Map, Earth } from "lucide-react";

import { ContextData } from "../ContextNode";

export default function DisplayResults({ data }: { data: ContextData }) {
  if (data.transition.type !== "AgentAction") {
    return null;
  }
  let coords = data.transition.tool_input.split(",");
  let x = parseFloat(coords[0]);
  let y = parseFloat(coords[1]);
  return (
    <div className="text-left border-2 border-solid border-gray-200 rounded-sm p-1">
      <MapContainer
        center={[x, y]}
        zoom={15}
        className="h-48"
        scrollWheelZoom={false}
        dragging={false}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors"
        />
        <Marker position={[x, y]}>
          <Popup>
            {x}, {y}
          </Popup>
        </Marker>
      </MapContainer>
      <span className="text-base text-gray-500 font-mono mt-1 block">
        {"["}
        {x.toFixed(4)}, {y.toFixed(4)}
        {"]"}
      </span>
      <button
        onClick={() => {
          navigator.clipboard.writeText(`${x},${y}`);
          toast({
            title: "Coordinates copied to clipboard",
            description: `${x},${y}`,
            duration: 1000,
          });
        }}
        className="text-blue-500 hover:text-blue-700 text-sm font-mono hover:underline items-center"
      >
        <Copy size={13} className="inline-block mr-1 -mt-1" />
        Copy Coordinates
      </button>
      <br />
      <a
        href={`https://www.google.com/maps/search/?api=1&query=${x},${y}`}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-2 text-blue-500 hover:text-blue-700 text-sm font-mono hover:underline items-center"
      >
        <Map size={13} className="inline-block mr-1 -mt-0.5" />
        Google Maps
      </a>
      <br />
      <a
        href={`https://earth.google.com/web/search/${x},${y}`}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-2 text-blue-500 hover:text-blue-700 text-sm font-mono hover:underline  items-center"
      >
        <Earth size={13} className="inline-block mr-1 -mt-1" />
        Google Earth
      </a>
    </div>
  );
}
