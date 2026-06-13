import React, { useState, useEffect, useCallback } from "react";
import { healthAPI, analyticsAPI, goalsAPI } from "../services/api";
import { Line, Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import {
  Activity,
  Heart,
  TrendingUp,
  Droplet,
  UploadCloud,
  Plus,
  AlertTriangle,
  Award,
  Sparkles,
  RefreshCw,
  Gauge,
  Wind,
  CheckCircle,
} from "lucide-react";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// ─── IDRS Arc Gauge ──────────────────────────────────────────────────────────
function IDRSArcGauge({ score, riskLevel }) {
  const maxScore = 100;
  const pct = Math.min(score / maxScore, 1);
  const size = 130;
  const strokeWidth = 8;
  const r = (size - 20) / 2; // radius is 55, leaves padding for glow
  const circ = 2 * Math.PI * r;
  
  // A 270 degree arc (3/4 of a circle)
  const angleRange = 270;
  const strokeDash = (pct * (angleRange / 360)) * circ;
  const trackDash = (angleRange / 360) * circ;

  const arcColor =
    (riskLevel || "").toLowerCase() === "high"
      ? "#ef4444" // vibrant red
      : (riskLevel || "").toLowerCase() === "medium"
        ? "#f59e0b" // amber
        : "#10b981"; // emerald

  // Gradient ID
  const gradId = `idrs-grad-${score}`;

  return (
    <div className="flex flex-col items-center justify-center relative my-2">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="rotate-[135deg]">
        <defs>
          <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={arcColor} stopOpacity={0.6} />
            <stop offset="100%" stopColor={arcColor} stopOpacity={1} />
          </linearGradient>
          <filter id="idrs-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        
        {/* Background track circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgba(255, 255, 255, 0.05)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${trackDash} ${circ}`}
        />

        {/* Outer thin border guide */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r + 6}
          fill="none"
          stroke="rgba(255, 255, 255, 0.02)"
          strokeWidth={1}
          strokeDasharray="4 2"
        />

        {/* Progress Arc */}
        {score > 0 && (
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={`url(#${gradId})`}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={`${strokeDash} ${circ}`}
            filter="url(#idrs-glow)"
            style={{
              transition: "stroke-dasharray 1.2s cubic-bezier(0.4, 0, 0.2, 1)",
            }}
          />
        )}
      </svg>

      {/* Centered Score */}
      <div className="absolute inset-0 flex flex-col items-center justify-center mt-[-6px]">
        <span className="text-3xl font-black text-slate-100 tracking-tight leading-none">{score}</span>
        <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-widest mt-1">Points</span>
      </div>
    </div>
  );
}

// ─── Stat Card ───────────────────────────────────────────────────────────────
function StatCard({ icon: Icon, label, value, unit, statusColor, statusLabel }) {
  return (
    <div className="glass-panel p-5 border border-slate-800 flex items-center gap-4">
      <div className={`p-3 rounded-xl border ${statusColor}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{label}</p>
        <p className="text-2xl font-extrabold text-slate-100 mt-0.5">
          {value ?? <span className="text-slate-600 text-base">—</span>}{" "}
          {value != null && <span className="text-sm font-normal text-slate-400">{unit}</span>}
        </p>
        {statusLabel && (
          <span className={`text-[10px] font-bold uppercase tracking-wider ${statusColor.includes("emerald") ? "text-emerald-400" : statusColor.includes("amber") ? "text-amber-400" : "text-rose-400"}`}>
            {statusLabel}
          </span>
        )}
      </div>
    </div>
  );
}

// ─── Chart Skeleton ───────────────────────────────────────────────────────────
function ChartSkeleton() {
  return (
    <div className="h-[250px] flex flex-col justify-end gap-2 animate-pulse px-2 pb-2">
      {[0.6, 0.8, 0.5, 0.9, 0.7, 0.85, 0.6].map((h, i) => (
        <div
          key={i}
          className="w-full bg-slate-800 rounded"
          style={{ height: `${h * 100}%` }}
        />
      ))}
    </div>
  );
}

// ─── Helpers ─────────────────────────────────────────────────────────────────
function getIDRSRiskColor(risk) {
  if (!risk) return "text-slate-400";
  const r = risk.toLowerCase();
  if (r === "high") return "text-rose-500 bg-rose-500/10 border-rose-500/20";
  if (r === "medium") return "text-amber-500 bg-amber-500/10 border-amber-500/20";
  return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
}

function getHRStatus(hr) {
  if (hr == null) return { color: "text-slate-500 bg-slate-800 border-slate-700", label: null };
  if (hr > 100) return { color: "text-rose-400 bg-rose-500/10 border-rose-500/20", label: "Tachycardia" };
  if (hr < 50) return { color: "text-amber-400 bg-amber-500/10 border-amber-500/20", label: "Bradycardia" };
  return { color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20", label: "Normal" };
}

function getFastingStatus(val) {
  if (val == null) return { color: "text-slate-500 bg-slate-800 border-slate-700", label: null };
  if (val >= 126) return { color: "text-rose-400 bg-rose-500/10 border-rose-500/20", label: "Diabetic" };
  if (val >= 100) return { color: "text-amber-400 bg-amber-500/10 border-amber-500/20", label: "Pre-diabetic" };
  return { color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20", label: "Normal" };
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function Dashboard({ username }) {
  const [records, setRecords] = useState([]);
  const [journey, setJourney] = useState(null);
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState(false);

  // Manual form state
  const [showAddForm, setShowAddForm] = useState(false);
  const [heartRate, setHeartRate] = useState("");
  const [bloodPressure, setBloodPressure] = useState("120/80");
  const [age, setAge] = useState("");
  const [sex, setSex] = useState("male");
  const [waist, setWaist] = useState("");
  const [activity, setActivity] = useState("moderate");
  const [familyDiabetic, setFamilyDiabetic] = useState("no");
  const [fastingSugar, setFastingSugar] = useState("");
  const [postprandialSugar, setPostprandialSugar] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const recordsData = await healthAPI.getRecords(30);
      // L-BUG-2 FIX: spread-copy before reverse to prevent double-mutation on repeated fetchData calls
      setRecords([...recordsData].reverse());

      const journeyData = await analyticsAPI.getJourney(username);
      setJourney(journeyData);

      const savedSteps = localStorage.getItem(`${username}_stepsInput`) || "0";
      const savedSleep = localStorage.getItem(`${username}_sleepInput`) || "0";
      const savedWeight = localStorage.getItem(`${username}_weightInput`) || "0";
      const goalsData = await goalsAPI.getGoals(
        username,
        parseFloat(savedSteps) || 0,
        parseFloat(savedSleep) || 0,
        parseFloat(savedWeight) || 0
      );
      setGoals(goalsData);
    } catch (err) {
      console.error("Error fetching patient dashboard data:", err);
    } finally {
      setLoading(false);
    }
  }, [username]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setUploadResult(null);
    setUploadError(false);

    try {
      const result = await healthAPI.uploadDataset(file, username);
      // FIX BUG-9: use actual backend response message, not hardcoded string
      const msg = result?.message || result?.analysis || "Health dataset ingested and analyzed successfully!";
      setUploadResult(msg);
      setUploadError(false);
      fetchData();
    } catch (err) {
      setUploadResult(err.message);
      setUploadError(true);
    } finally {
      setUploading(false);
    }
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    try {
      await healthAPI.addRecord({
        patient_name: username,
        heart_rate: parseInt(heartRate),
        blood_pressure: bloodPressure,
        age: age ? parseInt(age) : null,
        sex: sex,
        waist_cm: waist ? parseFloat(waist) : null,
        activity: activity,
        family_diabetic: familyDiabetic,
        fasting_blood_sugar: fastingSugar ? parseFloat(fastingSugar) : null,
        postprandial_blood_sugar: postprandialSugar ? parseFloat(postprandialSugar) : null,
      });
      setShowAddForm(false);
      setHeartRate("");
      setFastingSugar("");
      setPostprandialSugar("");
      fetchData();
    } catch (err) {
      alert(`Failed to add record: ${err.message}`);
    }
  };

  const latestRecord = records.length > 0 ? records[records.length - 1] : null;

  // Chart label using index (timestamps not stored in HealthData model)
  const chartLabels = records.map((_, i) => `#${i + 1}`);

  const heartRateData = {
    labels: chartLabels,
    datasets: [
      {
        label: "Heart Rate (BPM)",
        data: records.map((r) => r.heart_rate),
        borderColor: "#14b8a6",
        backgroundColor: "rgba(20, 184, 166, 0.1)",
        fill: true,
        tension: 0.4,
        pointRadius: records.length > 15 ? 2 : 4,
      },
    ],
  };

  const sugarData = {
    labels: chartLabels,
    datasets: [
      {
        label: "Fasting Blood Sugar (mg/dL)",
        data: records.map((r) => r.fasting_blood_sugar || null),
        borderColor: "#60a5fa",
        backgroundColor: "rgba(96, 165, 250, 0.08)",
        fill: false,
        tension: 0.3,
        pointRadius: records.length > 15 ? 2 : 4,
        spanGaps: true,
      },
      {
        label: "Postprandial Blood Sugar (mg/dL)",
        data: records.map((r) => r.postprandial_blood_sugar || null),
        borderColor: "#fb923c",
        backgroundColor: "rgba(251, 146, 60, 0.08)",
        fill: false,
        tension: 0.3,
        pointRadius: records.length > 15 ? 2 : 4,
        spanGaps: true,
      },
    ],
  };

  // Parse BP string for latest record
  const parseBP = (bpStr) => {
    if (!bpStr) return { systolic: null, diastolic: null };
    const parts = bpStr.split("/");
    return {
      systolic: parseInt(parts[0]) || null,
      diastolic: parseInt(parts[1]) || null,
    };
  };
  const latestBP = parseBP(latestRecord?.blood_pressure);

  const bpData = {
    labels: chartLabels,
    datasets: [
      {
        label: "Systolic (mmHg)",
        data: records.map((r) => {
          const parts = (r.blood_pressure || "").split("/");
          return parseInt(parts[0]) || null;
        }),
        backgroundColor: "rgba(248, 113, 113, 0.7)",
        borderColor: "#f87171",
        borderWidth: 1,
      },
      {
        label: "Diastolic (mmHg)",
        data: records.map((r) => {
          const parts = (r.blood_pressure || "").split("/");
          return parseInt(parts[1]) || null;
        }),
        backgroundColor: "rgba(129, 140, 248, 0.7)",
        borderColor: "#818cf8",
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#64748b", font: { size: 11 } } },
      x: { grid: { display: false }, ticks: { color: "#64748b", font: { size: 10 }, maxTicksLimit: 10 } },
    },
    plugins: { legend: { labels: { color: "#94a3b8", font: { size: 11 } } } },
  };

  // FIX BUG-4 + L-BUG-4: null guards + correct clinical threshold (> 100, not >= 100)
  const hasAbnormalHR = latestRecord != null && (latestRecord.heart_rate > 100 || latestRecord.heart_rate <= 50);
  const hasHighPPBS = latestRecord != null && latestRecord.postprandial_blood_sugar != null && latestRecord.postprandial_blood_sugar > 180;
  const hasAnomalies = journey != null && journey.anomaly_count > 0;
  // L-BUG-13 FIX: allClear must not show when there are no records at all
  const allClear = latestRecord != null && !hasAbnormalHR && !hasHighPPBS && !hasAnomalies;

  const hrStatus = getHRStatus(latestRecord?.heart_rate);
  const fastingStatus = getFastingStatus(latestRecord?.fasting_blood_sugar);

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-100">
            Welcome, <span className="text-teal-400">{username}</span>
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Secure, HIPAA-compliant digital health tracking dashboard.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={fetchData}
            disabled={loading}
            className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 font-bold rounded-xl flex items-center gap-2 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="px-4 py-2.5 bg-teal-500 hover:bg-teal-600 text-slate-950 font-bold rounded-xl flex items-center gap-2 transition-colors shadow-lg shadow-teal-500/10"
          >
            <Plus className="h-5 w-5" />
            Add Reading
          </button>
        </div>
      </div>

      {/* Latest Vitals Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          icon={Heart}
          label="Heart Rate"
          value={latestRecord?.heart_rate}
          unit="BPM"
          statusColor={hrStatus.color}
          statusLabel={hrStatus.label}
        />
        <StatCard
          icon={Activity}
          label="Blood Pressure"
          value={latestRecord?.blood_pressure ?? null}
          unit=""
          statusColor={
            latestBP.systolic != null && latestBP.systolic > 140
              ? "text-rose-400 bg-rose-500/10 border-rose-500/20"
              : "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
          }
          statusLabel={
            latestBP.systolic != null
              ? latestBP.systolic > 140
                ? "Hypertensive"
                : "Normal"
              : null
          }
        />
        <StatCard
          icon={Droplet}
          label="Fasting Sugar"
          value={latestRecord?.fasting_blood_sugar}
          unit="mg/dL"
          statusColor={fastingStatus.color}
          statusLabel={fastingStatus.label}
        />
      </div>

      {/* Ingest Widget + IDRS Gauge */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-panel p-6 border border-slate-800">
          <h3 className="text-lg font-bold text-slate-100 mb-4 flex items-center gap-2">
            <UploadCloud className="h-5 w-5 text-teal-400" />
            Ingest Health History Dataset
          </h3>
          <div className="border-2 border-dashed border-slate-800 hover:border-teal-500/50 rounded-2xl p-8 text-center transition-colors relative cursor-pointer group bg-slate-950/40">
            <input
              type="file"
              accept=".json,.csv,.xml"
              onChange={handleFileUpload}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              disabled={uploading}
            />
            <UploadCloud className="h-10 w-10 text-slate-500 group-hover:text-teal-400 mx-auto mb-4 transition-colors" />
            <p className="text-slate-300 font-medium text-sm">
              {uploading ? "Analyzing health dataset..." : "Drag and drop your health file here"}
            </p>
            <p className="text-slate-500 text-xs mt-1">
              Supports CSV, JSON, or XML formats (heart rate, blood pressure, sleep, etc.)
            </p>
          </div>
          {uploadResult && (
            <div className={`mt-4 p-4 rounded-xl text-sm flex items-start gap-2 ${uploadError ? "bg-red-500/10 border border-red-500/20 text-red-400" : "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"}`}>
              {!uploadError && <CheckCircle className="h-4 w-4 shrink-0 mt-0.5" />}
              <span>{uploadResult}</span>
            </div>
          )}
        </div>

        {/* IDRS Gauge — FIX: arc gauge instead of plain number */}
        <div className="glass-panel p-6 border border-slate-800 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-100 mb-4 flex items-center gap-2">
              <Gauge className="h-5 w-5 text-teal-400" />
              Indian Diabetes Risk Score
            </h3>
            {latestRecord && latestRecord.idrs_score != null ? (
              <div className="space-y-4">
                <IDRSArcGauge score={latestRecord.idrs_score} riskLevel={latestRecord.idrs_risk_level} />
                <div className={`px-4 py-2 border rounded-full font-bold uppercase text-xs tracking-wider mx-auto w-fit ${getIDRSRiskColor(latestRecord.idrs_risk_level)}`}>
                  {latestRecord.idrs_risk_level} Risk
                </div>
                <p className="text-slate-400 text-xs text-center px-2">
                  Based on age, waist circumference, physical activity, and family diabetic history.
                </p>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500 text-sm">
                No IDRS score calculated. Add your age, waist size, activity level, and family history.
              </div>
            )}
          </div>
          {journey && journey.snapshot_count > 0 && (
            <div className="border-t border-slate-800/60 pt-4 mt-4 flex items-center justify-between text-xs text-slate-400">
              <span>Risk Trend: <strong className="text-slate-200 capitalize">{journey.risk_trend}</strong></span>
              <span>Avg BMI: <strong className="text-slate-200">{journey.average_bmi}</strong></span>
            </div>
          )}
        </div>
      </div>

      {/* Manual Entry Form */}
      {showAddForm && (
        <form onSubmit={handleManualSubmit} className="glass-panel p-6 border border-slate-800 bg-slate-950/60 space-y-6">
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Plus className="h-5 w-5 text-teal-400" />
            Enter Single Vital Reading
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { label: "Heart Rate (BPM)", type: "number", value: heartRate, set: setHeartRate, placeholder: "e.g. 72", required: true },
              { label: "Blood Pressure (systolic/diastolic)", type: "text", value: bloodPressure, set: setBloodPressure, placeholder: "e.g. 120/80", required: true },
              { label: "Age", type: "number", value: age, set: setAge, placeholder: "e.g. 45" },
              { label: "Waist Circumference (cm)", type: "number", value: waist, set: setWaist, placeholder: "e.g. 88" },
              { label: "Fasting Blood Sugar (mg/dL)", type: "number", value: fastingSugar, set: setFastingSugar, placeholder: "e.g. 98" },
              { label: "Postprandial Blood Sugar (mg/dL)", type: "number", value: postprandialSugar, set: setPostprandialSugar, placeholder: "e.g. 140" },
            ].map(({ label, type, value, set, placeholder, required }) => (
              <div key={label}>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">{label}</label>
                <input
                  type={type}
                  required={required}
                  value={value}
                  onChange={(e) => set(e.target.value)}
                  placeholder={placeholder}
                  className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl focus:border-teal-500 focus:outline-none text-slate-100"
                />
              </div>
            ))}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Gender</label>
              <select value={sex} onChange={(e) => setSex(e.target.value)} className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl focus:border-teal-500 focus:outline-none text-slate-100">
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Physical Activity Level</label>
              <select value={activity} onChange={(e) => setActivity(e.target.value)} className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl focus:border-teal-500 focus:outline-none text-slate-100">
                <option value="vigorous">Vigorous/Regular Exercise</option>
                <option value="moderate">Moderate Exercise</option>
                <option value="sedentary">Sedentary/No Activity</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Family History of Diabetes</label>
              <select value={familyDiabetic} onChange={(e) => setFamilyDiabetic(e.target.value)} className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl focus:border-teal-500 focus:outline-none text-slate-100">
                <option value="no">No Parents Diabetic</option>
                <option value="one">One Parent Diabetic</option>
                <option value="both">Both Parents Diabetic</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setShowAddForm(false)} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-xl">Cancel</button>
            <button type="submit" className="px-6 py-2 bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 text-slate-950 font-bold rounded-xl">Save Vital</button>
          </div>
        </form>
      )}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Heart Rate Chart */}
        <div className="glass-panel p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Heart className="h-5 w-5 text-teal-400" />
              Heart Rate Trend
            </h3>
            {records.length > 0 && <span className="text-xs text-slate-500">{records.length} readings</span>}
          </div>
          {loading ? (
            <ChartSkeleton />
          ) : records.length > 0 ? (
            <div className="h-[250px]">
              <Line data={heartRateData} options={{ ...chartOptions, plugins: { ...chartOptions.plugins, legend: { display: false } } }} />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-[250px] text-slate-500 text-sm gap-2">
              <Wind className="h-8 w-8 text-slate-700" />
              Upload a health history file to see heart rate trends.
            </div>
          )}
        </div>

        {/* Blood Sugar Chart */}
        <div className="glass-panel p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Droplet className="h-5 w-5 text-blue-400" />
              Fasting &amp; Postprandial Blood Sugar
            </h3>
            {records.length > 0 && <span className="text-xs text-slate-500">{records.length} readings</span>}
          </div>
          {loading ? (
            <ChartSkeleton />
          ) : records.length > 0 ? (
            <div className="h-[250px]">
              <Line data={sugarData} options={chartOptions} />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-[250px] text-slate-500 text-sm gap-2">
              <Wind className="h-8 w-8 text-slate-700" />
              Upload a health history file to see blood sugar trends.
            </div>
          )}
        </div>

        {/* Blood Pressure Chart — FIX BUG-7: now actually charts BP data */}
        <div className="glass-panel p-6 border border-slate-800 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Activity className="h-5 w-5 text-violet-400" />
              Blood Pressure Trend (Systolic / Diastolic)
            </h3>
            {records.length > 0 && <span className="text-xs text-slate-500">{records.length} readings</span>}
          </div>
          {loading ? (
            <ChartSkeleton />
          ) : records.length > 0 ? (
            <div className="h-[220px]">
              <Bar
                data={bpData}
                options={{
                  ...chartOptions,
                  plugins: { legend: { labels: { color: "#94a3b8", font: { size: 11 } } } },
                  scales: {
                    ...chartOptions.scales,
                    y: { ...chartOptions.scales.y, min: 40 },
                  },
                }}
              />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-[220px] text-slate-500 text-sm gap-2">
              <Wind className="h-8 w-8 text-slate-700" />
              Add readings or upload a dataset to see blood pressure trends.
            </div>
          )}
        </div>
      </div>

      {/* Goals + Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-panel p-6 border border-slate-800 space-y-4">
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Award className="h-5 w-5 text-teal-400" />
            Active Wellness Goals
          </h3>
          {goals.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {goals.slice(0, 4).map((goal, idx) => {
                const pct = Math.round(goal.progress_percent);
                const barColor = pct >= 80 ? "#10b981" : pct >= 50 ? "#f59e0b" : "#f43f5e";
                return (
                  <div key={idx} className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-2">
                    <div className="flex justify-between text-sm">
                      {/* FIX BUG-2: replaceAll */}
                      <span className="font-semibold text-slate-300 capitalize">
                        {goal.goal_name.replaceAll("_", " ")}
                      </span>
                      <span className="font-bold" style={{ color: barColor }}>{pct}%</span>
                    </div>
                    <div className="w-full bg-slate-900 rounded-full h-2">
                      <div
                        className="h-2 rounded-full transition-all duration-700"
                        style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: barColor }}
                      />
                    </div>
                    <div className="text-[11px] text-slate-400 leading-normal flex items-start gap-1.5">
                      <Sparkles className="h-3.5 w-3.5 text-teal-400 shrink-0 mt-0.5" />
                      <span>{goal.recommendation}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-slate-500">No active goals configured. Goals will automatically be calculated upon ingestion.</p>
          )}
        </div>

        {/* Clinical Alerts */}
        <div className="glass-panel p-6 border border-slate-800 space-y-4">
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Clinical Alerts
          </h3>
          <div className="space-y-3 max-h-[220px] overflow-y-auto pr-1">
            {/* FIX BUG-4: null-guard checks */}
            {hasAnomalies && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-400 leading-relaxed">
                🚨 Isolation forest flagged <strong>{journey.anomaly_count}</strong> anomalous readings in your uploaded dataset.
              </div>
            )}
            {hasAbnormalHR && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-xs text-amber-400 leading-relaxed">
                ⚠️ Abnormal resting heart rate (<strong>{latestRecord.heart_rate} BPM</strong>). Inform your clinician if you feel discomfort.
              </div>
            )}
            {hasHighPPBS && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-400 leading-relaxed">
                🚨 Elevated postprandial blood sugar (<strong>{latestRecord.postprandial_blood_sugar} mg/dL</strong>) — potential Hyperglycemia.
              </div>
            )}
            {allClear && (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-xs text-emerald-400 leading-relaxed flex items-center gap-2">
                <CheckCircle className="h-3.5 w-3.5" />
                All readings are within safe clinical thresholds.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
