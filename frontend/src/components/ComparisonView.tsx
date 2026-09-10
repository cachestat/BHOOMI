import { useState, useRef } from 'react'
import './ComparisonView.css'
import { ChangeAnalysisResponse } from '../types'

interface ComparisonViewProps {
  selectedLocation: {
    latitude: number
    longitude: number
    bbox?: [number, number, number, number]
    name?: string
  } | null
  dateBefore: string
  dateAfter: string
  changeResult: ChangeAnalysisResponse | null
}

export default function ComparisonView({
  selectedLocation,
  dateBefore,
  dateAfter,
  changeResult
}: ComparisonViewProps) {
  const [sliderPosition, setSliderPosition] = useState(50)
  const containerRef = useRef<HTMLDivElement>(null)

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSliderPosition(parseInt(e.target.value))
  }

  if (!selectedLocation) {
    return (
      <div className="comparison-view empty">
        <div className="empty-state">
          <p>Select a location on the map to compare imagery</p>
        </div>
      </div>
    )
  }

  return (
    <div className="comparison-view">
      <div className="comparison-header">
        <h3>Before / After Comparison</h3>
        <div className="comparison-meta">
          <span className="meta-item before">
            <strong>Before:</strong> {dateBefore}
          </span>
          <span className="meta-item after">
            <strong>After:</strong> {dateAfter}
          </span>
          <span className="meta-item">
            <strong>Location:</strong> {selectedLocation.name || 'Custom'}
          </span>
        </div>
      </div>

      <div className="comparison-container" ref={containerRef}>
        <div className="comparison-slider-wrapper">
          <div
            className="comparison-image before"
            style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
          >
              <div className="demo-image-placeholder before-art">
              <div className="placeholder-content">
                <p className="placeholder-icon">🛰️</p>
                <p className="placeholder-text">Before: {dateBefore}</p>
                <p className="placeholder-subtext">{selectedLocation.name || 'Selected Area'}</p>
              </div>
            </div>
          </div>

          <div
            className="comparison-image after"
            style={{ clipPath: `inset(0 0 0 ${sliderPosition}%)` }}
          >
              <div className="demo-image-placeholder after-art">
              <div className="placeholder-content">
                <p className="placeholder-icon">🛰️</p>
                <p className="placeholder-text">After: {dateAfter}</p>
                <p className="placeholder-subtext">{selectedLocation.name || 'Selected Area'}</p>
              </div>
            </div>
          </div>

          <div
            className="comparison-slider-handle"
            style={{ left: `${sliderPosition}%` }}
          >
            <div className="slider-line"></div>
            <div className="slider-button">
              <span className="slider-arrows">◀ ▶</span>
            </div>
          </div>

          <input
            type="range"
            min="0"
            max="100"
            value={sliderPosition}
            onChange={handleSliderChange}
            className="comparison-slider-input"
          />
        </div>
      </div>

      {changeResult && <div className="change-summary"><strong>{changeResult.changed_regions.length} change regions detected</strong><span>{changeResult.summary}</span></div>}

      <div className="comparison-actions">
        <button className="action-btn">Detect Changes</button>
        <button className="action-btn primary">Find Construction</button>
        <button className="action-btn">Generate Report</button>
      </div>
    </div>
  )
}