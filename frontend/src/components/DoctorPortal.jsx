import React, { useState, useEffect } from "react";
import { auditAPI, healthAPI, analyticsAPI } from "../services/api";
import { User, AlertTriangle, ShieldCheck, Activity, Search, FileText, ChevronRight, Download } from "lucide-react";

export default function DoctorPortal() {
  const [patients, setPatients] = useState([
    { name: "John Doe", age: 45, status: "Critical Alert", gender: "Male", lastUpdate: "2026-06-06" },
    { name: "Unknown", age: 34, status: "Normal", gender: "Female", lastUpdate: "2026-06-05" },
  ]);
  const [search, setSearch] = useState("");
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [patientHistory, setPatientHistory] = useState([]);
  const [patientJourney, setPatientJourney] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [activeTab, setActiveTab] = useState("patients"); // patients, logs, alerts
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchAuditLogs();
  }, []);

  const fetchAuditLogs = async () => {
    try {
      const logs = await auditAPI.getLogs(50);
      setAuditLogs(logs);
    } catch (err) {
      console.error("Failed to load audit logs:", err);
    }
  };

  const handleSelectPatient = async (patientName) => {
    setLoading(true);
    setSelectedPatient(patientName);
    try {
      // Load selected patient health records from healthAPI
      const records = await healthAPI.getRecords(50);
      // Filter records for this patient
      const filtered = records.filter((r) => r.patient_name === patientName);
      setPatientHistory(filtered);

      const journeyData = await analyticsAPI.getJourney(patientName);
      setPatientJourney(journeyData);
    } catch (err) {
      console.error("Failed to load patient records:", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredPatients = patients.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight text-slate-100">
          Clinician Portal
        </h2>
        <p className="text-slate-400 text-sm mt-1">
          Review patient charts, monitor critical anomalies, and verify HIPAA audit logs.
        </p>
      </div>

      {/* Tabs bar */}
      <div className="flex border-b border-slate-800">
        <button
          onClick={() => setActiveTab("patients")}
          className={`px-6 py-3 text-sm font-bold border-b-2 transition-all ${activeTab === "patients" ? "border-teal-500 text-teal-400" : "border-transparent text-slate-400 hover:text-slate-200"}`}
        >
          Patient Charts
        </button>
        <button
          onClick={() => setActiveTab("logs")}
          className={`px-6 py-3 text-sm font-bold border-b-2 transition-all ${activeTab === "logs" ? "border-teal-500 text-teal-400" : "border-transparent text-slate-400 hover:text-slate-200"}`}
        >
          HIPAA Security Audit Logs
        </button>
      </div>

      {/* Main views */}
      {activeTab === "patients" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Patients list panel */}
          <div className="glass-panel p-6 border border-slate-800 space-y-4 h-fit">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <User className="h-5 w-5 text-teal-400" />
              Patient Registry
            </h3>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search patient registry..."
                className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl focus:border-teal-500 focus:outline-none text-slate-100 text-sm"
              />
            </div>

            {/* List */}
            <div className="space-y-3">
              {filteredPatients.map((patient, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectPatient(patient.name)}
                  className={`w-full p-4 border rounded-xl text-left transition-all flex items-center justify-between group ${selectedPatient === patient.name ? "bg-teal-500/10 border-teal-500/30" : "bg-slate-950/20 border-slate-800 hover:border-slate-700"}`}
                >
                  <div>
                    <h4 className="font-bold text-slate-200 text-sm group-hover:text-teal-400 transition-colors">
                      {patient.name}
                    </h4>
                    <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider mt-1 block">
                      Age: {patient.age} | {patient.gender}
                    </span>
                  </div>
                  <ChevronRight className="h-5 w-5 text-slate-500 group-hover:text-teal-400 transition-colors" />
                </button>
              ))}
            </div>
          </div>

          {/* Details Chart panel */}
          <div className="lg:col-span-2 glass-panel p-6 border border-slate-800 space-y-6">
            {selectedPatient ? (
              loading ? (
                <div className="text-center py-16 text-slate-500 text-sm">
                  Loading patient charts...
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Top info card */}
                  <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
                    <div>
                      <h3 className="text-2xl font-extrabold text-slate-100">
                        {selectedPatient}
                      </h3>
                      <p className="text-slate-400 text-xs mt-1">
                        Active health journey monitoring and medical history summaries.
                      </p>
                    </div>
                  </div>

                  {/* Summary grid */}
                  {patientJourney ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl">
                        <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">
                          Total readings
                        </span>
                        <div className="text-2xl font-extrabold text-slate-200 mt-1">
                          {patientJourney.snapshot_count}
                        </div>
                      </div>
                      <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl">
                        <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">
                          Heart rate (avg)
                        </span>
                        <div className="text-2xl font-extrabold text-slate-200 mt-1">
                          {patientJourney.average_heart_rate} BPM
                        </div>
                      </div>
                      <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl">
                        <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">
                          Daily steps (avg)
                        </span>
                        <div className="text-2xl font-extrabold text-slate-200 mt-1">
                          {patientJourney.average_steps}
                        </div>
                      </div>
                      <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl">
                        <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">
                          Diabetes Risk
                        </span>
                        <div className="text-xl font-extrabold text-teal-400 mt-1.5 capitalize">
                          {patientJourney.latest_risk_level}
                        </div>
                      </div>
                    </div>
                  ) : null}

                  {/* History List */}
                  <div className="space-y-4">
                    <h4 className="font-bold text-slate-200 text-sm flex items-center gap-2">
                      <Activity className="h-4 w-4 text-teal-400" />
                      Clinical Readings Log
                    </h4>
                    {patientHistory.length > 0 ? (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs text-slate-300">
                          <thead>
                            <tr className="border-b border-slate-800 text-slate-500 uppercase font-semibold">
                              <th className="pb-3 pr-4">Heart Rate</th>
                              <th className="pb-3 px-4">BP (mmHg)</th>
                              <th className="pb-3 px-4">Glucose (F)</th>
                              <th className="pb-3 pl-4">Glucose (PP)</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/40">
                            {patientHistory.slice(0, 5).map((h, i) => (
                              <tr key={i}>
                                <td className="py-3 pr-4 text-slate-200 font-bold">{h.heart_rate} BPM</td>
                                <td className="py-3 px-4 text-slate-300">{h.blood_pressure}</td>
                                <td className="py-3 px-4 text-slate-400">
                                  {h.fasting_blood_sugar ? `${h.fasting_blood_sugar} mg/dL` : "—"}
                                </td>
                                <td className="py-3 pl-4 text-slate-400">
                                  {h.postprandial_blood_sugar ? `${h.postprandial_blood_sugar} mg/dL` : "—"}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="text-slate-500 text-sm">No historical readings found for this patient.</p>
                    )}
                  </div>
                </div>
              )
            ) : (
              <div className="text-center py-20 text-slate-500 text-sm border border-slate-800 border-dashed rounded-2xl bg-slate-950/20">
                Select a patient from the registry to inspect health data.
              </div>
            )}
          </div>
        </div>
      )}

      {/* HIPAA audit log view */}
      {activeTab === "logs" && (
        <div className="glass-panel p-6 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-emerald-400" />
              HIPAA Compliant System Audit Logs
            </h3>
            <button
              onClick={fetchAuditLogs}
              className="text-xs text-teal-400 hover:text-teal-300 font-medium"
            >
              Refresh Logs
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500 uppercase font-semibold">
                  <th className="pb-3 pr-4">Timestamp</th>
                  <th className="pb-3 px-4">Operator</th>
                  <th className="pb-3 px-4">Role</th>
                  <th className="pb-3 px-4">Action</th>
                  <th className="pb-3 px-4">Resource Accessed</th>
                  <th className="pb-3 pl-4 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {auditLogs.map((log) => (
                  <tr key={log.id}>
                    <td className="py-3 pr-4 text-slate-500 font-mono">{log.timestamp}</td>
                    <td className="py-3 px-4 font-bold text-slate-300">{log.username}</td>
                    <td className="py-3 px-4 text-slate-400 capitalize">{log.role}</td>
                    <td className="py-3 px-4 font-mono font-bold text-teal-400">{log.action}</td>
                    <td className="py-3 px-4 text-slate-400 font-mono text-[10px]">{log.resource}</td>
                    <td className="py-3 pl-4 text-right">
                      <span className={`px-2 py-0.5 border rounded-full text-[9px] font-extrabold tracking-wider ${log.status === "SUCCESS" ? "text-emerald-500 border-emerald-500/20 bg-emerald-500/5" : "text-rose-500 border-rose-500/20 bg-rose-500/5"}`}>
                        {log.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
