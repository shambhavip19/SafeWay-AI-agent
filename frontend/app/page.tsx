"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { 
  Shield, 
  MapPin, 
  AlertTriangle, 
  Navigation, 
  PlusCircle, 
  BarChart3, 
  Clock, 
  Loader2, 
  Compass, 
  PhoneCall, 
  HeartPulse, 
  Info,
  CheckCircle2
} from "lucide-react";

// Dynamically import Leaflet Map (requires window object, cannot be server-side rendered)
const Map = dynamic(() => import("../components/Map"), {
  ssr: false,
  loading: () => (
    <div className="map-placeholder">
      <Loader2 className="animate-spin" size={32} />
      <span style={{ marginLeft: "10px" }}>Loading Map Engine...</span>
    </div>
  ),
});

const API_BASE = "http://localhost:8000";

export default function Home() {
  // Navigation State
  const [activeTab, setActiveTab] = useState<"planner" | "report" | "analytics">("planner");
  
  // Map Data State
  const [originCoords, setOriginCoords] = useState<any>(null);
  const [destinationCoords, setDestinationCoords] = useState<any>(null);
  const [primaryRoute, setPrimaryRoute] = useState<any>(null);
  const [alternativeRoute, setAlternativeRoute] = useState<any>(null);
  const [allReports, setAllReports] = useState<any[]>([]);
  const [emergencyResources, setEmergencyResources] = useState<any[]>([]);

  // Planner Form State
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [travelTime, setTravelTime] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState("");
  const [safetyResult, setSafetyResult] = useState<any>(null);

  // Report Form State
  const [reportLocation, setReportLocation] = useState("");
  const [reportLat, setReportLat] = useState("");
  const [reportLon, setReportLon] = useState("");
  const [reportType, setReportType] = useState("Harassment");
  const [reportDesc, setReportDesc] = useState("");
  const [isSubmittingReport, setIsSubmittingReport] = useState(false);
  const [reportSuccess, setReportSuccess] = useState(false);
  const [reportError, setReportError] = useState("");

  // Admin Analytics State
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);

  // Load all reports on mount to display them on the map
  useEffect(() => {
    fetchRecentReports();
    // Pre-populate travelTime with current time
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    setTravelTime(now.toISOString().slice(0, 16));
  }, []);

  // Fetch recent reports from backend
  const fetchRecentReports = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/reports`);
      if (response.ok) {
        const data = await response.json();
        setAllReports(data);
      }
    } catch (e) {
      console.error("Error fetching reports:", e);
    }
  };

  // Fetch analytics data when analytics tab is opened
  const fetchAnalytics = async () => {
    setIsLoadingAnalytics(true);
    try {
      const response = await fetch(`${API_BASE}/api/analytics`);
      if (response.ok) {
        const data = await response.json();
        setAnalyticsData(data);
      }
    } catch (e) {
      console.error("Error fetching analytics:", e);
    } finally {
      setIsLoadingAnalytics(false);
    }
  };

  useEffect(() => {
    if (activeTab === "analytics") {
      fetchAnalytics();
    }
  }, [activeTab]);

  // Click handler on map to auto-fill reports
  const handleMapClick = (lat: number, lon: number) => {
    setReportLat(lat.toFixed(6));
    setReportLon(lon.toFixed(6));
    // Also perform reverse lookup mock or placeholder name
    setReportLocation(`Coordinates: ${lat.toFixed(4)}, ${lon.toFixed(4)}`);
    // Automatically switch to report tab so the user can easily submit!
    setActiveTab("report");
    setReportSuccess(false);
    setReportError("");
  };

  // Submit Safety / Route Analysis
  const handleSafetyAnalysis = async (e: React.FormEvent, isRouteOnly: boolean) => {
    e.preventDefault();
    if (!destination) {
      setAnalysisError("Destination is required.");
      return;
    }
    if (isRouteOnly && !origin) {
      setAnalysisError("Origin is required for route segment analysis.");
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError("");
    setSafetyResult(null);
    setPrimaryRoute(null);
    setAlternativeRoute(null);

    const payload = {
      origin: origin || "Your Location",
      destination: destination,
      event_time: new Date(travelTime).toISOString(),
    };

    const endpoint = isRouteOnly ? "api/route" : "api/analysis";

    try {
      const response = await fetch(`${API_BASE}/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const data = await response.json();
        
        if (isRouteOnly) {
          // Route analysis response
          setSafetyResult({
            score: data.primary_route.overall_score,
            risk_level: data.primary_route.risk_level,
            threats: data.primary_route.threats,
            recommendation: data.recommendation,
            police_count: data.primary_route.segments.reduce((acc: number, cur: any) => acc + (cur.police_count || 0), 0),
            hospital_count: data.primary_route.segments.reduce((acc: number, cur: any) => acc + (cur.hospital_count || 0), 0),
          });
          
          setOriginCoords(data.origin_coords);
          setDestinationCoords(data.destination_coords);
          setPrimaryRoute(data.primary_route);
          setAlternativeRoute(data.alternative_route);
          
          // Flatten emergency services from segments to show in panel
          const allResources: any[] = [];
          data.primary_route.segments.forEach((seg: any) => {
            if (seg.nearby_resources) {
              seg.nearby_resources.forEach((r: any) => {
                if (!allResources.some(res => res.name === r.name)) {
                  allResources.push(r);
                }
              });
            }
          });
          setEmergencyResources(allResources);
        } else {
          // Point analysis response
          setSafetyResult(data);
          setOriginCoords(null);
          setDestinationCoords({ latitude: data.latitude, longitude: data.longitude });
          setEmergencyResources(data.nearby_resources || []);
        }
      } else {
        const errorData = await response.json();
        setAnalysisError(errorData.detail || "Analysis request failed.");
      }
    } catch (err) {
      setAnalysisError("Network connection to backend failed. Make sure the FastAPI server is running on port 8000.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Submit Community Report
  const handleReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportLocation || !reportLat || !reportLon) {
      setReportError("Location description, latitude, and longitude are required. Click on the map to autofill coordinates.");
      return;
    }

    setIsSubmittingReport(true);
    setReportError("");
    setReportSuccess(false);

    const payload = {
      location: reportLocation,
      latitude: parseFloat(reportLat),
      longitude: parseFloat(reportLon),
      report_type: reportType,
      description: reportDesc || "",
    };

    try {
      const response = await fetch(`${API_BASE}/api/reports`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        setReportSuccess(true);
        setReportLocation("");
        setReportLat("");
        setReportLon("");
        setReportDesc("");
        // Reload all reports to update map markers
        fetchRecentReports();
      } else {
        const errData = await response.json();
        setReportError(errData.detail || "Failed to submit report.");
      }
    } catch (err) {
      setReportError("Connection failure with backend server.");
    } finally {
      setIsSubmittingReport(false);
    }
  };

  const getScoreColorClass = (score: number) => {
    if (score >= 7.5) return "score-success";
    if (score >= 4.5) return "score-warning";
    return "score-danger";
  };

  const getBadgeClass = (risk: string) => {
    if (risk.toLowerCase() === "low") return "badge-low";
    if (risk.toLowerCase() === "medium") return "badge-medium";
    return "badge-high";
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      {/* HEADER */}
      <header>
        <div className="logo">
          <Shield size={28} />
          <span>SafeWay</span>
          <span style={{ fontSize: "0.75rem", background: "var(--primary-light)", color: "var(--primary-color)", padding: "2px 6px", borderRadius: "4px" }}>AI</span>
        </div>
        
        <div className="nav-tabs">
          <button 
            className={`nav-tab ${activeTab === "planner" ? "active" : ""}`}
            onClick={() => setActiveTab("planner")}
          >
            <Compass size={16} style={{ marginRight: "6px", verticalAlign: "middle" }} />
            Travel Planner
          </button>
          
          <button 
            className={`nav-tab ${activeTab === "report" ? "active" : ""}`}
            onClick={() => setActiveTab("report")}
          >
            <PlusCircle size={16} style={{ marginRight: "6px", verticalAlign: "middle" }} />
            Report Incident
          </button>
          
          <button 
            className={`nav-tab ${activeTab === "analytics" ? "active" : ""}`}
            onClick={() => setActiveTab("analytics")}
          >
            <BarChart3 size={16} style={{ marginRight: "6px", verticalAlign: "middle" }} />
            Safety Analytics
          </button>
        </div>
      </header>

      {/* BODY */}
      <main className="main-container">
        
        {/* SIDEBAR CONTROL PANEL */}
        <div className="sidebar">
          
          {/* TAB 1: TRAVEL SAFETY PLANNER */}
          {activeTab === "planner" && (
            <>
              <div className="card">
                <h2 className="section-title">
                  <Navigation size={20} />
                  Travel Safety Planner
                </h2>
                
                <form onSubmit={(e) => handleSafetyAnalysis(e, true)}>
                  <div className="form-group">
                    <label htmlFor="origin">Origin (Start Point)</label>
                    <input 
                      id="origin"
                      type="text" 
                      className="form-input" 
                      placeholder="e.g. Baner, Pune" 
                      value={origin}
                      onChange={(e) => setOrigin(e.target.value)}
                    />
                  </div>
                  
                  <div className="form-group">
                    <label htmlFor="destination">Destination (End Point) *</label>
                    <input 
                      id="destination"
                      type="text" 
                      className="form-input" 
                      placeholder="e.g. Shivajinagar, Pune" 
                      required
                      value={destination}
                      onChange={(e) => setDestination(e.target.value)}
                    />
                  </div>
                  
                  <div className="form-group">
                    <label htmlFor="travelTime">Departure Date & Time</label>
                    <input 
                      id="travelTime"
                      type="datetime-local" 
                      className="form-input" 
                      value={travelTime}
                      onChange={(e) => setTravelTime(e.target.value)}
                    />
                  </div>
                  
                  {analysisError && (
                    <div style={{ color: "var(--danger-text)", backgroundColor: "var(--danger-light)", padding: "10px", borderRadius: "6px", fontSize: "0.85rem", marginBottom: "15px" }}>
                      ⚠️ {analysisError}
                    </div>
                  )}

                  <div style={{ display: "flex", gap: "10px" }}>
                    <button 
                      type="submit" 
                      className="btn btn-primary"
                      disabled={isAnalyzing}
                      style={{ flexGrow: 1 }}
                    >
                      {isAnalyzing ? (
                        <>
                          <Loader2 className="animate-spin" size={16} />
                          Analyzing Route...
                        </>
                      ) : (
                        "Analyze Route"
                      )}
                    </button>
                    
                    <button 
                      type="button" 
                      className="btn btn-secondary"
                      disabled={isAnalyzing}
                      onClick={(e) => handleSafetyAnalysis(e, false)}
                      title="Quick Safety Check at Destination"
                    >
                      Check Area Only
                    </button>
                  </div>
                </form>
              </div>

              {/* SAFETY RESULTS BRIEFING */}
              {safetyResult && (
                <div className="card" style={{ borderColor: safetyResult.score >= 7.5 ? "var(--success)" : safetyResult.score >= 4.5 ? "var(--warning)" : "var(--danger)" }}>
                  <div className="result-header">
                    <div>
                      <h3 style={{ fontSize: "1.1rem", fontWeight: "700" }}>Safety Assessment</h3>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                        Generated at {new Date(travelTime).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                      </span>
                    </div>
                    
                    <div style={{ textAlign: "right" }}>
                      <div className="score-display">
                        <span className="score-number" style={{ color: safetyResult.score >= 7.5 ? "var(--success)" : safetyResult.score >= 4.5 ? "var(--warning)" : "var(--danger)" }}>
                          {safetyResult.score}
                        </span>
                        <span className="score-max">/10</span>
                      </div>
                      <span className={`badge ${getBadgeClass(safetyResult.risk_level)}`}>
                        {safetyResult.risk_level} Risk
                      </span>
                    </div>
                  </div>

                  {/* THREAT DETECTION ZONE */}
                  {safetyResult.threats && safetyResult.threats.length > 0 && (
                    <div style={{ marginBottom: "1.25rem" }}>
                      <h4 style={{ fontSize: "0.85rem", fontWeight: "600", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
                        Detected Threat Signatures:
                      </h4>
                      <div className="threat-list">
                        {safetyResult.threats.map((threat: string, idx: number) => (
                          <div className="threat-item" key={idx}>
                            <AlertTriangle size={14} />
                            <span>{threat}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* RECOMMENDATIONS */}
                  {safetyResult.recommendation && (
                    <div style={{ marginBottom: "1.25rem", borderTop: "1px solid var(--border-color)", paddingTop: "1rem" }}>
                      <h4 style={{ fontSize: "0.85rem", fontWeight: "600", color: "var(--text-secondary)", marginBottom: "0.25rem", display: "flex", alignItems: "center", gap: "4px" }}>
                        <Info size={14} />
                        AI Travel Advice
                      </h4>
                      <div className="recommendation-content">
                        {/* Check if HTML or Markdown and render simply */}
                        <div dangerouslySetInnerHTML={{ __html: safetyResult.recommendation
                          .replace(/\n\n/g, "<p></p>")
                          .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                          .replace(/### (.*?)\n/g, "<h4>$1</h4>")
                          .replace(/\* (.*?)\n/g, "<li>$1</li>")
                        }} />
                      </div>
                    </div>
                  )}

                  {/* CLOSEST EMERGENCY RESOURCES */}
                  {emergencyResources && emergencyResources.length > 0 && (
                    <div style={{ borderTop: "1px solid var(--border-color)", paddingTop: "1rem" }}>
                      <h4 style={{ fontSize: "0.85rem", fontWeight: "600", color: "var(--text-secondary)", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "6px" }}>
                        <PhoneCall size={14} />
                        Nearest Emergency Resources
                      </h4>
                      <div className="resource-list">
                        {emergencyResources.slice(0, 3).map((res: any, idx: number) => {
                          const isPolice = res.resource_type === "Police Station";
                          return (
                            <div className="resource-item" key={idx}>
                              <div>
                                <div className="resource-name" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                                  {isPolice ? <Shield size={14} color="#3b82f6" /> : <HeartPulse size={14} color="#ef4444" />}
                                  {res.name}
                                </div>
                                <div className="resource-meta">
                                  {res.resource_type} • {res.address || "Nearby"}
                                </div>
                              </div>
                              <div className="resource-distance">
                                {res.distance_meters}m
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* TAB 2: SUBMIT A REPORT */}
          {activeTab === "report" && (
            <div className="card">
              <h2 className="section-title">
                <PlusCircle size={20} />
                Report Incident
              </h2>
              
              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "1.25rem" }}>
                Submit a safety concern to help keep community route data accurate. Double-click the map on the right to auto-fill latitude and longitude coordinates.
              </p>

              <form onSubmit={handleReportSubmit}>
                <div className="form-group">
                  <label htmlFor="reportLocation">Location Name / Landmark *</label>
                  <input 
                    id="reportLocation"
                    type="text" 
                    className="form-input" 
                    placeholder="e.g. Near Jupiter Hospital, Baner" 
                    required
                    value={reportLocation}
                    onChange={(e) => setReportLocation(e.target.value)}
                  />
                </div>

                <div className="grid-cols-2">
                  <div className="form-group">
                    <label htmlFor="reportLat">Latitude *</label>
                    <input 
                      id="reportLat"
                      type="number" 
                      step="any"
                      className="form-input" 
                      placeholder="e.g. 18.5590"
                      required
                      value={reportLat}
                      onChange={(e) => setReportLat(e.target.value)}
                    />
                  </div>
                  
                  <div className="form-group">
                    <label htmlFor="reportLon">Longitude *</label>
                    <input 
                      id="reportLon"
                      type="number" 
                      step="any"
                      className="form-input" 
                      placeholder="e.g. 73.7925"
                      required
                      value={reportLon}
                      onChange={(e) => setReportLon(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="reportType">Concern Category *</label>
                  <select 
                    id="reportType"
                    className="form-input"
                    value={reportType}
                    onChange={(e) => setReportType(e.target.value)}
                    style={{ appearance: "auto" }}
                  >
                    <option value="Harassment">Harassment</option>
                    <option value="Suspicious Activity">Suspicious Activity</option>
                    <option value="Poor Lighting">Poor Lighting</option>
                    <option value="Unsafe Area">Unsafe Area</option>
                    <option value="Road Blockage">Road Blockage</option>
                    <option value="Theft">Theft</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="reportDesc">Description / Details</label>
                  <textarea 
                    id="reportDesc"
                    className="form-input" 
                    placeholder="Provide details about lighting conditions, time, or what specifically made the area feel unsafe." 
                    rows={4}
                    value={reportDesc}
                    onChange={(e) => setReportDesc(e.target.value)}
                    style={{ resize: "vertical", fontFamily: "inherit" }}
                  />
                </div>

                {reportError && (
                  <div style={{ color: "var(--danger-text)", backgroundColor: "var(--danger-light)", padding: "10px", borderRadius: "6px", fontSize: "0.85rem", marginBottom: "15px" }}>
                    ⚠️ {reportError}
                  </div>
                )}

                {reportSuccess && (
                  <div style={{ color: "var(--success-text)", backgroundColor: "var(--success-light)", padding: "10px", borderRadius: "6px", fontSize: "0.85rem", marginBottom: "15px", display: "flex", alignItems: "center", gap: "6px" }}>
                    <CheckCircle2 size={16} />
                    Safety report submitted successfully!
                  </div>
                )}

                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={isSubmittingReport}
                >
                  {isSubmittingReport ? (
                    <>
                      <Loader2 className="animate-spin" size={16} />
                      Submitting Report...
                    </>
                  ) : (
                    "Submit Report"
                  )}
                </button>
              </form>
            </div>
          )}

          {/* TAB 3: ADMIN SAFETY ANALYTICS */}
          {activeTab === "analytics" && (
            <div className="card">
              <h2 className="section-title">
                <BarChart3 size={20} />
                Safety Analytics
              </h2>

              {isLoadingAnalytics ? (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "40px 0" }}>
                  <Loader2 className="animate-spin" size={32} color="var(--primary-color)" />
                  <span style={{ marginTop: "10px", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                    Loading analytics matrices...
                  </span>
                </div>
              ) : analyticsData ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                  
                  {/* Totals Grid */}
                  <div className="grid-cols-2">
                    <div className="stat-box">
                      <div className="stat-value">{analyticsData.total_reports}</div>
                      <div className="stat-label">Reports Logged</div>
                    </div>
                    <div className="stat-box">
                      <div className="stat-value">
                        {analyticsData.daily_analyses.reduce((acc: number, cur: any) => acc + cur.count, 0)}
                      </div>
                      <div className="stat-label">Total Checks</div>
                    </div>
                  </div>

                  {/* Hotspots Section */}
                  <div>
                    <h4 style={{ fontSize: "0.85rem", fontWeight: "600", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
                      Top 5 Hotspot Areas:
                    </h4>
                    <div className="analytics-list">
                      {analyticsData.hotspot_locations.length > 0 ? (
                        analyticsData.hotspot_locations.map((item: any, idx: number) => (
                          <div className="analytics-item" key={idx}>
                            <span>{idx + 1}. {item.location}</span>
                            <span className="analytics-count">{item.count} reports</span>
                          </div>
                        ))
                      ) : (
                        <div style={{ fontSize: "0.825rem", color: "var(--text-secondary)", fontStyle: "italic" }}>
                          No community reports logged yet.
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Category Breakdown */}
                  <div>
                    <h4 style={{ fontSize: "0.85rem", fontWeight: "600", color: "var(--text-secondary)", marginBottom: "0.75rem" }}>
                      Incident Categories Distribution:
                    </h4>
                    <div className="chart-bar-container">
                      {analyticsData.report_categories.length > 0 ? (
                        analyticsData.report_categories.map((item: any, idx: number) => {
                          const maxCount = Math.max(...analyticsData.report_categories.map((c: any) => c.count)) || 1;
                          const percent = (item.count / maxCount) * 100;
                          return (
                            <div className="chart-row" key={idx}>
                              <span className="chart-label">{item.category}</span>
                              <div className="chart-bar-bg">
                                <div className="chart-bar-fill" style={{ width: `${percent}%` }} />
                              </div>
                              <span style={{ fontWeight: 600, width: "20px" }}>{item.count}</span>
                            </div>
                          );
                        })
                      ) : (
                        <div style={{ fontSize: "0.825rem", color: "var(--text-secondary)", fontStyle: "italic" }}>
                          No category statistics available.
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Common Threats */}
                  <div>
                    <h4 style={{ fontSize: "0.85rem", fontWeight: "600", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
                      Frequency of Threat Warnings:
                    </h4>
                    <div className="analytics-list">
                      {analyticsData.common_threats.map((item: any, idx: number) => (
                        <div className="analytics-item" key={idx}>
                          <span>{item.threat}</span>
                          <span style={{ fontWeight: 600 }}>{item.count} triggers</span>
                        </div>
                      ))}
                    </div>
                  </div>

                </div>
              ) : (
                <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", textAlign: "center", padding: "20px 0" }}>
                  Could not fetch analytics data. Check server connectivity.
                </div>
              )}
            </div>
          )}

        </div>

        {/* MAP PANEL */}
        <div className="map-container-wrapper">
          <Map 
            originCoords={originCoords}
            destinationCoords={destinationCoords}
            primaryRoute={primaryRoute}
            alternativeRoute={alternativeRoute}
            reports={allReports}
            emergencyResources={emergencyResources}
            onMapClick={handleMapClick}
          />
        </div>

      </main>
    </div>
  );
}
