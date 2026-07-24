"use client";

import { CheckCircle2, Loader2, PlusCircle } from "lucide-react";
import type { FormEvent } from "react";

interface ReportFormProps {
  reportLocation: string;
  reportLat: string;
  reportLon: string;
  reportType: string;
  reportDesc: string;
  isSubmittingReport: boolean;
  reportSuccess: boolean;
  reportError: string;
  onReportLocationChange: (value: string) => void;
  onReportLatChange: (value: string) => void;
  onReportLonChange: (value: string) => void;
  onReportTypeChange: (value: string) => void;
  onReportDescChange: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
}

export default function ReportForm({
  reportLocation,
  reportLat,
  reportLon,
  reportType,
  reportDesc,
  isSubmittingReport,
  reportSuccess,
  reportError,
  onReportLocationChange,
  onReportLatChange,
  onReportLonChange,
  onReportTypeChange,
  onReportDescChange,
  onSubmit,
}: ReportFormProps) {
  return (
    <div className="card">
      <h2 className="section-title">
        <PlusCircle size={20} />
        Report Incident
      </h2>

      <p className="panel-intro">
        Share local concerns so future trips can reflect the latest safety context. Clicking the map auto-fills the coordinates.
      </p>

      <form onSubmit={onSubmit}>
        <div className="form-group">
          <label htmlFor="reportLocation">Location Name / Landmark *</label>
          <input
            id="reportLocation"
            type="text"
            className="form-input"
            placeholder="e.g. Near Jupiter Hospital, Baner"
            required
            value={reportLocation}
            onChange={(event) => onReportLocationChange(event.target.value)}
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
              onChange={(event) => onReportLatChange(event.target.value)}
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
              onChange={(event) => onReportLonChange(event.target.value)}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="reportType">Concern Category *</label>
          <select
            id="reportType"
            className="form-input"
            value={reportType}
            onChange={(event) => onReportTypeChange(event.target.value)}
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
            onChange={(event) => onReportDescChange(event.target.value)}
            style={{ resize: "vertical", fontFamily: "inherit" }}
          />
        </div>

        {reportError ? <div className="alert alert-danger">⚠️ {reportError}</div> : null}
        {reportSuccess ? (
          <div className="alert alert-success">
            <CheckCircle2 size={16} />
            Safety report submitted successfully!
          </div>
        ) : null}

        <button type="submit" className="btn btn-primary" disabled={isSubmittingReport}>
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
  );
}
