import './ImageDisplay.css'
import { ChangeAnalysisResponse } from '../types'

interface ImageDisplayProps {
  selectedLocation: {
    latitude: number
    longitude: number
    bbox?: [number, number, number, number]
    name?: string
  } | null
  changeResult: ChangeAnalysisResponse | null
}

export default function ImageDisplay({
  selectedLocation,
  changeResult
}: ImageDisplayProps) {
  if (!selectedLocation) {
    return (
      <div className="image-display empty">
        <div className="empty-state">
          <p>Select a location on the map to view satellite imagery</p>
        </div>
      </div>
    )
  }

  return (
    <div className="image-display">
      <div className="image-header">
        <h3>Satellite Imagery</h3>
        <div className="image-meta">
          <span className="meta-item"><strong>Date:</strong> latest demo capture</span>
          <span className="meta-item"><strong>Source:</strong> Sentinel-2 / demo</span>
          <span className="meta-item">
            <strong>Location:</strong> {selectedLocation.name || 'Custom'}
          </span>
        </div>
      </div>

      <div className="image-container">
        <div className="satellite-canvas">
          <div className="terrain terrain-one" /><div className="terrain terrain-two" /><div className="road road-one" /><div className="road road-two" />
          <div className="image-stamp">DEMO MOSAIC / 10 m<br /><strong>{selectedLocation.name || 'SELECTED AOI'}</strong></div>
          {changeResult?.changed_regions.slice(0, 4).map((region, index) => <div className="region-marker" style={{ left: `${24 + index * 17}%`, top: `${31 + (index % 2) * 25}%` }} key={region.id}>{index + 1}</div>)}
        </div>
      </div>

      <div className="image-actions">
        <button className="action-btn">Export snapshot</button>
        <button className="action-btn">View metadata</button>
      </div>
    </div>
  )
}