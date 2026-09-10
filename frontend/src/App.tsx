import { useCallback, useState } from 'react'
import MapInterface from './components/MapInterface'
import AnalysisPanel from './components/AnalysisPanel'
import Sidebar from './components/Sidebar'
import './App.css'

function App() {
  const [selectedLocation, setSelectedLocation] = useState<{
    latitude: number
    longitude: number
    bbox?: [number, number, number, number]
    name?: string
  } | null>(null)

  const handleLocationSelect = useCallback((location: {
    latitude: number
    longitude: number
    bbox?: [number, number, number, number]
    name?: string
  }) => setSelectedLocation(location), [])
  
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0])

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <h1 className="app-title">UPRISER</h1>
        </div>
        <div className="header-right">
          <button className="header-btn">Settings</button>
        </div>
      </header>

      <div className="app-main">
        <Sidebar
          selectedLocation={selectedLocation}
          selectedDate={selectedDate}
          onDateChange={setSelectedDate}
        />

        <div className="map-container">
          <MapInterface
            onLocationSelect={handleLocationSelect}
            selectedLocation={selectedLocation}
          />
        </div>

        <AnalysisPanel
          selectedLocation={selectedLocation}
          selectedDate={selectedDate}
        />
      </div>
    </div>
  )
}

export default App