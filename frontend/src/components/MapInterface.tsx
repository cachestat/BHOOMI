import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import './MapInterface.css'

interface MapInterfaceProps {
  onLocationSelect: (location: {
    latitude: number
    longitude: number
    bbox?: [number, number, number, number]
    name?: string
  }) => void
  selectedLocation: {
    latitude: number
    longitude: number
    bbox?: [number, number, number, number]
    name?: string
  } | null
}

export default function MapInterface({ onLocationSelect, selectedLocation }: MapInterfaceProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [satelliteEnabled, setSatelliteEnabled] = useState(true)
  const [buildingsEnabled, setBuildingsEnabled] = useState(true)

  const refreshBuildings = async () => {
    const currentMap = map.current
    if (!currentMap || currentMap.getZoom() < 12) return

    const bounds = currentMap.getBounds()
    const query = `[out:json][timeout:15];(way[building](${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()}););out geom;`

    try {
      const response = await fetch('https://overpass-api.de/api/interpreter', {
        method: 'POST',
        body: `data=${encodeURIComponent(query)}`,
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      if (!response.ok) return
      const data = await response.json()
      const features = data.elements
        .filter((element: { geometry?: Array<{ lat: number; lon: number }> }) => (element.geometry?.length ?? 0) >= 3)
        .map((element: { id: number; geometry: Array<{ lat: number; lon: number }> }) => ({
          type: 'Feature',
          properties: {},
          geometry: {
            type: 'Polygon',
            coordinates: [[...element.geometry.map(point => [point.lon, point.lat]), [element.geometry[0].lon, element.geometry[0].lat]]],
          },
        }))
      const source = currentMap.getSource('buildings') as maplibregl.GeoJSONSource | undefined
      source?.setData({ type: 'FeatureCollection', features })
    } catch {
      // The map remains usable when the optional building service is unavailable.
    }
  }

  useEffect(() => {
    if (!mapContainer.current) return

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          satellite: {
            type: 'raster',
            tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
            tileSize: 256,
            attribution: 'Esri, Maxar, Earthstar Geographics',
            maxzoom: 19,
          },
          buildings: {
            type: 'geojson',
            data: { type: 'FeatureCollection', features: [] },
          },
        },
        layers: [
          { id: 'satellite', type: 'raster', source: 'satellite' },
          { id: 'building-fill', type: 'fill', source: 'buildings', paint: { 'fill-color': '#f3c969', 'fill-opacity': 0.42 } },
          { id: 'building-outline', type: 'line', source: 'buildings', paint: { 'line-color': '#8b4a2f', 'line-width': 1 } },
        ],
      },
      center: [0, 20],
      zoom: 2,
    })

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right')
    map.current.addControl(new maplibregl.ScaleControl(), 'bottom-left')

    map.current.on('load', refreshBuildings)
    map.current.on('moveend', refreshBuildings)

    map.current.on('click', (e) => {
      const { lng, lat } = e.lngLat
      const halfHeight = 0.00575
      const halfWidth = halfHeight / Math.max(Math.cos(lat * Math.PI / 180), 0.2)
      onLocationSelect({
        latitude: lat,
        longitude: lng,
        bbox: [
          lng - halfWidth,
          lat - halfHeight,
          lng + halfWidth,
          lat + halfHeight
        ]
      })
      map.current?.flyTo({ center: [lng, lat], zoom: 14, duration: 1000 })
    })

    return () => {
      map.current?.off('load', refreshBuildings)
      map.current?.off('moveend', refreshBuildings)
      map.current?.remove()
    }
  }, [onLocationSelect])

  useEffect(() => {
    if (selectedLocation && map.current) {
      map.current.flyTo({
        center: [selectedLocation.longitude, selectedLocation.latitude],
        duration: 1000
      })
    }
  }, [selectedLocation])

  const handleSearch = async () => {
    if (!searchQuery.trim() || !map.current) return

    const response = await fetch(`https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=${encodeURIComponent(searchQuery)}`)
    if (!response.ok) return
    const [result] = await response.json() as Array<{ lat: string; lon: string; display_name: string; boundingbox?: string[] }>
    if (!result) return

    const latitude = Number(result.lat)
    const longitude = Number(result.lon)
    const halfHeight = 0.00575
    const halfWidth = halfHeight / Math.max(Math.cos(latitude * Math.PI / 180), 0.2)
    const bbox = [longitude - halfWidth, latitude - halfHeight, longitude + halfWidth, latitude + halfHeight] as [number, number, number, number]
    map.current.flyTo({ center: [longitude, latitude], zoom: 14, duration: 1000 })
    onLocationSelect({ latitude, longitude, name: result.display_name, bbox })
  }

  return (
    <div className="map-interface">
      <div className="map-search">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search location..."
          className="map-search-input"
        />
        <button onClick={handleSearch} className="map-search-btn">
          Search
        </button>
      </div>
      <div className="map-layers" aria-label="Map layers">
        <button className={satelliteEnabled ? 'active' : ''} onClick={() => {
          const enabled = !satelliteEnabled
          setSatelliteEnabled(enabled)
          map.current?.setLayoutProperty('satellite', 'visibility', enabled ? 'visible' : 'none')
        }}>Satellite</button>
        <button className={buildingsEnabled ? 'active' : ''} onClick={() => {
          const enabled = !buildingsEnabled
          setBuildingsEnabled(enabled)
          map.current?.setLayoutProperty('building-fill', 'visibility', enabled ? 'visible' : 'none')
          map.current?.setLayoutProperty('building-outline', 'visibility', enabled ? 'visible' : 'none')
        }}>Buildings</button>
      </div>
      <div ref={mapContainer} className="map-container" />
      {selectedLocation && (
        <div className="map-info">
          <div className="map-info-item">
            <strong>Location:</strong> {selectedLocation.name || `${selectedLocation.latitude.toFixed(4)}, ${selectedLocation.longitude.toFixed(4)}`}
          </div>
          <div className="map-info-item">
            <strong>Lat:</strong> {selectedLocation.latitude.toFixed(4)}
          </div>
          <div className="map-info-item">
            <strong>Lng:</strong> {selectedLocation.longitude.toFixed(4)}
          </div>
        </div>
      )}
    </div>
  )
}