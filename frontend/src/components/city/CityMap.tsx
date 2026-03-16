"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";

export function CityMap({ latitude, longitude, name }: { latitude: number | null; longitude: number | null; name: string }) {
  const mapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!mapRef.current || latitude === null || longitude === null) {
      return;
    }

    const map = new maplibregl.Map({
      container: mapRef.current,
      style: "https://demotiles.maplibre.org/style.json",
      center: [longitude, latitude],
      zoom: 10
    });

    new maplibregl.Marker({ color: "#00e0ff" }).setLngLat([longitude, latitude]).setPopup(new maplibregl.Popup().setText(name)).addTo(map);

    return () => map.remove();
  }, [latitude, longitude, name]);

  return <div className="map" ref={mapRef} />;
}

