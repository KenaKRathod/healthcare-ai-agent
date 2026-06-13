import React, { useState, useEffect, useMemo } from "react";
import { medicationsAPI } from "../services/api";
import { Check, X, Plus, Calendar, Activity, Pill, Clock, TrendingUp, AlertTriangle, ChevronDown, ChevronUp } from "lucide-react";

// ─── Adherence Rate Label ─────────────────────────────────────────────────────
function getAdherenceLabel(rate, hasLogs) {
  if (!hasLogs) return { label: "No data yet", color: "text-slate-500", barColor: "#334155" };
  if (rate >= 90) return { label: "Excellent", color: "text-emerald-400", barColor: "#10b981" };
  if (rate >= 75) return { label: "Good", color: "text-teal-400", barColor: "#14b8a6" };
  if (rate >= 50) return { label: "Needs Improvement", color: "text-amber-400", barColor: "#f59e0b" };
  return { label: "Critical — Take Action", color: "text-rose-400", barColor: "#f43f5e" };
}

// ─── Streak Counter ────────────────────────────────────────────────────────────
// Given sorted adherence logs (newest first), calculate how many consecutive
// days ALL meds were taken (simplified: days where at least one "Taken" log exists)
function calculateStreak(logs) {
  if (!logs.length) return 0;

  // Get unique dates from logs where all on that date are "Taken"
  const byDate = {};
  logs.forEach((l) => {
    if (!byDate[l.date]) byDate[l.date] = { total: 0, taken: 0 };
    byDate[l.date].total++;
    if (l.status === "Taken") byDate[l.date].taken++;
  });

  // Sort dates descending
  const dates = Object.keys(byDate).sort((a, b) => (a > b ? -1 : 1));
  let streak = 0;
  for (const date of dates) {
    if (byDate[date].taken > 0 && byDate[date].taken === byDate[date].total) {
      streak++;
    } else {
      break;
    }
  }
  return streak;
}

// ─── Missed Today Banner ──────────────────────────────────────────────────────
function MissedTodayBanner({ missedMeds }) {
  if (!missedMeds.length) return null;
  return (
    <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-start gap-3">
      <AlertTriangle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
      <div>
        <p className="text-sm font-bold text-rose-400">Missed Medication Today</p>
        <p className="text-xs text-rose-300/70 mt-0.5">
          You have missed: <strong className="text-rose-300">{missedMeds.join(", ")}</strong>. Contact your healthcare provider if needed.
        </p>
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function MedicationTracker({ username }) {
  const [schedules, setSchedules] = useState([]);
  const [adherenceLogs, setAdherenceLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAllLogs, setShowAllLogs] = useState(false);

  // Add medication form state
  const [showAddForm, setShowAddForm] = useState(false);
  const [drugName, setDrugName] = useState("");
  const [dosage, setDosage] = useState("");
  const [timing, setTiming] = useState("Morning");
  const [drugType, setDrugType] = useState("Allopathic");

  // L-BUG-5 FIX: use useMemo so 'today' is always the current date (avoids stale date
  // if the app is left open past midnight — previously computed once at mount time)
  const today = useMemo(() => new Date().toISOString().split("T")[0], []);

  const fetchMedicationData = async () => {
    try {
      setLoading(true);
      const scheduleData = await medicationsAPI.getSchedules(username);
      setSchedules(scheduleData);

      const logData = await medicationsAPI.getAdherence(username);
      setAdherenceLogs(logData);
    } catch (err) {
      console.error("Failed to load medication tracker data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMedicationData();
  }, [username]);

  const handleAddMedication = async (e) => {
    e.preventDefault();
    try {
      await medicationsAPI.createSchedule({
        patient_name: username,
        drug_name: drugName,
        dosage,
        timing,
        drug_type: drugType,
      });
      setShowAddForm(false);
      setDrugName("");
      setDosage("");
      fetchMedicationData();
    } catch (err) {
      alert(`Failed to add medication schedule: ${err.message}`);
    }
  };

  const handleLogAdherence = async (drugName, status) => {
    try {
      await medicationsAPI.logAdherence({
        patient_name: username,
        drug_name: drugName,
        date: today,
        status,
      });
      fetchMedicationData();
    } catch (err) {
      alert(`Failed to log adherence: ${err.message}`);
    }
  };

  const getTodayStatus = (drugName) => {
    const todayLog = adherenceLogs.find((l) => l.drug_name === drugName && l.date === today);
    return todayLog ? todayLog.status : null;
  };

  // FIX BUG-5: return null when no logs, not 100%
  const hasLogs = adherenceLogs.length > 0;
  const calculateAdherenceRate = () => {
    if (!hasLogs) return null;
    const takenDoses = adherenceLogs.filter((l) => l.status === "Taken").length;
    return Math.round((takenDoses / adherenceLogs.length) * 100);
  };

  const adherenceRate = calculateAdherenceRate();
  const adherenceLabel = getAdherenceLabel(adherenceRate, hasLogs);
  const streak = calculateStreak(adherenceLogs);

  // Find today's missed meds for banner
  const missedToday = adherenceLogs
    .filter((l) => l.date === today && l.status === "Missed")
    .map((l) => l.drug_name);

  const displayedLogs = showAllLogs ? adherenceLogs : adherenceLogs.slice(0, 5);

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-100">
            Medication Tracker
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Log allopathic and ayurvedic schedules to maintain medication safety.
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-4 py-2.5 bg-teal-500 hover:bg-teal-600 text-slate-950 font-bold rounded-xl flex items-center gap-2 transition-colors shadow-lg"
        >
          <Plus className="h-5 w-5" />
          Add Medication
        </button>
      </div>

      {/* Missed Today Banner */}
      <MissedTodayBanner missedMeds={missedToday} />

      {/* Analytics + Schedule */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Adherence Card */}
        <div className="glass-panel p-6 border border-slate-800 flex flex-col justify-between">
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Activity className="h-5 w-5 text-teal-400" />
              Adherence Rate
            </h3>
            <div className="text-center py-2">
              {/* FIX BUG-5: show N/A when no logs instead of 100% */}
              <div className={`text-6xl font-extrabold mb-1 ${adherenceLabel.color}`}>
                {hasLogs ? `${adherenceRate}%` : "N/A"}
              </div>
              <p className={`text-sm font-bold ${adherenceLabel.color}`}>{adherenceLabel.label}</p>
              <p className="text-slate-500 text-xs mt-2 px-4 leading-relaxed">
                Adherence above 80% is recommended for chronic therapies.
              </p>
            </div>

            {/* Progress bar */}
            {hasLogs && (
              <div className="space-y-1">
                <div className="w-full bg-slate-900 rounded-full h-2.5">
                  <div
                    className="h-2.5 rounded-full transition-all duration-700"
                    style={{ width: `${adherenceRate}%`, backgroundColor: adherenceLabel.barColor }}
                  />
                </div>
              </div>
            )}

            {/* Streak */}
            {streak > 0 && (
              <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 rounded-xl px-3 py-2">
                <span className="text-lg">🔥</span>
                <div>
                  <p className="text-xs font-bold text-amber-400">{streak}-Day Streak</p>
                  <p className="text-[10px] text-amber-400/60">All meds taken consistently</p>
                </div>
              </div>
            )}
          </div>

          <div className="border-t border-slate-800/60 pt-4 text-center text-xs text-slate-500">
            Based on {adherenceLogs.length} total logged dose{adherenceLogs.length !== 1 ? "s" : ""}.
          </div>
        </div>

        {/* Schedule List */}
        <div className="lg:col-span-2 glass-panel p-6 border border-slate-800">
          <h3 className="text-lg font-bold text-slate-100 mb-4 flex items-center gap-2">
            <Pill className="h-5 w-5 text-teal-400" />
            Today's Scheduled Doses
            {schedules.length > 0 && (
              <span className="ml-auto text-xs text-slate-500 font-normal">
                {adherenceLogs.filter((l) => l.date === today && l.status === "Taken").length}/{schedules.length} taken today
              </span>
            )}
          </h3>

          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((n) => (
                <div key={n} className="animate-pulse p-4 bg-slate-800/30 rounded-xl h-16" />
              ))}
            </div>
          ) : schedules.length > 0 ? (
            <div className="space-y-4">
              {schedules.map((med) => {
                const todayStatus = getTodayStatus(med.drug_name);
                return (
                  <div
                    key={med.id}
                    className={`p-4 border rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4 transition-colors ${
                      todayStatus === "Taken"
                        ? "bg-emerald-500/5 border-emerald-500/20"
                        : todayStatus === "Missed"
                          ? "bg-rose-500/5 border-rose-500/20"
                          : "bg-slate-950/40 border-slate-800"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2.5 rounded-xl border ${med.drug_type === "Ayurvedic" ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" : "bg-teal-500/10 border-teal-500/20 text-teal-400"}`}>
                        <Pill className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-bold text-slate-100 text-base">{med.drug_name}</h4>
                          {todayStatus === "Taken" && (
                            <span className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold rounded-full">✓ Done</span>
                          )}
                          {todayStatus === "Missed" && (
                            <span className="px-2 py-0.5 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-[10px] font-bold rounded-full">✗ Missed</span>
                          )}
                        </div>
                        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-1">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3.5 w-3.5 text-slate-500" />
                            {med.timing}
                          </span>
                          <span>Dosage: <strong className="text-slate-300">{med.dosage}</strong></span>
                          <span className={`px-2 py-0.5 border rounded-full text-[10px] uppercase font-semibold tracking-wider ${med.drug_type === "Ayurvedic" ? "text-emerald-500 border-emerald-500/30" : "text-teal-400 border-teal-400/30"}`}>
                            {med.drug_type}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => handleLogAdherence(med.drug_name, "Taken")}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all border ${todayStatus === "Taken" ? "bg-emerald-500 text-slate-950 border-emerald-500" : "bg-slate-900 border-slate-800 text-slate-400 hover:text-emerald-400 hover:border-emerald-500/30"}`}
                      >
                        <Check className="h-4 w-4" />
                        Taken
                      </button>
                      <button
                        onClick={() => handleLogAdherence(med.drug_name, "Missed")}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all border ${todayStatus === "Missed" ? "bg-rose-500 text-slate-950 border-rose-500" : "bg-slate-900 border-slate-800 text-slate-400 hover:text-rose-400 hover:border-rose-500/30"}`}
                      >
                        <X className="h-4 w-4" />
                        Missed
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500 text-sm border border-slate-800 border-dashed rounded-xl bg-slate-950/20">
              No active medication schedules found. Click "Add Medication" to configure daily schedules.
            </div>
          )}
        </div>
      </div>

      {/* Add medication form */}
      {showAddForm && (
        <form onSubmit={handleAddMedication} className="glass-panel p-6 border border-slate-800 bg-slate-950/60 space-y-6 max-w-2xl mx-auto">
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Plus className="h-5 w-5 text-teal-400" />
            Add Medication Schedule
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Medication/Drug Name</label>
              <input
                type="text"
                required
                value={drugName}
                onChange={(e) => setDrugName(e.target.value)}
                placeholder="e.g. Metformin"
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl focus:border-teal-500 focus:outline-none text-slate-100"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Dosage</label>
              <input
                type="text"
                required
                value={dosage}
                onChange={(e) => setDosage(e.target.value)}
                placeholder="e.g. 500mg"
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl focus:border-teal-500 focus:outline-none text-slate-100"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Frequency Timing</label>
              <select
                value={timing}
                onChange={(e) => setTiming(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl focus:border-teal-500 focus:outline-none text-slate-100"
              >
                <option value="Morning">Morning (Breakfast)</option>
                <option value="Afternoon">Afternoon (Lunch)</option>
                <option value="Evening">Evening (Tea)</option>
                <option value="Night">Night (Dinner/Bedtime)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Medication Category</label>
              <select
                value={drugType}
                onChange={(e) => setDrugType(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl focus:border-teal-500 focus:outline-none text-slate-100"
              >
                <option value="Allopathic">Allopathic Medicine</option>
                <option value="Ayurvedic">Ayurvedic (Traditional)</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setShowAddForm(false)} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-xl">Cancel</button>
            <button type="submit" className="px-6 py-2 bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 text-slate-950 font-bold rounded-xl">Configure Schedule</button>
          </div>
        </form>
      )}

      {/* Adherence Log Table — with pagination */}
      {adherenceLogs.length > 0 && (
        <div className="glass-panel p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Calendar className="h-5 w-5 text-teal-400" />
              Medication Adherence Logs
            </h3>
            <span className="text-xs text-slate-500">{adherenceLogs.length} total records</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-sm text-slate-300">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase font-semibold text-xs tracking-wider">
                  <th className="pb-3 pr-4">Date</th>
                  <th className="pb-3 px-4">Medication</th>
                  <th className="pb-3 pl-4 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {displayedLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-900/30 transition-colors">
                    <td className="py-3.5 pr-4 text-slate-400 font-medium">
                      {log.date === today ? (
                        <span className="flex items-center gap-1.5">
                          {log.date}
                          <span className="px-1.5 py-0.5 bg-teal-500/10 text-teal-400 text-[9px] font-bold rounded-full border border-teal-500/20">TODAY</span>
                        </span>
                      ) : (
                        log.date
                      )}
                    </td>
                    <td className="py-3.5 px-4 font-bold text-slate-200">{log.drug_name}</td>
                    <td className="py-3.5 pl-4 text-right">
                      <span className={`px-2 py-0.5 border rounded-full text-[10px] uppercase font-bold tracking-wider ${log.status === "Taken" ? "text-emerald-500 border-emerald-500/20 bg-emerald-500/5" : "text-rose-500 border-rose-500/20 bg-rose-500/5"}`}>
                        {log.status === "Taken" ? "✓ " : "✗ "}{log.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Show more / less toggle */}
          {adherenceLogs.length > 5 && (
            <button
              onClick={() => setShowAllLogs(!showAllLogs)}
              className="mt-4 w-full flex items-center justify-center gap-2 py-2 text-xs font-semibold text-slate-400 hover:text-slate-200 border border-slate-800 hover:border-slate-700 rounded-xl transition-colors"
            >
              {showAllLogs ? (
                <><ChevronUp className="h-4 w-4" /> Show Less</>
              ) : (
                <><ChevronDown className="h-4 w-4" /> Show All {adherenceLogs.length} Records</>
              )}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
