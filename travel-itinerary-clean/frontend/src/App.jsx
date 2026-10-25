import React, { useState, useEffect } from 'react';
import { api } from './api';

export default function App() {
  const [activeTrip, setActiveTrip] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedDay, setSelectedDay] = useState(1);
  const [savedTrips, setSavedTrips] = useState([]);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [isSavedModalOpen, setIsSavedModalOpen] = useState(false);
  const [regenDayModal, setRegenDayModal] = useState({ isOpen: false, dayNum: 1, prompt: '' });

  const [formData, setFormData] = useState({
    destination: 'Paris, France',
    start_date: '2026-06-01',
    end_date: '2026-06-04',
    budget_tier: 'moderate',
    budget_amount: 1200,
    travel_style: 'solo',
    group_size: 1,
    pace: 'balanced',
    interests: ['Food & Dining', 'Sightseeing', 'Culture'],
    special_notes: '',
  });

  const [copilotMessages, setCopilotMessages] = useState([
    {
      sender: 'ai',
      text: 'Hello! I am your AI Travel Copilot. Ask me anything about packing, local customs, eSIM cards, or transit for your trip!',
    },
  ]);
  const [copilotInput, setCopilotInput] = useState('');
  const [isCopilotLoading, setIsCopilotLoading] = useState(false);

  useEffect(() => {
    loadSavedTrips();
  }, []);

  const loadSavedTrips = async () => {
    try {
      const data = await api.listTrips();
      setSavedTrips(data);
    } catch (e) {
      console.warn('Trips fetch failed:', e);
    }
  };

  const handleGenerate = async (e) => {
    if (e) e.preventDefault();
    setIsGenerating(true);
    try {
      const trip = await api.generateTrip(formData);
      setActiveTrip(trip);
      setSelectedDay(1);
      loadSavedTrips();
    } catch (err) {
      alert(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const applyScenario = async (id) => {
    try {
      const scenario = await api.getScenario(id);
      setFormData(scenario.preset_data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRegenerateDay = async () => {
    if (!activeTrip) return;
    try {
      const updated = await api.regenerateDay(
        activeTrip.id,
        regenDayModal.dayNum,
        regenDayModal.prompt
      );
      setActiveTrip(updated);
      setRegenDayModal({ isOpen: false, dayNum: 1, prompt: '' });
      loadSavedTrips();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleSendCopilot = async (e) => {
    e.preventDefault();
    if (!copilotInput.trim()) return;
    const msg = copilotInput.trim();
    setCopilotInput('');
    setCopilotMessages((prev) => [...prev, { sender: 'user', text: msg }]);
    setIsCopilotLoading(true);

    try {
      const res = await api.askCopilot(
        activeTrip ? activeTrip.destination : formData.destination,
        msg
      );
      setCopilotMessages((prev) => [
        ...prev,
        { sender: 'ai', text: res.answer, actions: res.suggested_actions },
      ]);
    } catch (err) {
      setCopilotMessages((prev) => [
        ...prev,
        { sender: 'ai', text: 'Sorry, copilot service is currently unavailable.' },
      ]);
    } finally {
      setIsCopilotLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      {/* Navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">✈️</span>
            <span className="text-xl font-extrabold tracking-tight text-slate-900">
              Wander<span className="text-teal-600">AI</span>
            </span>
            <span className="text-xs bg-teal-50 text-teal-700 px-2.5 py-0.5 rounded-full font-semibold border border-teal-200">
              Personalized Travel Planner
            </span>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setIsSavedModalOpen(true)}
              className="text-sm font-medium text-slate-600 hover:text-slate-900 px-3 py-1.5 rounded-lg border border-slate-200"
            >
              Saved Trips ({savedTrips.length})
            </button>
            <button
              onClick={() => setIsCopilotOpen(!isCopilotOpen)}
              className="text-sm font-bold bg-teal-600 hover:bg-teal-700 text-white px-3.5 py-1.5 rounded-lg shadow-sm"
            >
              AI Copilot
            </button>
          </div>
        </div>
      </header>

      {/* Scenario Presets Bar */}
      <section className="bg-slate-900 text-white py-8 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-6">
            <h1 className="text-3xl font-extrabold">Personalized Travel Itinerary Planner</h1>
            <p className="text-slate-400 text-sm mt-1">
              Select a pre-built test scenario or build your custom trip below
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div
              onClick={() => applyScenario('scenario-1-solo-weekend')}
              className="bg-slate-800 p-4 rounded-xl border border-slate-700 hover:border-teal-500 cursor-pointer transition"
            >
              <div className="text-xs text-blue-400 font-bold mb-1">SCENARIO 1</div>
              <h3 className="font-bold text-base">Solo Traveler: Weekend Getaway</h3>
              <p className="text-xs text-slate-400 mt-1">
                Optimized 3-day Paris weekend for solo pace, walkability & food.
              </p>
            </div>

            <div
              onClick={() => applyScenario('scenario-2-couple-vacation')}
              className="bg-slate-800 p-4 rounded-xl border border-slate-700 hover:border-teal-500 cursor-pointer transition"
            >
              <div className="text-xs text-rose-400 font-bold mb-1">SCENARIO 2</div>
              <h3 className="font-bold text-base">Couple: Romantic Vacation</h3>
              <p className="text-xs text-slate-400 mt-1">
                6-Day Amalfi Coast with relaxed pacing, scenic stays & day regeneration.
              </p>
            </div>

            <div
              onClick={() => applyScenario('scenario-3-group-trip')}
              className="bg-slate-800 p-4 rounded-xl border border-slate-700 hover:border-teal-500 cursor-pointer transition"
            >
              <div className="text-xs text-emerald-400 font-bold mb-1">SCENARIO 3</div>
              <h3 className="font-bold text-base">Small Group: Multi-Day Trip</h3>
              <p className="text-xs text-slate-400 mt-1">
                Tokyo 6-day friends adventure with shared budget tracking.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 py-8 flex-1 w-full grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Form */}
        <div className="lg:col-span-5 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-lg font-bold text-slate-900 border-b pb-3">Smart Trip Builder</h2>
          <form onSubmit={handleGenerate} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Destination</label>
              <input
                type="text"
                required
                value={formData.destination}
                onChange={(e) => setFormData({ ...formData, destination: e.target.value })}
                className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Start Date</label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">End Date</label>
                <input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Travel Style</label>
                <select
                  value={formData.travel_style}
                  onChange={(e) => setFormData({ ...formData, travel_style: e.target.value })}
                  className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300"
                >
                  <option value="solo">Solo</option>
                  <option value="couple">Couple</option>
                  <option value="group">Small Group</option>
                  <option value="family">Family</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Group Size</label>
                <input
                  type="number"
                  min="1"
                  max="25"
                  value={formData.group_size}
                  onChange={(e) => setFormData({ ...formData, group_size: parseInt(e.target.value) || 1 })}
                  className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Budget Tier</label>
                <select
                  value={formData.budget_tier}
                  onChange={(e) => setFormData({ ...formData, budget_tier: e.target.value })}
                  className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300"
                >
                  <option value="budget">Budget ($)</option>
                  <option value="moderate">Moderate ($$)</option>
                  <option value="luxury">Luxury ($$$)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Target Budget ($)</label>
                <input
                  type="number"
                  value={formData.budget_amount}
                  onChange={(e) => setFormData({ ...formData, budget_amount: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isGenerating}
              className="w-full py-3 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-sm shadow-md transition disabled:opacity-50"
            >
              {isGenerating ? 'Generating AI Plan...' : 'Generate Itinerary'}
            </button>
          </form>
        </div>

        {/* Itinerary Display */}
        <div className="lg:col-span-7 space-y-6">
          {!activeTrip ? (
            <div className="bg-white p-12 text-center rounded-2xl border border-dashed border-slate-300">
              <span className="text-4xl">🗺️</span>
              <h3 className="text-lg font-bold text-slate-800 mt-2">Ready to plan your trip</h3>
              <p className="text-xs text-slate-500 mt-1">
                Select a preset or enter destination details to see your AI-generated itinerary.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Trip Header */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-xs font-bold text-teal-600 uppercase">
                      {activeTrip.travel_style} • {activeTrip.duration_days} Days
                    </span>
                    <h2 className="text-2xl font-extrabold text-slate-900">{activeTrip.title}</h2>
                    <p className="text-xs text-slate-500 mt-1">{activeTrip.overview}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400">Total Est. Cost</span>
                    <div className="text-xl font-extrabold text-slate-900">
                      ${activeTrip.budget_breakdown.total_estimated_cost}
                    </div>
                  </div>
                </div>

                {/* Day Selector */}
                <div className="flex gap-2 mt-6 overflow-x-auto">
                  {activeTrip.days.map((day) => (
                    <button
                      key={day.day_number}
                      onClick={() => setSelectedDay(day.day_number)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold ${
                        selectedDay === day.day_number
                          ? 'bg-slate-900 text-white'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      Day {day.day_number} (${day.estimated_daily_cost})
                    </button>
                  ))}
                </div>
              </div>

              {/* Day Details */}
              {activeTrip.days
                .filter((d) => d.day_number === selectedDay)
                .map((day) => (
                  <div key={day.day_number} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                    <div className="flex justify-between items-center border-b pb-3">
                      <div>
                        <h3 className="text-lg font-bold text-slate-900">
                          Day {day.day_number}: {day.theme}
                        </h3>
                        <p className="text-xs text-slate-500">{day.summary}</p>
                      </div>
                      <button
                        onClick={() => setRegenDayModal({ isOpen: true, dayNum: day.day_number, prompt: '' })}
                        className="text-xs font-bold bg-teal-50 text-teal-700 border border-teal-200 px-3 py-1.5 rounded-lg hover:bg-teal-100"
                      >
                        ⚡ Regenerate Day
                      </button>
                    </div>

                    <div className="space-y-3">
                      {day.activities.map((act) => (
                        <div key={act.id} className="p-3.5 rounded-xl border border-slate-200 bg-white">
                          <div className="flex justify-between items-start">
                            <div>
                              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                                {act.category} • {act.start_time} - {act.end_time}
                              </span>
                              <h4 className="font-bold text-slate-900 text-sm mt-1">{act.title}</h4>
                              <p className="text-xs text-slate-600 mt-0.5">{act.description}</p>
                              <div className="text-xs text-slate-400 mt-1">📍 {act.location}</div>
                            </div>
                            <span className="text-xs font-bold text-slate-800">${act.cost_estimate}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      </main>

      {/* Regeneration Modal */}
      {regenDayModal.isOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl">
            <h3 className="text-base font-bold mb-2">Regenerate Day {regenDayModal.dayNum}</h3>
            <textarea
              rows="3"
              value={regenDayModal.prompt}
              onChange={(e) => setRegenDayModal({ ...regenDayModal, prompt: e.target.value })}
              placeholder="e.g. Focus on fine dining, scenic viewpoints, less walking..."
              className="w-full p-2.5 text-xs rounded-xl border border-slate-300 mb-3"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setRegenDayModal({ isOpen: false, dayNum: 1, prompt: '' })}
                className="px-3 py-1.5 text-xs font-semibold text-slate-600"
              >
                Cancel
              </button>
              <button
                onClick={handleRegenerateDay}
                className="px-3 py-1.5 text-xs font-bold bg-teal-600 text-white rounded-lg"
              >
                Regenerate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
