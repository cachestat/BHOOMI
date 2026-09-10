import { useState } from 'react'
import './AnalysisPanel.css'
import { SuperResolutionResult } from '../types'
import { generateSuperResolution } from '../services/api'

interface AnalysisPanelProps {
  selectedLocation: {
    latitude: number
    longitude: number
    bbox?: [number, number, number, number]
    name?: string
  } | null
  selectedDate: string
}

export default function AnalysisPanel({
  selectedLocation,
  selectedDate
}: AnalysisPanelProps) {
  const [result, setResult] = useState<SuperResolutionResult | null>(null)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState('')
  const [expandedImage, setExpandedImage] = useState<{ title: string; src: string } | null>(null)
  const [cacheKey, setCacheKey] = useState(0)
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
  const runSR = async () => {
    setProcessing(true)
    setError('')
    try { setResult(await generateSuperResolution(selectedLocation!, selectedDate)); setCacheKey(Date.now()) }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'SR processing failed.') }
    finally { setProcessing(false) }
  }
  return (
    <div className="analysis-panel">
      <div className="analysis-tabs">
        <button className="tab-btn active">Super-resolution mapping</button>
      </div>

      <div className="analysis-content">
        {processing && (
          <div className="loading-overlay">
            <div className="loading-spinner"></div>
            <p className="loading-message">Running overlapping tile inference...</p>
          </div>
        )}
        <div className="srm-workspace">
          <p className="srm-kicker">Sentinel-2 spatial detail</p>
          <h2>Original vs super-resolved</h2>
          <p className="srm-copy">Process a small Sentinel-2 tile through the trained 4x ESRGAN model. Output detail is generated at a nominal 2.5 m grid and must be validated against high-resolution reference imagery.</p>
          <button className="srm-button" disabled={!selectedLocation || processing} onClick={runSR}>
            {processing ? 'Processing...' : 'Generate Super Resolution'}
          </button>
          {!selectedLocation && <p className="srm-note">Select an area on the map to begin.</p>}
          {error && <p className="srm-error">{error}</p>}
          {result && <>
            <div className="srm-meta"><span><strong>Model</strong>{result.model}</span><span><strong>Input</strong>{result.input_width} x {result.input_height} px at {result.input_resolution_m} m</span><span><strong>Output</strong>{result.output_width} x {result.output_height} px at {result.output_resolution_m} m nominal</span><span><strong>Scale</strong>{result.scale}x</span><span><strong>Time</strong>{result.processing_time_seconds}s</span></div>
            <div className="srm-comparison"><div><span>Original</span><img onClick={() => setExpandedImage({ title: 'Original Sentinel-2', src: `${apiUrl}${result.input_preview_url}?v=${cacheKey}` })} src={`${apiUrl}${result.input_preview_url}?v=${cacheKey}`} /></div><div><span>SR output</span><img onClick={() => setExpandedImage({ title: 'Satlas ESRGAN output', src: `${apiUrl}${result.output_preview_url}?v=${cacheKey}` })} src={`${apiUrl}${result.output_preview_url}?v=${cacheKey}`} /></div></div>
            <div className="srm-downloads"><a href={`${apiUrl}${result.input_url}`} download>Download original GeoTIFF</a><a href={`${apiUrl}${result.output_url}`} download>Download SR GeoTIFF</a></div>
            <p className="srm-note">{result.validation_message || `PSNR ${result.metrics?.psnr} | SSIM ${result.metrics?.ssim}`}</p>
          </>}
        </div>
        {expandedImage && <div className="srm-modal-backdrop" onClick={() => setExpandedImage(null)} role="presentation">
          <div className="srm-modal" onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true" aria-label={expandedImage.title}>
            <div className="srm-modal-header"><strong>{expandedImage.title}</strong><button onClick={() => setExpandedImage(null)} aria-label="Close image viewer">Close</button></div>
            <img src={expandedImage.src} alt={expandedImage.title} />
          </div>
        </div>}
      </div>
    </div>
  )
}