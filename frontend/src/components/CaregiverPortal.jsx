import React, { useState, useEffect } from "react";
import { healthAPI, medicationsAPI, goalsAPI } from "../services/api";
import { User, Activity, AlertTriangle, Pill, ShieldCheck, Heart, Sparkles } from "lucide-react";

export default function CaregiverPortal() {
  const [monitoredPatient, setMonitoredPatient] = useState("John Doe");
  const [latestVitals, setLatestVitals] = useState(null);
  const [meds, setMeds] = useState([]);
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchPatientDetails = async () => {
    try {
      setLoading(true);
      const records = await healthAPI.getRecords(10);
      const filtered = records.filter((r) => r.patient_name === monitoredPatient);
      if (filtered.length > 0) {
        setLatestVitals(filtered[0]);
      }

      const medSchedule = await medicationsAPI.getSchedules(monitoredPatient);
      setMeds(medSchedule);

      const goalsData = await goalsAPI.getGoals(monitoredPatient, 0, 0, 0);
      setGoals(goalsData);
    } catch (err) {
      console.error("Failed to load caregiver patient stats:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatientDetails();
  }, [monitoredPatient]);

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight text-slate-100">
          Caregiver Companion Dashboard
        </h2>
        <p className="text-slate-400 text-sm mt-1">
          Monitor linked family member compliance, check medication logs, and inspect active vitals.
        </p>
      </div>

      {/* Main card */}
      <div className="glass-panel p-6 border border-slate-800 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-teal-500/10 border border-teal-500/20 rounded-2xl">
              <User className="h-6 w-6 text-teal-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-100">John Doe</h3>
              <span className="text-xs text-slate-400">Linked profile relationship: Parent</span>
            </div>
          </div>
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-ping"></span>
        </div>

        {loading ? (
          <div className="text-center py-12 text-slate-500 text-sm">
            Syncing family member metrics...
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Vitals Summary Card */}
            <div className="p-5 bg-slate-950/40 border border-slate-900 rounded-xl space-y-4">
              <h4 className="font-bold text-slate-200 text-sm flex items-center gap-2">
                <Heart className="h-4 w-4 text-rose-500" />
                Latest Vitals
              </h4>
              {latestVitals ? (
                <div className="space-y-3 pt-2">
                  <div className="flex justify-between items-center text-sm border-b border-slate-900 pb-2">
                    <span className="text-slate-400">Heart Rate</span>
                    <strong className="text-slate-200">{latestVitals.heart_rate} BPM</strong>
                  </div>
                  <div className="flex justify-between items-center text-sm border-b border-slate-900 pb-2">
                    <span className="text-slate-400">Blood Pressure</span>
                    <strong className="text-slate-200">{latestVitals.blood_pressure} mmHg</strong>
                  </div>
                  {latestVitals.fasting_blood_sugar && (
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-slate-400">Fasting Glucose</span>
                      <strong className="text-slate-200">{latestVitals.fasting_blood_sugar} mg/dL</strong>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-slate-500 text-xs">No recent vital logs retrieved.</p>
              )}
            </div>

            {/* Meds Adherence Summary Card */}
            <div className="p-5 bg-slate-950/40 border border-slate-900 rounded-xl space-y-4">
              <h4 className="font-bold text-slate-200 text-sm flex items-center gap-2">
                <Pill className="h-4 w-4 text-teal-400" />
                Scheduled Medications
              </h4>
              <div className="space-y-2.5 max-h-[150px] overflow-y-auto pr-1">
                {meds.length > 0 ? (
                  meds.map((med) => (
                    <div key={med.id} className="text-xs flex items-center justify-between p-2 bg-slate-900 border border-slate-800 rounded-lg">
                      <div>
                        <strong className="text-slate-200 block">{med.drug_name}</strong>
                        <span className="text-slate-400 text-[10px]">{med.timing}</span>
                      </div>
                      <span className={`px-1.5 py-0.5 border rounded-full text-[9px] uppercase font-bold tracking-wider ${med.drug_type === "Ayurvedic" ? "text-emerald-500 border-emerald-500/20" : "text-teal-400 border-teal-400/20"}`}>
                        {med.drug_type}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-500 text-xs">No active medication schedules.</p>
                )}
              </div>
            </div>

            {/* Goals progress */}
            <div className="p-5 bg-slate-950/40 border border-slate-900 rounded-xl space-y-4">
              <h4 className="font-bold text-slate-200 text-sm flex items-center gap-2">
                <Activity className="h-4 w-4 text-blue-400" />
                Daily Activity Goals
              </h4>
              <div className="space-y-3">
                {goals.slice(0, 2).map((goal, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-xs text-slate-400">
                      <span className="capitalize">{goal.goal_name.replace("_", " ")}</span>
                      <strong className="text-teal-400">{Math.round(goal.progress_percent)}%</strong>
                    </div>
                    <div className="w-full bg-slate-900 rounded-full h-1.5">
                      <div className="bg-teal-500 h-1.5 rounded-full" style={{ width: `${Math.min(goal.progress_percent, 100)}%` }}></div>
                    </div>
                  </div>
                ))}
                {goals.length === 0 && (
                  <p className="text-slate-500 text-xs">No active activity goals configured.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Safety notifications simulation */}
      <div className="glass-panel p-6 border border-slate-800 space-y-4">
        <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-amber-500" />
          Safety reminders & alert triggers
        </h3>
        <div className="p-4 bg-slate-950/40 border border-slate-900 rounded-xl flex items-start gap-3">
          <Sparkles className="h-5 w-5 text-teal-400 shrink-0 mt-0.5" />
          <div className="text-xs text-slate-400 leading-normal">
            <strong>AuraHealth suggestion</strong>: John's daily steps are currently at 45% of the 8,000 steps target. Send a gentle reminder to encourage an afternoon walk to maintain cardiovascular health.
          </div>
        </div>
      </div>
    </div>
  );
}
