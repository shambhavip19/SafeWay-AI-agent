"use client";

import { BarChart3, Loader2 } from "lucide-react";

interface AnalyticsPanelProps {
  isLoadingAnalytics: boolean;
  analyticsData: any;
}

export default function AnalyticsPanel({ isLoadingAnalytics, analyticsData }: AnalyticsPanelProps) {
  if (isLoadingAnalytics) {
    return (
      <div className="card">
        <h2 className="section-title">
          <BarChart3 size={20} />
          Safety Analytics
        </h2>
        <div className="empty-state">
          <Loader2 className="animate-spin" size={32} color="var(--primary-color)" />
          <span>Loading analytics matrices...</span>
        </div>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="card">
        <h2 className="section-title">
          <BarChart3 size={20} />
          Safety Analytics
        </h2>
        <div className="empty-state">
          Could not fetch analytics data. Check server connectivity.
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="section-title">
        <BarChart3 size={20} />
        Safety Analytics
      </h2>

      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        <div className="grid-cols-2">
          <div className="stat-box">
            <div className="stat-value">{analyticsData.total_reports}</div>
            <div className="stat-label">Reports Logged</div>
          </div>
          <div className="stat-box">
            <div className="stat-value">
              {analyticsData.daily_analyses.reduce((total: number, item: any) => total + item.count, 0)}
            </div>
            <div className="stat-label">Total Checks</div>
          </div>
        </div>

        <div>
          <h4 className="subsection-title">Top 5 Hotspot Areas:</h4>
          <div className="analytics-list">
            {analyticsData.hotspot_locations.length > 0 ? (
              analyticsData.hotspot_locations.map((item: any, index: number) => (
                <div className="analytics-item" key={`${item.location}-${index}`}>
                  <span>{index + 1}. {item.location}</span>
                  <span className="analytics-count">{item.count} reports</span>
                </div>
              ))
            ) : (
              <div className="muted-text">No community reports logged yet.</div>
            )}
          </div>
        </div>

        <div>
          <h4 className="subsection-title">Incident Categories Distribution:</h4>
          <div className="chart-bar-container">
            {analyticsData.report_categories.length > 0 ? (
              analyticsData.report_categories.map((item: any, index: number) => {
                const maxCount = Math.max(...analyticsData.report_categories.map((entry: any) => entry.count)) || 1;
                const percent = (item.count / maxCount) * 100;
                return (
                  <div className="chart-row" key={`${item.category}-${index}`}>
                    <span className="chart-label">{item.category}</span>
                    <div className="chart-bar-bg">
                      <div className="chart-bar-fill" style={{ width: `${percent}%` }} />
                    </div>
                    <span style={{ fontWeight: 600, width: "20px" }}>{item.count}</span>
                  </div>
                );
              })
            ) : (
              <div className="muted-text">No category statistics available.</div>
            )}
          </div>
        </div>

        <div>
          <h4 className="subsection-title">Frequency of Threat Warnings:</h4>
          <div className="analytics-list">
            {analyticsData.common_threats.map((item: any, index: number) => (
              <div className="analytics-item" key={`${item.threat}-${index}`}>
                <span>{item.threat}</span>
                <span style={{ fontWeight: 600 }}>{item.count} triggers</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
