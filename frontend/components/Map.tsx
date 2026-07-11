"use client";

import { useEffect, useState } from "react";
import L from "leaflet";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// Fix for default Leaflet marker icons in Next.js/Webpack
const fixLeafletIcon = () => {
  delete (L.Icon.Default.prototype as any)._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
    iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
  });
};

// Custom icons using standard emojis inside divs for visual clarity
const createEmojiIcon = (emoji: string, color: string) => {
  return L.divIcon({
    html: `<div style="background-color: ${color}; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3); font-size: 16px;">${emoji}</div>`,
    className: "custom-emoji-icon",
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16]
  });
};

const policeIcon = createEmojiIcon("🚨", "#3b82f6"); // Blue background
const hospitalIcon = createEmojiIcon("🏥", "#ef4444"); // Red background
const reportIcon = createEmojiIcon("⚠️", "#f59e0b"); // Orange background
const originIcon = createEmojiIcon("🟢", "#10b981"); // Green circle
const destIcon = createEmojiIcon("🏁", "#8b5cf6"); // Purple flag
const generalRiskIcon = createEmojiIcon("🛑", "#ef4444");

// Helper to center/zoom map when coordinates change
function ChangeView({ center, zoom, bounds }: { center: [number, number]; zoom: number; bounds?: L.LatLngBoundsExpression }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50] });
    } else {
      map.setView(center, zoom);
    }
  }, [center, zoom, bounds, map]);
  return null;
}

// Click event listener component
function MapClickEvents({ onMapClick }: { onMapClick?: (lat: number, lon: number) => void }) {
  useMapEvents({
    click(e) {
      if (onMapClick) {
        onMapClick(e.latlng.lat, e.latlng.lng);
      }
    },
  });
  return null;
}

interface MapProps {
  originCoords?: { latitude: number; longitude: number } | null;
  destinationCoords?: { latitude: number; longitude: number } | null;
  primaryRoute?: any;
  alternativeRoute?: any;
  reports?: any[];
  emergencyResources?: any[];
  onMapClick?: (lat: number, lon: number) => void;
}

export default function Map({
  originCoords,
  destinationCoords,
  primaryRoute,
  alternativeRoute,
  reports = [],
  emergencyResources = [],
  onMapClick
}: MapProps) {
  const [mapCenter, setMapCenter] = useState<[number, number]>([18.5204, 73.8567]); // Default Pune
  const [mapZoom, setMapZoom] = useState<number>(12);
  const [mapBounds, setMapBounds] = useState<L.LatLngBoundsExpression | undefined>(undefined);

  useEffect(() => {
    fixLeafletIcon();
  }, []);

  // Update map viewport when coordinates change
  useEffect(() => {
    const latLngs: L.LatLng[] = [];

    if (originCoords) {
      latLngs.push(L.latLng(originCoords.latitude, originCoords.longitude));
    }
    if (destinationCoords) {
      latLngs.push(L.latLng(destinationCoords.latitude, destinationCoords.longitude));
    }

    if (latLngs.length > 0) {
      if (latLngs.length === 1) {
        setMapCenter([latLngs[0].lat, latLngs[0].lng]);
        setMapZoom(14);
        setMapBounds(undefined);
      } else {
        const bounds = L.latLngBounds(latLngs);
        setMapBounds(bounds.toBBoxString() ? [[bounds.getSouthWest().lat, bounds.getSouthWest().lng], [bounds.getNorthEast().lat, bounds.getNorthEast().lng]] : undefined);
      }
    }
  }, [originCoords, destinationCoords]);

  // Decode GeoJSON LineString coordinates into Leaflet format: [lat, lon]
  const parseRouteCoords = (geometry: any): [number, number][] => {
    if (!geometry || !geometry.coordinates) return [];
    return geometry.coordinates.map((coord: number[]) => [coord[1], coord[0]]);
  };

  // Helper to determine route segment color based on its score
  const getSegmentColor = (score: number) => {
    if (score >= 7.5) return "#10b981"; // Green (Safe)
    if (score >= 4.5) return "#f59e0b"; // Yellow (Caution)
    return "#ef4444"; // Red (High Risk)
  };

  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      <MapContainer 
        center={mapCenter} 
        zoom={mapZoom} 
        style={{ width: "100%", height: "100%" }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <ChangeView center={mapCenter} zoom={mapZoom} bounds={mapBounds} />
        <MapClickEvents onMapClick={onMapClick} />

        {/* Origin Marker */}
        {originCoords && (
          <Marker position={[originCoords.latitude, originCoords.longitude]} icon={originIcon}>
            <Popup>
              <strong>Start Point</strong><br />
              Latitude: {originCoords.latitude.toFixed(4)}<br />
              Longitude: {originCoords.longitude.toFixed(4)}
            </Popup>
          </Marker>
        )}

        {/* Destination Marker */}
        {destinationCoords && (
          <Marker position={[destinationCoords.latitude, destinationCoords.longitude]} icon={destIcon}>
            <Popup>
              <strong>Destination Point</strong><br />
              Latitude: {destinationCoords.latitude.toFixed(4)}<br />
              Longitude: {destinationCoords.longitude.toFixed(4)}
            </Popup>
          </Marker>
        )}

        {/* Render Alternative Route (Blue/Dashed Line) */}
        {alternativeRoute && alternativeRoute.geometry && (
          <Polyline
            positions={parseRouteCoords(alternativeRoute.geometry)}
            color="#3b82f6"
            weight={4}
            opacity={0.6}
            dashArray="10, 10"
          >
            <Popup>
              <strong>Alternative Route</strong><br />
              Safety Score: {alternativeRoute.overall_score}/10 ({alternativeRoute.risk_level} Risk)
            </Popup>
          </Polyline>
        )}

        {/* Render Primary Route Segments (Colored according to safety score) */}
        {primaryRoute && primaryRoute.segments && primaryRoute.segments.map((seg: any, idx: number) => {
          const segCoords = seg.coordinates.map((coord: number[]) => [coord[1], coord[0]]);
          return (
            <Polyline
              key={`seg-${idx}`}
              positions={segCoords}
              color={getSegmentColor(seg.safety_score)}
              weight={6}
              opacity={0.85}
            >
              <Popup>
                <strong>Route Segment {idx + 1}</strong><br />
                Safety Rating: {seg.safety_score}/10<br />
                Risk Rating: <strong>{seg.risk_level}</strong><br />
                {seg.threats.length > 0 && (
                  <div>
                    <span style={{ color: "#ef4444", fontSize: "11px" }}>Threats:</span>
                    <ul style={{ margin: "5px 0 0 10px", padding: 0, fontSize: "11px" }}>
                      {seg.threats.map((t: string, i: number) => (
                        <li key={i}>{t}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </Popup>
            </Polyline>
          );
        })}

        {/* Render Community Reports */}
        {reports.map((report) => (
          <Marker
            key={`rep-${report.id}`}
            position={[report.latitude, report.longitude]}
            icon={reportIcon}
          >
            <Popup>
              <div style={{ maxWidth: "200px" }}>
                <strong>⚠️ {report.report_type}</strong><br />
                <span style={{ fontSize: "11px", color: "#64748b" }}>{report.location}</span><br />
                <p style={{ margin: "5px 0 0 0", fontSize: "12px" }}>{report.description || "No description provided."}</p>
                <span style={{ fontSize: "10px", display: "block", marginTop: "5px", color: "#94a3b8" }}>
                  Reported on: {new Date(report.created_at).toLocaleDateString()}
                </span>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Render Emergency Resources */}
        {emergencyResources.map((resource, idx) => {
          const isPolice = resource.resource_type === "Police Station";
          return (
            <Marker
              key={`em-${idx}`}
              position={[resource.latitude, resource.longitude]}
              icon={isPolice ? policeIcon : hospitalIcon}
            >
              <Popup>
                <strong>{isPolice ? "🚨" : "🏥"} {resource.name}</strong><br />
                <span style={{ fontSize: "11px", color: "#64748b" }}>Type: {resource.resource_type}</span><br />
                {resource.address && <span style={{ fontSize: "11px", display: "block" }}>Address: {resource.address}</span>}
                {resource.contact_info && resource.contact_info !== "N/A" && (
                  <span style={{ fontSize: "11px", display: "block" }}>Phone: {resource.contact_info}</span>
                )}
                {resource.distance_meters !== undefined && (
                  <span style={{ fontSize: "11px", fontWeight: "bold", color: "#4f46e5" }}>
                    Distance: {resource.distance_meters}m
                  </span>
                )}
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
      
      <div className="map-hint">
        💡 Double-click or click anywhere on the map to autofill coordinates in the Report form below.
      </div>
    </div>
  );
}
