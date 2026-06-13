import React, { useState, useEffect, useCallback, useRef } from "react";
import { goalsAPI } from "../services/api";
import { Plus, Check, Award, Sparkles, TrendingUp, AlertCircle, RefreshCw, Edit2, X, Trophy } from "lucide-react";

// ─── Ring Progress SVG ────────────────────────────────────────────────────────
function RingProgress({ percent, color = "#14b8a6", size = 80 }) {
  const r = (size - 10) / 2;
  const circ = 2 * Math.PI * r;
  const filled = Math.min(percent, 100);
  const strokeDash = (filled / 100) * circ;

  return (
    <svg width={size} height={size} className="rotate-[-90deg]">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth={8} />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={8}
        strokeLinecap="round"
        strokeDasharray={`${strokeDash} ${circ}`}
        style={{ transition: "stroke-dasharray 0.6s ease" }}
      />
    </svg>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function getStatusColor(pct) {
  if (pct >= 80) return { ring: "#10b981", text: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20", label: "On Track" };
  if (pct >= 50) return { ring: "#f59e0b", text: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20", label: "In Progress" };
  return { ring: "#f43f5e", text: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/20", label: "Needs Attention" };
}

function formatGoalName(name) {
  return name.replaceAll("_", " ");
}

// ─── Inline Edit Component ────────────────────────────────────────────────────
function InlineEdit({ currentValue, onSave, onCancel }) {
  const [val, setVal] = useState(String(currentValue));
  const inputRef = useRef(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const parsed = parseFloat(val);
    if (!isNaN(parsed) && parsed > 0) onSave(parsed);
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2 mt-2">
      <input
        ref={inputRef}
        type="number"
        step="any"
        value={val}
        onChange={(e) => setVal(e.target.value)}
        className="w-28 px-3 py-1.5 bg-slate-900 border border-teal-500/50 rounded-lg focus:outline-none text-slate-100 text-sm"
      />
      <button type="submit" className="p-1.5 bg-teal-500/20 hover:bg-teal-500/40 text-teal-400 rounded-lg border border-teal-500/30 transition-colors">
        <Check className="h-3.5 w-3.5" />
      </button>
      <button type="button" onClick={onCancel} className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded-lg border border-slate-700 transition-colors">
        <X className="h-3.5 w-3.5" />
      </button>
    </form>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function GoalsManager({ username }) {
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  // L-BUG-14 FIX: separate recalculating state from initial load so the Recalculate
  // button doesn't show a spinner on first page mount
  const [isRecalculating, setIsRecalculating] = useState(false);
  const [error, setError] = useState(null);
  const [editingGoalId, setEditingGoalId] = useState(null);

  // Create goal form state
  const [showAddForm, setShowAddForm] = useState(false);
  const [goalName, setGoalName] = useState("daily_steps");
  const [targetValue, setTargetValue] = useState("");
  const [unit, setUnit] = useState("steps");

  // Progress inputs — stored locally, fetched on "Recalculate" (FIX BUG-3: no longer fires API on every keystroke)
  const [stepsInput, setStepsInput] = useState(() => localStorage.getItem(`${username}_stepsInput`) || "0");
  const [sleepInput, setSleepInput] = useState(() => localStorage.getItem(`${username}_sleepInput`) || "0");
  const [weightInput, setWeightInput] = useState(() => localStorage.getItem(`${username}_weightInput`) || "0");

  // The values actually sent to the API (only updated when user clicks Recalculate)
  const [progressValues, setProgressValues] = useState(() => ({
    steps: parseFloat(localStorage.getItem(`${username}_stepsInput`)) || 0,
    sleep: parseFloat(localStorage.getItem(`${username}_sleepInput`)) || 0,
    weight: parseFloat(localStorage.getItem(`${username}_weightInput`)) || 0,
  }));

  const fetchGoals = useCallback(async (steps, sleep, weight, recalculating = false) => {
    try {
      if (recalculating) setIsRecalculating(true);
      else setLoading(true);
      setError(null);
      const data = await goalsAPI.getGoals(
        username,
        parseFloat(steps) || 0,
        parseFloat(sleep) || 0,
        parseFloat(weight) || 0
      );
      setGoals(data);
    } catch (err) {
      setError(err.message || "Failed to load goals. Please try again.");
    } finally {
      setLoading(false);
      setIsRecalculating(false);
    }
  }, [username]);

  useEffect(() => {
    const savedSteps = localStorage.getItem(`${username}_stepsInput`) || "0";
    const savedSleep = localStorage.getItem(`${username}_sleepInput`) || "0";
    const savedWeight = localStorage.getItem(`${username}_weightInput`) || "0";
    fetchGoals(savedSteps, savedSleep, savedWeight);
  }, [username, fetchGoals]);

  const handleRecalculate = () => {
    const s = parseFloat(stepsInput) || 0;
    const sl = parseFloat(sleepInput) || 0;
    const w = parseFloat(weightInput) || 0;
    setProgressValues({ steps: s, sleep: sl, weight: w });
    localStorage.setItem(`${username}_stepsInput`, stepsInput);
    localStorage.setItem(`${username}_sleepInput`, sleepInput);
    localStorage.setItem(`${username}_weightInput`, weightInput);
    fetchGoals(s, sl, w, true); // pass recalculating=true to use separate spinner state
  };

  const handleCreateGoal = async (e) => {
    e.preventDefault();
    try {
      await goalsAPI.createGoal(username, goalName, parseFloat(targetValue), unit);
      setShowAddForm(false);
      setTargetValue("");
      fetchGoals(progressValues.steps, progressValues.sleep, progressValues.weight);
    } catch (err) {
      setError(`Failed to create goal: ${err.message}`);
    }
  };

  // FIX BUG-8: replaced window.prompt with inline edit UI
  const handleInlineSave = async (goalId, newTarget) => {
    try {
      await goalsAPI.updateGoal(goalId, newTarget);
      setEditingGoalId(null);
      fetchGoals(progressValues.steps, progressValues.sleep, progressValues.weight);
    } catch (err) {
      setError(`Failed to update goal: ${err.message}`);
    }
  };

  // L-BUG-12 FIX: always sync unit when goal name changes; add else fallback
  const updateUnit = (name) => {
    if (name === "daily_steps") setUnit("steps");
    else if (name === "sleep_hours") setUnit("hours");
    else if (name === "weight_loss_kg") setUnit("kg");
    else setUnit(""); // fallback for any future custom goal types
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-100">
            Wellness Goals Manager
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Track daily targets and get insights powered by AuraHealth AI.
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-4 py-2.5 bg-teal-500 hover:bg-teal-600 text-slate-950 font-bold rounded-xl flex items-center gap-2 transition-colors shadow-lg"
        >
          <Plus className="h-5 w-5" />
          Configure New Goal
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="flex items-start gap-3 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto shrink-0 hover:text-rose-300">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Goal Form */}
      {showAddForm && (
        <form onSubmit={handleCreateGoal} className="glass-panel p-6 border border-slate-800 bg-slate-950/60 space-y-6 max-w-xl mx-auto">
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Plus className="h-5 w-5 text-teal-400" />
            Set Wellness Goal
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Goal Category
              </label>
              <select
                value={goalName}
                onChange={(e) => {
                  setGoalName(e.target.value);
                  updateUnit(e.target.value);
                }}
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl focus:border-teal-500 focus:outline-none text-slate-100"
              >
                <option value="daily_steps">Daily Steps Goal</option>
                <option value="sleep_hours">Sleep Hours Goal</option>
                <option value="weight_loss_kg">Weight Loss Goal</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Target Value
              </label>
              <input
                type="number"
                step="any"
                required
                value={targetValue}
                onChange={(e) => setTargetValue(e.target.value)}
                placeholder="e.g. 8000"
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl focus:border-teal-500 focus:outline-none text-slate-100"
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => setShowAddForm(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-xl"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2 bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 text-slate-950 font-bold rounded-xl"
            >
              Activate Goal
            </button>
          </div>
        </form>
      )}

      {/* Progress Update Panel — FIX BUG-3: now uses explicit Recalculate button */}
      <div className="glass-panel p-6 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-teal-400" />
            Today's Progress Values
          </h3>
          <button
            onClick={handleRecalculate}
            disabled={loading || isRecalculating}
            className="px-4 py-2 bg-teal-500/10 hover:bg-teal-500/20 border border-teal-500/30 text-teal-400 font-bold rounded-xl flex items-center gap-2 text-sm transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isRecalculating ? "animate-spin" : ""}`} />
            Recalculate
          </button>
        </div>
        <p className="text-xs text-slate-500">Enter today's values and click Recalculate to update your goal progress.</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Steps taken today
            </label>
            <input
              type="number"
              value={stepsInput}
              onChange={(e) => setStepsInput(e.target.value)}
              placeholder="e.g. 6400"
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl focus:border-teal-500 focus:outline-none text-slate-100"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Hours slept last night
            </label>
            <input
              type="number"
              step="any"
              value={sleepInput}
              onChange={(e) => setSleepInput(e.target.value)}
              placeholder="e.g. 7.5"
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl focus:border-teal-500 focus:outline-none text-slate-100"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Weight loss progress (kg)
            </label>
            <input
              type="number"
              step="any"
              value={weightInput}
              onChange={(e) => setWeightInput(e.target.value)}
              placeholder="e.g. 1.2"
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl focus:border-teal-500 focus:outline-none text-slate-100"
            />
          </div>
        </div>
      </div>

      {/* Goal Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {loading ? (
          // Skeleton loaders
          [1, 2, 3].map((n) => (
            <div key={n} className="glass-panel p-6 border border-slate-800 space-y-4 animate-pulse">
              <div className="h-4 bg-slate-800 rounded-full w-1/2" />
              <div className="h-3 bg-slate-800 rounded-full w-3/4" />
              <div className="h-2 bg-slate-800 rounded-full w-full" />
              <div className="h-12 bg-slate-800/50 rounded-xl w-full" />
            </div>
          ))
        ) : goals.length > 0 ? (
          goals.map((goal) => {
            const pct = Math.round(goal.progress_percent);
            const status = getStatusColor(pct);
            const isComplete = pct >= 100;
            const isEditing = editingGoalId === goal.goal_id;

            return (
              <div
                key={goal.goal_id}
                className="glass-panel p-6 border border-slate-800 flex flex-col justify-between space-y-4 hover:border-slate-700 transition-colors"
              >
                {/* Card Top */}
                <div>
                  <div className="flex items-start justify-between gap-4">
                    {/* Ring + info */}
                    <div className="flex items-center gap-4">
                      <div className="relative shrink-0">
                        <RingProgress percent={pct} color={status.ring} size={72} />
                        <div className="absolute inset-0 flex items-center justify-center">
                          {isComplete ? (
                            <Trophy className="h-5 w-5 text-amber-400" />
                          ) : (
                            <span className={`text-xs font-extrabold ${status.text}`}>{pct}%</span>
                          )}
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-extrabold text-slate-100 text-base capitalize">
                            {/* FIX BUG-1: replaceAll replaces ALL underscores */}
                            {formatGoalName(goal.goal_name)}
                          </h4>
                          {isComplete && (
                            <span className="px-2 py-0.5 bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[10px] font-bold rounded-full uppercase tracking-wider">
                              Achieved!
                            </span>
                          )}
                        </div>
                        <p className="text-slate-400 text-xs mt-1">
                          <span className={`font-bold ${status.text}`}>
                            {goal.current_value.toLocaleString()} {goal.unit}
                          </span>{" "}
                          of{" "}
                          <span className="text-slate-300 font-semibold">
                            {goal.target_value.toLocaleString()} {goal.unit}
                          </span>
                        </p>
                        {/* Status badge */}
                        <span className={`mt-1.5 inline-block px-2 py-0.5 border text-[10px] font-bold uppercase tracking-wider rounded-full ${status.bg} ${status.text}`}>
                          {isComplete ? "Goal Complete" : status.label}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Flat progress bar (secondary visual) */}
                  <div className="w-full bg-slate-900 rounded-full h-1.5 mt-4">
                    <div
                      className="h-1.5 rounded-full transition-all duration-700"
                      style={{
                        width: `${Math.min(pct, 100)}%`,
                        backgroundColor: status.ring,
                      }}
                    />
                  </div>
                </div>

                {/* AI Recommendation */}
                <div className="bg-slate-950/40 p-3.5 rounded-xl border border-slate-900 flex items-start gap-2.5">
                  <Sparkles className="h-4 w-4 text-teal-400 shrink-0 mt-0.5" />
                  <p className="text-xs text-slate-400 leading-normal">{goal.recommendation}</p>
                </div>

                {/* Edit section */}
                <div className="flex justify-end gap-2 pt-1">
                  {!isEditing ? (
                    <button
                      onClick={() => setEditingGoalId(goal.goal_id)}
                      className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-teal-500/30 text-xs font-semibold rounded-lg text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1.5"
                    >
                      <Edit2 className="h-3.5 w-3.5" />
                      Adjust Target
                    </button>
                  ) : (
                    <InlineEdit
                      currentValue={goal.target_value}
                      onSave={(val) => handleInlineSave(goal.goal_id, val)}
                      onCancel={() => setEditingGoalId(null)}
                    />
                  )}
                </div>
              </div>
            );
          })
        ) : (
          /* Enhanced empty state */
          <div className="col-span-2 flex flex-col items-center justify-center py-16 text-center border border-slate-800 border-dashed rounded-2xl bg-slate-950/20 space-y-4">
            <div className="p-4 bg-teal-500/5 border border-teal-500/10 rounded-2xl">
              <Award className="h-10 w-10 text-teal-500/40" />
            </div>
            <div>
              <p className="text-slate-400 font-semibold">No goals configured yet</p>
              <p className="text-slate-600 text-sm mt-1">Create a wellness goal above, or ingest a health dataset to auto-generate goals.</p>
            </div>
            <button
              onClick={() => setShowAddForm(true)}
              className="px-5 py-2.5 bg-teal-500/10 hover:bg-teal-500/20 border border-teal-500/30 text-teal-400 font-bold rounded-xl text-sm transition-colors flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Set Your First Goal
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
