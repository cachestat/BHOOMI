import './Sidebar.css'

interface SidebarProps {
  selectedLocation: {
    latitude: number
    longitude: number
    bbox?: [number, number, number, number]
    name?: string
  } | null
  selectedDate: string
  onDateChange: (date: string) => void
}

export default function Sidebar({
  selectedLocation,
  selectedDate,
  onDateChange,
}: SidebarProps) {
  return (
    <div className="sidebar">
      <div className="sidebar-section">
        <h3 className="sidebar-title">Location</h3>
        <div className="sidebar-content">
          {selectedLocation ? (
            <>
              <div className="sidebar-info">
                <strong>Name:</strong> {selectedLocation.name || 'Custom Location'}
              </div>
              <div className="sidebar-info">
                <strong>Latitude:</strong> {selectedLocation.latitude.toFixed(4)}
              </div>
              <div className="sidebar-info">
                <strong>Longitude:</strong> {selectedLocation.longitude.toFixed(4)}
              </div>
            </>
          ) : (
            <p className="sidebar-hint">Select a location on the map</p>
          )}
        </div>
      </div>

      <div className="sidebar-section">
        <h3 className="sidebar-title">Imagery</h3>
        <div className="sidebar-content">
          <div className="sidebar-info"><strong>Source:</strong> Sentinel-2 L1C TCI</div>
          <div className="sidebar-field">
            <label>Date:</label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => onDateChange(e.target.value)}
              className="sidebar-input"
            />
          </div>
          <div className="sidebar-info"><strong>Resolution:</strong> 10 m input</div>
        </div>
      </div>

    </div>
  )
}