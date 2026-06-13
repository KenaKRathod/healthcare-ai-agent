import React, { useState, useEffect } from "react";
import { authAPI } from "../services/api";
import { applyDarkMode, getStoredDarkMode } from "../utils/theme";
import {
  Activity,
  User,
  Lock,
  ArrowRight,
  Eye,
  EyeOff,
  Moon,
  Sun,
} from "lucide-react";

export default function Login({ onLoginSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [darkMode, setDarkMode] = useState(getStoredDarkMode);
  const [role, setRole] = useState("patient");
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    applyDarkMode(darkMode);
  }, [darkMode]);

  const toggleTheme = () => setDarkMode((prev) => !prev);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    if (!isLogin) {
      if (username.trim().length < 3) {
        setError("Username must be at least 3 characters long.");
        setLoading(false);
        return;
      }
      if (password.length < 6) {
        setError("Password must be at least 6 characters long.");
        setLoading(false);
        return;
      }
      if (!consent && role === "patient") {
        setError("You must consent to the HIPAA privacy policy to register as a patient.");
        setLoading(false);
        return;
      }
    }

    try {
      if (isLogin) {
        const data = await authAPI.login(username, password);
        onLoginSuccess(data.role, data.username);
      } else {
        await authAPI.register(username, password, role);
        setIsLogin(true);
        setUsername("");
        setPassword("");
        setError("Account created successfully! Please sign in.");
      }
    } catch (err) {
      setError(err.message || "An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell min-h-screen flex items-center justify-center px-4 relative overflow-hidden text-aura-text">
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-teal-500/10 dark:bg-teal-400/10 blur-[100px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-emerald-500/10 dark:bg-emerald-400/10 blur-[100px] pointer-events-none" />

      <button
        type="button"
        onClick={toggleTheme}
        className="absolute top-5 right-5 z-20 p-2.5 rounded-xl border border-aura-border bg-aura-surface/80 text-aura-text-muted hover:text-aura-accent transition-colors"
        title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
      >
        {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </button>

      <div className="auth-panel w-full max-w-md p-8 relative z-10">
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 rounded-2xl mb-4 border border-teal-500/25 bg-teal-500/10 pulse-ring">
            <Activity className="h-10 w-10 text-teal-600 dark:text-teal-400" />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight aura-gradient-text">
            AuraHealth AI
          </h1>
          <p className="text-aura-text-muted text-sm mt-2 text-center">
            Your Personal AI Healthcare Companion
          </p>
        </div>

        {error && (
          <div
            className={`p-4 rounded-xl mb-6 text-sm ${
              error.includes("successfully")
                ? "bg-emerald-500/10 border border-emerald-500/25 text-emerald-700 dark:text-emerald-400"
                : "bg-red-500/10 border border-red-500/25 text-red-700 dark:text-red-400"
            }`}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold text-aura-text-muted uppercase tracking-wider mb-2">
              Username
            </label>
            <div className="relative">
              <User className="absolute left-3 top-3.5 h-5 w-5 text-aura-text-muted" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                className="auth-input w-full pl-10 pr-4 py-3"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-aura-text-muted uppercase tracking-wider mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-3.5 h-5 w-5 text-aura-text-muted" />
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                className="auth-input w-full pl-10 pr-12 py-3"
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-3 top-3.5 text-aura-text-muted hover:text-aura-accent transition-colors"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5" />
                ) : (
                  <Eye className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>

          {!isLogin && (
            <div>
              <label className="block text-xs font-semibold text-aura-text-muted uppercase tracking-wider mb-2">
                Account Role
              </label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="auth-input w-full px-4 py-3"
              >
                <option value="patient">Patient</option>
                <option value="doctor">Medical Doctor</option>
                <option value="caregiver">Caregiver / Family Member</option>
              </select>
            </div>
          )}

          {!isLogin && role === "patient" && (
            <div className="flex items-start gap-3 mt-4">
              <input
                id="consent-checkbox"
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                className="mt-1 h-4 w-4 rounded border-aura-border bg-aura-muted text-teal-600 focus:ring-teal-500"
              />
              <label htmlFor="consent-checkbox" className="text-xs text-aura-text-muted leading-normal">
                I consent to the secure storage and processing of my health history under HIPAA compliance guidelines.
              </label>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 dark:from-teal-500 dark:to-emerald-500 dark:hover:from-teal-400 dark:hover:to-emerald-400 text-white font-bold rounded-xl flex items-center justify-center gap-2 shadow-lg transition-all duration-300 disabled:opacity-50"
          >
            {loading ? (
              <span className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                {isLogin ? "Sign In" : "Register"}
                <ArrowRight className="h-5 w-5" />
              </>
            )}
          </button>
        </form>

        <div className="mt-8 text-center border-t border-aura-border pt-6">
          <button
            onClick={() => {
              setIsLogin(!isLogin);
              setError("");
            }}
            className="text-sm text-teal-700 dark:text-teal-400 hover:text-teal-600 dark:hover:text-teal-300 font-medium transition-colors"
          >
            {isLogin
              ? "New to AuraHealth AI? Create an account"
              : "Already have an account? Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
}
