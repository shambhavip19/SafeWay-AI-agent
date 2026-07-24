"use client";

import { AlertTriangle, CheckCircle2, Compass, HeartPulse, Info, Loader2, Navigation, PhoneCall, Shield } from "lucide-react";
import type { FormEvent } from "react";

interface SafetyFormProps {
  origin: string;
  destination: string;
  travelTime: string;
  isAnalyzing: boolean;
  analysisError: string;
  safetyResult: any;
  emergencyResources: any[];
  onOriginChange: (value: string) => void;
  onDestinationChange: (value: string) => void;
  onTravelTimeChange: (value: string) => void;
  onAnalyze: (event: FormEvent, isRouteOnly: boolean) => void;
}

export default function SafetyForm({
  origin,
  destination,
  travelTime,
  isAnalyzing,
  analysisError,
  safetyResult,
  emergencyResources,
  onOriginChange,
  onDestinationChange,
  onTravelTimeChange,
  onAnalyze,
}: SafetyFormProps) {
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
    <>
      <div className="card">
        <h2 className="section-title">
          <Navigation size={20} />
          Travel Safety Planner
        </h2>
        <p className="panel-intro">
          Compare a planned route against local safety signals, emergency coverage, and recent community reports.
        </p>

        <form onSubmit={(event) => onAnalyze(event, true)}>
          <div className="form-group">
            <label htmlFor="origin">Origin (Start Point)</label>
            <input
              id="origin"
              type="text"
              className="form-input"
              placeholder="e.g. Baner, Pune"
              value={origin}
              onChange={(event) => onOriginChange(event.target.value)}
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
              onChange={(event) => onDestinationChange(event.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="travelTime">Departure Date & Time</label>
            <input
              id="travelTime"
              type="datetime-local"
              className="form-input"
              value={travelTime}
              onChange={(event) => onTravelTimeChange(event.target.value)}
            />
          </div>

          {analysisError ? (
            <div className="alert alert-danger">⚠️ {analysisError}</div>
          ) : null}

          <div className="action-row">
            <button type="submit" className="btn btn-primary" disabled={isAnalyzing}>
              {isAnalyzing ? (
                <>
                  <Loader2 className="animate-spin" size={16} />
                  Analyzing Route...
                </>
              ) : (
                "Analyze Route"
              )}
            </button>

            <button type="button" className="btn btn-secondary" disabled={isAnalyzing} onClick={(event) => onAnalyze(event as unknown as FormEvent, false)}>
              Check Area Only
            </button>
          </div>
        </form>
      </div>

      {safetyResult ? (
        <div className={`card ${getScoreColorClass(safetyResult.score)}`} style={{ borderColor: safetyResult.score >= 7.5 ? "var(--success)" : safetyResult.score >= 4.5 ? "var(--warning)" : "var(--danger)" }}>
          <div className="result-header">
            <div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: "700" }}>Safety Assessment</h3>
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                Generated at {travelTime ? new Date(travelTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "now"}
              </span>
            </div>

            <div style={{ textAlign: "right" }}>
              <div className="score-display">
                <span className="score-number" style={{ color: safetyResult.score >= 7.5 ? "var(--success)" : safetyResult.score >= 4.5 ? "var(--warning)" : "var(--danger)" }}>
                  {safetyResult.score}
                </span>
                <span className="score-max">/10</span>
              </div>
              <span className={`badge ${getBadgeClass(safetyResult.risk_level)}`}>{safetyResult.risk_level} Risk</span>
            </div>
          </div>

          {safetyResult.threats && safetyResult.threats.length > 0 ? (
            <div style={{ marginBottom: "1.25rem" }}>
              <h4 className="subsection-title">Detected Threat Signatures:</h4>
              <div className="threat-list">
                {safetyResult.threats.map((threat: string, index: number) => (
                  <div className="threat-item" key={`${threat}-${index}`}>
                    <AlertTriangle size={14} />
                    <span>{threat}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {safetyResult.recommendation ? (
            <div className="panel-section">
              <h4 className="subsection-title">
                <Info size={14} />
                AI Travel Advice
              </h4>
              <div className="recommendation-content">
                <div dangerouslySetInnerHTML={{ __html: safetyResult.recommendation.replace(/\n\n/g, "<p></p>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/### (.*?)\n/g, "<h4>$1</h4>").replace(/\* (.*?)\n/g, "<li>$1</li>") }} />
              </div>
            </div>
          ) : null}

          {emergencyResources && emergencyResources.length > 0 ? (
            <div className="panel-section">
              <h4 className="subsection-title">
                <PhoneCall size={14} />
                Nearest Emergency Resources
              </h4>
              <div className="resource-list">
                {emergencyResources.slice(0, 3).map((resource: any, index: number) => {
                  const isPolice = resource.resource_type === "Police Station";
                  return (
                    <div className="resource-item" key={`${resource.name}-${index}`}>
                      <div>
                        <div className="resource-name" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                          {isPolice ? <Shield size={14} color="#3b82f6" /> : <HeartPulse size={14} color="#ef4444" />}
                          {resource.name}
                        </div>
                        <div className="resource-meta">
                          {resource.resource_type} • {resource.address || "Nearby"}
                        </div>
                      </div>
                      <div className="resource-distance">{resource.distance_meters}m</div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
