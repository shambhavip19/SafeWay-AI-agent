import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
    baseURL: API_URL,
    headers: { "Content-Type": "application/json" },
});

export interface AnalysisResult {
    id: number;
    origin: string;
    destination: string;
    latitude: number;
    longitude: number;
    safety_score: number;
    risk_level: "Low" | "Medium" | "High";
    recommendation: string;
    created_at: string;
}

export interface RouteResult {
    origin: string;
    destination: string;
    safety_score: number;
    risk_level: string;
    route_geometry: GeoJSON.LineString;
    risk_segments: {
        coordinates: [number, number][];
        risk_level: string;
        reason: string;
    }[];
    alternative_route_geometry?: GeoJSON.LineString;
}

export interface EmergencyResource {
    id: number;
    name: string;
    resource_type: "Police" | "Hospital";
    latitude: number;
    longitude: number;
}

export interface CommunityReport {
    id: number;
    location: string;
    latitude: number;
    longitude: number;
    report_type: string;
    description: string;
    created_at: string;
}

export const analyzeTravelSafety = (data: {
    origin: string;
    destination: string;
    event_time?: string;
}) => api.post<AnalysisResult>("/api/analysis", data);

export const analyzeRoute = (data: { origin: string; destination: string }) =>
    api.post<RouteResult>("/api/route", data);

export const getEmergencyResources = (lat: number, lon: number) =>
    api.get<EmergencyResource[]>("/api/emergency", { params: { lat, lon } });

export const getReports = (lat?: number, lon?: number) =>
    api.get<CommunityReport[]>("/api/reports", { params: { lat, lon } });

export const submitReport = (data: {
    location: string;
    latitude: number;
    longitude: number;
    report_type: string;
    description: string;
}) => api.post<CommunityReport>("/api/reports", data);

export const getAnalytics = () => api.get("/api/analytics");