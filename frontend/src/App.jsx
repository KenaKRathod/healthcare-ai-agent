import React, { useState, useEffect } from "react";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";
import Chatbot from "./components/Chatbot";
import MedicationTracker from "./components/MedicationTracker";
import GoalsManager from "./components/GoalsManager";
import DoctorPortal from "./components/DoctorPortal";
import CaregiverPortal from "./components/CaregiverPortal";
import { getRole, getUsername, logout } from "./services/api";
import { applyDarkMode, getStoredDarkMode } from "./utils/theme";
import {
  Activity,
  LogOut,
  Moon,
  Sun,
  LayoutDashboard,
  MessageSquareHeart,
  Pill,
  ShieldCheck,
  User,
  Heart,
  Settings,
} from "lucide-react";

export default function App() {
  const [role, setRole] = useState(getRole());
  const [username, setUsername] = useState(getUsername());
  const [activeTab, setActiveTab] = useState("dashboard");
  const [darkMode, setDarkMode] = useState(getStoredDarkMode);

  useEffect(() => {
    applyDarkMode(darkMode);
  }, [darkMode]);

  const toggleTheme = () => setDarkMode((prev) => !prev);

  const handleLoginSuccess = (userRole, userName) => {
    setRole(userRole);
    setUsername(userName);
    // Set appropriate starting tab based on role
    if (userRole === "doctor") {
      setActiveTab("doctor-portal");
    } else if (userRole === "caregiver") {
      setActiveTab("caregiver-portal");
    } else {
      setActiveTab("dashboard");
    }
  };

  const handleLogout = () => {
    logout();
    setRole(null);
    setUsername(null);
  };

  if (!role) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-aura-bg text-aura-text transition-colors duration-300">
      {/* Top Header Navbar */}
      <header className="sticky top-0 z-40 backdrop-blur-md border-b border-aura-border bg-aura-surface/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-teal-500/10 border border-teal-500/20 rounded-xl">
              <Activity className="h-5 w-5 text-teal-500 dark:text-teal-400" />
            </div>
            <span className="font-extrabold text-xl tracking-tight aura-gradient-text">
              AuraHealth AI
            </span>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={toggleTheme}
              className="p-2.5 border border-aura-border bg-aura-muted hover:text-aura-accent text-aura-text-muted rounded-xl transition-colors"
            >
              {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>

            <div className="flex items-center gap-3 border-l border-aura-border pl-4">
              <div className="text-right hidden sm:block">
                <div className="text-xs font-semibold text-aura-text">{username}</div>
                <div className="text-[10px] text-aura-text-muted uppercase tracking-widest font-bold capitalize">{role}</div>
              </div>
              <button
                onClick={handleLogout}
                className="p-2.5 border border-aura-border bg-aura-muted hover:border-red-500/30 hover:text-red-500 rounded-xl transition-colors"
                title="Log Out"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Body Shell */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col lg:flex-row gap-8">
        {/* Navigation Sidebar Panel */}
        <aside className="w-full lg:w-64 shrink-0">
          <nav className="glass-panel p-4 space-y-1">
            {role === "patient" && (
              <>
                <button
                  onClick={() => setActiveTab("dashboard")}
                  className={`w-full px-4 py-3 rounded-xl text-left text-sm font-bold flex items-center gap-3 transition-colors ${activeTab === "dashboard" ? "bg-teal-500/10 text-teal-600 dark:text-teal-400" : "text-aura-text-muted hover:bg-aura-muted"}`}
                >
                  <LayoutDashboard className="h-4 w-4" />
                  Health Dashboard
                </button>
                <button
                  onClick={() => setActiveTab("chatbot")}
                  className={`w-full px-4 py-3 rounded-xl text-left text-sm font-bold flex items-center gap-3 transition-colors ${activeTab === "chatbot" ? "bg-teal-500/10 text-teal-600 dark:text-teal-400" : "text-aura-text-muted hover:bg-aura-muted"}`}
                >
                  <MessageSquareHeart className="h-4 w-4" />
                  AuraHealth Chatbot
                </button>
                <button
                  onClick={() => setActiveTab("medications")}
                  className={`w-full px-4 py-3 rounded-xl text-left text-sm font-bold flex items-center gap-3 transition-colors ${activeTab === "medications" ? "bg-teal-500/10 text-teal-600 dark:text-teal-400" : "text-aura-text-muted hover:bg-aura-muted"}`}
                >
                  <Pill className="h-4 w-4" />
                  Medication Tracker
                </button>
                <button
                  onClick={() => setActiveTab("goals")}
                  className={`w-full px-4 py-3 rounded-xl text-left text-sm font-bold flex items-center gap-3 transition-colors ${activeTab === "goals" ? "bg-teal-500/10 text-teal-600 dark:text-teal-400" : "text-aura-text-muted hover:bg-aura-muted"}`}
                >
                  <Heart className="h-4 w-4" />
                  Wellness Goals
                </button>
              </>
            )}

            {role === "doctor" && (
              <button
                onClick={() => setActiveTab("doctor-portal")}
                className={`w-full px-4 py-3 rounded-xl text-left text-sm font-bold flex items-center gap-3 transition-colors ${activeTab === "doctor-portal" ? "bg-teal-500/10 text-teal-600 dark:text-teal-400" : "text-aura-text-muted hover:bg-aura-muted"}`}
              >
                <ShieldCheck className="h-4 w-4" />
                Clinician Portal
              </button>
            )}

            {role === "caregiver" && (
              <button
                onClick={() => setActiveTab("caregiver-portal")}
                className={`w-full px-4 py-3 rounded-xl text-left text-sm font-bold flex items-center gap-3 transition-colors ${activeTab === "caregiver-portal" ? "bg-teal-500/10 text-teal-600 dark:text-teal-400" : "text-aura-text-muted hover:bg-aura-muted"}`}
              >
                <User className="h-4 w-4" />
                Caregiver Portal
              </button>
            )}
          </nav>
        </aside>

        {/* Dynamic page container */}
        <main className="flex-1 min-w-0">
          {activeTab === "dashboard" && <Dashboard username={username} />}
          {activeTab === "chatbot" && <Chatbot username={username} />}
          {activeTab === "medications" && <MedicationTracker username={username} />}
          {activeTab === "goals" && <GoalsManager username={username} />}
          {activeTab === "doctor-portal" && <DoctorPortal />}
          {activeTab === "caregiver-portal" && <CaregiverPortal />}
        </main>
      </div>
    </div>
  );
}
