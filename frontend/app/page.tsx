"use client";

import { useState, useEffect, type FormEvent } from "react";
import dynamic from "next/dynamic";
import { Shield, Compass, PlusCircle, BarChart3, Loader2 } from "lucide-react";
import SafetyForm from "../components/SafetyForm";
import ReportForm from "../components/ReportForm";
import AnalyticsPanel from "../components/AnalyticsPanel";

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
              <SafetyForm
                origin={origin}
                destination={destination}
                travelTime={travelTime}
                isAnalyzing={isAnalyzing}
                analysisError={analysisError}
                safetyResult={safetyResult}
                emergencyResources={emergencyResources}
                onOriginChange={setOrigin}
                onDestinationChange={setDestination}
                onTravelTimeChange={setTravelTime}
                onAnalyze={handleSafetyAnalysis}
              />
            </>
          )}

          {/* TAB 2: SUBMIT A REPORT */}
          {activeTab === "report" && (
            <ReportForm
              reportLocation={reportLocation}
              reportLat={reportLat}
              reportLon={reportLon}
              reportType={reportType}
              reportDesc={reportDesc}
              isSubmittingReport={isSubmittingReport}
              reportSuccess={reportSuccess}
              reportError={reportError}
              onReportLocationChange={setReportLocation}
              onReportLatChange={setReportLat}
              onReportLonChange={setReportLon}
              onReportTypeChange={setReportType}
              onReportDescChange={setReportDesc}
              onSubmit={handleReportSubmit}
            />
          )}

          {/* TAB 3: ADMIN SAFETY ANALYTICS */}
          {activeTab === "analytics" && (
            <AnalyticsPanel isLoadingAnalytics={isLoadingAnalytics} analyticsData={analyticsData} />
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
