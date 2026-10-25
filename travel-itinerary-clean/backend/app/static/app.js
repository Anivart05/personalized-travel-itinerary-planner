const { useState, useEffect, useRef } = React;

// Category Badge Color Mapping
const CATEGORY_STYLES = {
  attraction: { bg: 'bg-blue-50 text-blue-700 border-blue-200', icon: 'compass', label: 'Attraction' },
  dining: { bg: 'bg-amber-50 text-amber-700 border-amber-200', icon: 'utensils', label: 'Dining' },
  accommodation: { bg: 'bg-purple-50 text-purple-700 border-purple-200', icon: 'bed', label: 'Stay' },
  transit: { bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: 'navigation', label: 'Transit' },
  leisure: { bg: 'bg-rose-50 text-rose-700 border-rose-200', icon: 'sparkles', label: 'Leisure' },
};

function App() {
  // Navigation & View state
  const [activeTab, setActiveTab] = useState('planner'); // 'planner', 'saved', 'scenarios'
  const [selectedDay, setSelectedDay] = useState(1);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [isSavedModalOpen, setIsSavedModalOpen] = useState(false);

  // Active Trip State
  const [activeTrip, setActiveTrip] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [savedTrips, setSavedTrips] = useState([]);

  // Modals state
  const [regenDayModal, setRegenDayModal] = useState({ isOpen: false, dayNum: 1, prompt: '' });
  const [addActivityModal, setAddActivityModal] = useState({ isOpen: false, dayNum: 1 });
  const [editActivityModal, setEditActivityModal] = useState({ isOpen: false, activity: null, dayNum: 1 });

  // Form builder state
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

  // Copilot messages
  const [copilotMessages, setCopilotMessages] = useState([
    {
      sender: 'ai',
      text: 'Hello! I am your AI Travel Copilot. Ask me anything about packing, local customs, eSIM cards, or transit for your trip!',
    },
  ]);
  const [copilotInput, setCopilotInput] = useState('');
  const [isCopilotLoading, setIsCopilotLoading] = useState(false);

  // Available Interests
  const AVAILABLE_INTERESTS = [
    'Sightseeing', 'Food & Dining', 'Culture', 'Nature',
    'Adventure', 'Nightlife', 'Relaxation', 'Shopping', 'Art & Museums'
  ];

  // Load saved trips on mount
  useEffect(() => {
    fetchSavedTrips();
  }, []);

  // Initialize Lucide icons
  useEffect(() => {
    if (window.lucide) {
      window.lucide.createIcons();
    }
  }, [activeTrip, activeTab, selectedDay, isCopilotOpen]);

  const fetchSavedTrips = async () => {
    try {
      const res = await fetch('/api/trips');
      if (res.ok) {
        const data = await res.json();
        setSavedTrips(data);
      }
    } catch (err) {
      console.warn('Could not fetch saved trips', err);
    }
  };

  // Generate Itinerary API Call
  const handleGenerateTrip = async (e) => {
    if (e) e.preventDefault();
    setIsGenerating(true);
    try {
      const res = await fetch('/api/trips/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!res.ok) throw new Error('Generation failed');
      const trip = await res.json();
      setActiveTrip(trip);
      setSelectedDay(1);
      fetchSavedTrips();
    } catch (err) {
      alert('Error generating itinerary: ' + err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  // Load Scenario Preset
  const handleApplyScenario = async (scenarioId) => {
    try {
      const res = await fetch(`/api/scenarios/${scenarioId}`);
      if (res.ok) {
        const scenario = await res.json();
        setFormData(scenario.preset_data);
        setActiveTab('planner');
        // Auto scroll to form
        window.scrollTo({ top: 380, behavior: 'smooth' });
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Regenerate Day Action
  const handleRegenerateDay = async () => {
    if (!activeTrip) return;
    try {
      const res = await fetch(`/api/trips/${activeTrip.id}/regenerate-day`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          day_number: regenDayModal.dayNum,
          refinement_prompt: regenDayModal.prompt,
        }),
      });

      if (!res.ok) throw new Error('Day regeneration failed');
      const updated = await res.json();
      setActiveTrip(updated);
      setRegenDayModal({ isOpen: false, dayNum: 1, prompt: '' });
      fetchSavedTrips();
    } catch (err) {
      alert('Failed to regenerate day: ' + err.message);
    }
  };

  // Delete Activity
  const handleDeleteActivity = async (activityId) => {
    if (!activeTrip || !confirm('Are you sure you want to remove this activity?')) return;
    try {
      const res = await fetch(`/api/trips/${activeTrip.id}/activities/${activityId}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        const updated = await res.json();
        setActiveTrip(updated);
      }
    } catch (err) {
      alert('Failed to delete activity: ' + err.message);
    }
  };

  // Toggle Activity Completed
  const handleToggleCompleted = (dayNum, actId) => {
    if (!activeTrip) return;
    const cloned = { ...activeTrip };
    const day = cloned.days.find((d) => d.day_number === dayNum);
    if (day) {
      const act = day.activities.find((a) => a.id === actId);
      if (act) {
        act.is_completed = !act.is_completed;
        setActiveTrip(cloned);
      }
    }
  };

  // Ask Copilot
  const handleSendCopilot = async (e) => {
    e.preventDefault();
    if (!copilotInput.trim()) return;
    const userMsg = copilotInput.trim();
    setCopilotInput('');
    setCopilotMessages((prev) => [...prev, { sender: 'user', text: userMsg }]);
    setIsCopilotLoading(true);

    try {
      const res = await fetch('/api/trips/copilot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          destination: activeTrip ? activeTrip.destination : formData.destination,
          question: userMsg,
        }),
      });
      const data = await res.json();
      setCopilotMessages((prev) => [
        ...prev,
        { sender: 'ai', text: data.answer, actions: data.suggested_actions },
      ]);
    } catch (err) {
      setCopilotMessages((prev) => [
        ...prev,
        { sender: 'ai', text: 'Sorry, I had trouble processing your question. Please try again.' },
      ]);
    } finally {
      setIsCopilotLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* HEADER NAVBAR */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm no-print">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('planner')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-teal-400 flex items-center justify-center text-white shadow-md shadow-brand-500/20 font-bold text-xl">
              ✈️
            </div>
            <div>
              <span className="text-xl font-extrabold tracking-tight text-slate-900">
                Wander<span className="text-brand-600">AI</span>
              </span>
              <span className="hidden sm:inline-block ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-brand-50 text-brand-700 border border-brand-200">
                FastAPI + React + Supabase
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-2 sm:space-x-4">
            <button
              onClick={() => setIsSavedModalOpen(true)}
              className="flex items-center space-x-1.5 px-3.5 py-2 text-sm font-medium rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition"
            >
              <span>📁 Saved Trips</span>
              <span className="text-xs font-bold bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded-full">
                {savedTrips.length}
              </span>
            </button>

            <button
              onClick={() => setIsCopilotOpen(!isCopilotOpen)}
              className="flex items-center space-x-1.5 px-3.5 py-2 text-sm font-semibold rounded-lg bg-brand-50 text-brand-700 border border-brand-200 hover:bg-brand-100 transition"
            >
              <span>✨ AI Copilot</span>
            </button>

            <a
              href="/docs"
              target="_blank"
              className="hidden md:inline-flex items-center px-3 py-2 text-xs font-semibold text-slate-500 hover:text-slate-800 border border-slate-200 rounded-lg"
            >
              API Docs
            </a>
          </div>
        </div>
      </header>

      {/* HERO SCENARIO PRESETS BAR */}
      <section className="bg-gradient-to-b from-teal-900 to-slate-900 text-white py-10 px-4 sm:px-6 lg:px-8 no-print">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-8">
            <span className="text-brand-400 text-xs font-bold uppercase tracking-wider bg-brand-900/50 px-3 py-1 rounded-full border border-brand-500/30">
              Smart Travel Automation
            </span>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-3">
              Personalized AI Travel Itinerary Planner
            </h1>
            <p className="text-slate-300 text-sm sm:text-base mt-2">
              Generate optimized day-by-day itineraries tailored to your budget, travel style, and pace.
              Zero decision fatigue, curated logistics, and instant day regeneration.
            </p>
          </div>

          {/* Quick Scenario Selector Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div
              onClick={() => handleApplyScenario('scenario-1-solo-weekend')}
              className="bg-slate-800/80 hover:bg-slate-800 border border-slate-700 hover:border-brand-500 rounded-xl p-4 cursor-pointer transition transform hover:-translate-y-1 shadow-lg"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                  Scenario 1: Solo
                </span>
                <span className="text-xs text-slate-400">3 Days • Paris</span>
              </div>
              <h3 className="font-bold text-white text-base">Solo Weekend Getaway</h3>
              <p className="text-xs text-slate-300 mt-1">
                Optimized walking routes, safe evening cafes, and top landmarks for solo travelers with limited research time.
              </p>
              <div className="mt-3 text-xs text-brand-400 font-semibold flex items-center">
                Load Solo Preset →
              </div>
            </div>

            <div
              onClick={() => handleApplyScenario('scenario-2-couple-vacation')}
              className="bg-slate-800/80 hover:bg-slate-800 border border-slate-700 hover:border-brand-500 rounded-xl p-4 cursor-pointer transition transform hover:-translate-y-1 shadow-lg"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                  Scenario 2: Couple
                </span>
                <span className="text-xs text-slate-400">6 Days • Amalfi Coast</span>
              </div>
              <h3 className="font-bold text-white text-base">Romantic Couple Vacation</h3>
              <p className="text-xs text-slate-300 mt-1">
                Relaxed pacing, cliffside sunset dining, scenic viewpoints, and personalized day regeneration.
              </p>
              <div className="mt-3 text-xs text-brand-400 font-semibold flex items-center">
                Load Romantic Preset →
              </div>
            </div>

            <div
              onClick={() => handleApplyScenario('scenario-3-group-trip')}
              className="bg-slate-800/80 hover:bg-slate-800 border border-slate-700 hover:border-brand-500 rounded-xl p-4 cursor-pointer transition transform hover:-translate-y-1 shadow-lg"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Scenario 3: Small Group
                </span>
                <span className="text-xs text-slate-400">6 Days • Tokyo</span>
              </div>
              <h3 className="font-bold text-white text-base">Group Adventure Coordination</h3>
              <p className="text-xs text-slate-300 mt-1">
                Shared budget tracking, balanced group interests (food, nightlife, culture), and minimized delays.
              </p>
              <div className="mt-3 text-xs text-brand-400 font-semibold flex items-center">
                Load Group Preset →
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* MAIN CONTAINER */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* LEFT COLUMN: SMART TRIP BUILDER FORM */}
          <div className="lg:col-span-5 space-y-6 no-print">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-5">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Smart Trip Builder</h2>
                  <p className="text-xs text-slate-500">Input your preferences to generate your tailored plan</p>
                </div>
                <span className="w-8 h-8 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center font-bold text-sm">
                  ⚡
                </span>
              </div>

              <form onSubmit={handleGenerateTrip} className="space-y-4">
                {/* Destination */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Destination
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.destination}
                    onChange={(e) => setFormData({ ...formData, destination: e.target.value })}
                    placeholder="e.g. Paris, Tokyo, Rome, New York, Bali"
                    className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition font-medium"
                  />
                  {/* Destination quick chips */}
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {['Paris, France', 'Tokyo, Japan', 'Rome, Italy', 'New York, USA', 'Bali, Indonesia', 'Amalfi Coast, Italy'].map((city) => (
                      <button
                        key={city}
                        type="button"
                        onClick={() => setFormData({ ...formData, destination: city })}
                        className="text-[11px] font-medium bg-slate-100 hover:bg-slate-200 text-slate-600 px-2 py-0.5 rounded-md transition"
                      >
                        {city.split(',')[0]}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Dates */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      required
                      value={formData.start_date}
                      onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                      className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      End Date
                    </label>
                    <input
                      type="date"
                      required
                      value={formData.end_date}
                      onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                      className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                </div>

                {/* Travel Style & Group Size */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      Travel Style
                    </label>
                    <select
                      value={formData.travel_style}
                      onChange={(e) => setFormData({ ...formData, travel_style: e.target.value })}
                      className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 font-medium"
                    >
                      <option value="solo">Solo Traveler</option>
                      <option value="couple">Couple / Romantic</option>
                      <option value="group">Small Group / Friends</option>
                      <option value="family">Family Trip</option>
                      <option value="business">Business & Leisure</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      Group Size
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="30"
                      value={formData.group_size}
                      onChange={(e) => setFormData({ ...formData, group_size: parseInt(e.target.value) || 1 })}
                      className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                </div>

                {/* Budget Tier & Target Budget */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      Budget Tier
                    </label>
                    <select
                      value={formData.budget_tier}
                      onChange={(e) => setFormData({ ...formData, budget_tier: e.target.value })}
                      className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 font-medium"
                    >
                      <option value="backpacker">Backpacker ($)</option>
                      <option value="budget">Budget ($$)</option>
                      <option value="moderate">Moderate ($$$)</option>
                      <option value="luxury">Luxury ($$$$)</option>
                      <option value="ultra_luxury">Ultra Luxury ($$$$$)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      Target Budget ($ USD)
                    </label>
                    <input
                      type="number"
                      step="50"
                      value={formData.budget_amount}
                      onChange={(e) => setFormData({ ...formData, budget_amount: parseFloat(e.target.value) || 0 })}
                      placeholder="e.g. 1500"
                      className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 font-medium"
                    />
                  </div>
                </div>

                {/* Pace */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Itinerary Pace
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { id: 'relaxed', label: 'Relaxed', desc: 'Fewer stops' },
                      { id: 'balanced', label: 'Balanced', desc: 'Standard' },
                      { id: 'fast_paced', label: 'Fast-Paced', desc: 'See it all' },
                    ].map((p) => (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => setFormData({ ...formData, pace: p.id })}
                        className={`py-2 px-2 text-center rounded-xl border text-xs font-semibold transition ${
                          formData.pace === p.id
                            ? 'bg-brand-50 border-brand-500 text-brand-700 ring-1 ring-brand-500'
                            : 'border-slate-200 hover:border-slate-300 text-slate-600'
                        }`}
                      >
                        <div>{p.label}</div>
                        <div className="text-[10px] text-slate-400 font-normal">{p.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Interests */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Interests (Select multiple)
                  </label>
                  <div className="flex flex-wrap gap-1.5">
                    {AVAILABLE_INTERESTS.map((interest) => {
                      const selected = formData.interests.includes(interest);
                      return (
                        <button
                          key={interest}
                          type="button"
                          onClick={() => {
                            if (selected) {
                              setFormData({
                                ...formData,
                                interests: formData.interests.filter((i) => i !== interest),
                              });
                            } else {
                              setFormData({
                                ...formData,
                                interests: [...formData.interests, interest],
                              });
                            }
                          }}
                          className={`text-xs px-2.5 py-1 rounded-lg border font-medium transition ${
                            selected
                              ? 'bg-teal-600 border-teal-600 text-white shadow-sm'
                              : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                          }`}
                        >
                          {interest}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Special Notes */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Special Notes / Constraints
                  </label>
                  <textarea
                    rows="2"
                    value={formData.special_notes}
                    onChange={(e) => setFormData({ ...formData, special_notes: e.target.value })}
                    placeholder="e.g. Vegetarian dining, anniversary celebration, avoid steep hills..."
                    className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={isGenerating}
                  className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-teal-500 hover:from-brand-700 hover:to-teal-600 text-white font-bold text-sm shadow-md shadow-brand-500/25 transition disabled:opacity-50 flex items-center justify-center space-x-2"
                >
                  {isGenerating ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span>Generating AI Itinerary...</span>
                    </>
                  ) : (
                    <span>🚀 Generate Personalized Itinerary</span>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* RIGHT COLUMN: ITINERARY DASHBOARD & VIEWER */}
          <div className="lg:col-span-7 space-y-6">
            {!activeTrip ? (
              <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-12 text-center">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center text-3xl mb-4">
                  🗺️
                </div>
                <h3 className="text-xl font-bold text-slate-800">No Itinerary Loaded Yet</h3>
                <p className="text-slate-500 text-sm max-w-md mx-auto mt-2">
                  Fill in the Trip Builder on the left or click one of the quick scenario presets above to generate a complete day-by-day travel plan.
                </p>
                <div className="mt-6 flex justify-center gap-3">
                  <button
                    onClick={() => handleApplyScenario('scenario-1-solo-weekend')}
                    className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700"
                  >
                    Load Solo Paris
                  </button>
                  <button
                    onClick={() => handleApplyScenario('scenario-2-couple-vacation')}
                    className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700"
                  >
                    Load Romantic Amalfi
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {/* TRIP HEADER CARD */}
                <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                  <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 pb-4">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-brand-50 text-brand-700 border border-brand-200">
                          {activeTrip.travel_style.toUpperCase()} • {activeTrip.duration_days} DAYS
                        </span>
                        <span className="text-xs text-slate-400">
                          {activeTrip.start_date} to {activeTrip.end_date}
                        </span>
                      </div>
                      <h2 className="text-2xl font-extrabold text-slate-900 mt-1">
                        {activeTrip.title}
                      </h2>
                      <p className="text-sm text-slate-600 mt-1">{activeTrip.overview}</p>
                    </div>

                    <div className="flex items-center space-x-2 no-print">
                      <button
                        onClick={() => window.print()}
                        className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg border border-slate-200 text-xs font-medium flex items-center space-x-1"
                        title="Print or Export as PDF"
                      >
                        <span>🖨️ Print / PDF</span>
                      </button>
                      <button
                        onClick={() => {
                          const shareUrl = `${window.location.origin}/api/trips/share/${activeTrip.share_token}`;
                          navigator.clipboard.writeText(shareUrl);
                          alert('Public Share Link copied to clipboard:\n' + shareUrl);
                        }}
                        className="p-2 text-brand-700 bg-brand-50 hover:bg-brand-100 rounded-lg border border-brand-200 text-xs font-medium flex items-center space-x-1"
                        title="Copy Share Link"
                      >
                        <span>🔗 Share</span>
                      </button>
                    </div>
                  </div>

                  {/* BUDGET ANALYTICS SUMMARY BAR */}
                  <div className="pt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                      <div className="text-[11px] font-bold text-slate-500 uppercase">Est. Total Cost</div>
                      <div className="text-lg font-extrabold text-slate-900">
                        ${activeTrip.budget_breakdown.total_estimated_cost}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        Target: ${activeTrip.budget_breakdown.user_budget || 'Flexible'}
                      </div>
                    </div>

                    <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                      <div className="text-[11px] font-bold text-slate-500 uppercase">Accommodations</div>
                      <div className="text-lg font-extrabold text-purple-700">
                        ${activeTrip.budget_breakdown.accommodations}
                      </div>
                      <div className="text-[10px] text-slate-400">{activeTrip.duration_days - 1} nights est.</div>
                    </div>

                    <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                      <div className="text-[11px] font-bold text-slate-500 uppercase">Dining & Food</div>
                      <div className="text-lg font-extrabold text-amber-700">
                        ${activeTrip.budget_breakdown.dining}
                      </div>
                      <div className="text-[10px] text-slate-400">Curated cafes & dinners</div>
                    </div>

                    <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                      <div className="text-[11px] font-bold text-slate-500 uppercase">Budget Status</div>
                      <div className="mt-1">
                        <span
                          className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                            activeTrip.budget_breakdown.status === 'within_budget'
                              ? 'bg-emerald-100 text-emerald-800'
                              : activeTrip.budget_breakdown.status === 'slightly_over'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-rose-100 text-rose-800'
                          }`}
                        >
                          {activeTrip.budget_breakdown.status.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* DAY SELECTOR TABS */}
                <div className="flex items-center space-x-2 overflow-x-auto pb-1 no-print">
                  {activeTrip.days.map((day) => (
                    <button
                      key={day.day_number}
                      onClick={() => setSelectedDay(day.day_number)}
                      className={`px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition flex items-center space-x-1.5 ${
                        selectedDay === day.day_number
                          ? 'bg-slate-900 text-white shadow-sm'
                          : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
                      }`}
                    >
                      <span>Day {day.day_number}</span>
                      <span className="text-[10px] opacity-75">(${day.estimated_daily_cost})</span>
                    </button>
                  ))}
                  <button
                    onClick={() => setSelectedDay(0)} // 0 means show all
                    className={`px-3 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition ${
                      selectedDay === 0
                        ? 'bg-slate-900 text-white'
                        : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    View All Days
                  </button>
                </div>

                {/* ACTIVE DAY ITINERARY DETAILS */}
                {activeTrip.days
                  .filter((d) => selectedDay === 0 || d.day_number === selectedDay)
                  .map((day) => (
                    <div key={day.day_number} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-5">
                      {/* Day Header */}
                      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs font-extrabold text-brand-600 uppercase tracking-wider">
                              Day {day.day_number} • {day.date}
                            </span>
                            <span className="text-xs text-slate-400">| Est. ${day.estimated_daily_cost}</span>
                          </div>
                          <h3 className="text-lg font-bold text-slate-900 mt-0.5">{day.theme}</h3>
                          <p className="text-xs text-slate-500 mt-0.5">{day.summary}</p>
                        </div>

                        {/* Day Actions */}
                        <div className="flex items-center space-x-2 no-print">
                          <button
                            onClick={() =>
                              setRegenDayModal({
                                isOpen: true,
                                dayNum: day.day_number,
                                prompt: '',
                              })
                            }
                            className="px-3 py-1.5 text-xs font-bold rounded-lg bg-teal-50 text-teal-700 border border-teal-200 hover:bg-teal-100 transition flex items-center space-x-1"
                          >
                            <span>⚡ Regenerate Day</span>
                          </button>

                          <button
                            onClick={() => setAddActivityModal({ isOpen: true, dayNum: day.day_number })}
                            className="px-3 py-1.5 text-xs font-bold rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition"
                          >
                            + Add Stop
                          </button>
                        </div>
                      </div>

                      {/* Activities Timeline */}
                      <div className="space-y-4">
                        {day.activities.map((activity, index) => {
                          const style = CATEGORY_STYLES[activity.category.toLowerCase()] || CATEGORY_STYLES.attraction;
                          return (
                            <div
                              key={activity.id}
                              className={`p-4 rounded-xl border transition ${
                                activity.is_completed
                                  ? 'bg-slate-50 border-slate-200 opacity-60'
                                  : 'bg-white border-slate-200 hover:border-slate-300 hover:shadow-xs'
                              }`}
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div className="flex items-start space-x-3">
                                  {/* Completion checkbox */}
                                  <input
                                    type="checkbox"
                                    checked={activity.is_completed || false}
                                    onChange={() => handleToggleCompleted(day.day_number, activity.id)}
                                    className="mt-1 h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 cursor-pointer no-print"
                                  />

                                  <div>
                                    <div className="flex flex-wrap items-center gap-2">
                                      <span
                                        className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${style.bg}`}
                                      >
                                        {style.label}
                                      </span>
                                      <span className="text-xs font-semibold text-slate-500">
                                        {activity.start_time} - {activity.end_time}
                                      </span>
                                      <span className="text-xs font-bold text-slate-800">
                                        ${activity.cost_estimate}
                                      </span>
                                    </div>

                                    <h4
                                      className={`text-base font-bold text-slate-900 mt-1 ${
                                        activity.is_completed ? 'line-through text-slate-400' : ''
                                      }`}
                                    >
                                      {activity.title}
                                    </h4>

                                    <p className="text-xs text-slate-600 mt-1">{activity.description}</p>

                                    <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-slate-500">
                                      <span className="flex items-center">
                                        📍 <span className="ml-1 font-medium">{activity.location}</span>
                                      </span>
                                      {activity.transit_info && (
                                        <span className="flex items-center text-teal-700 bg-teal-50 px-2 py-0.5 rounded-md border border-teal-100">
                                          🚶 <span className="ml-1">{activity.transit_info}</span>
                                        </span>
                                      )}
                                      {activity.booking_tips && (
                                        <span className="flex items-center text-amber-700 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-100">
                                          💡 <span className="ml-1">{activity.booking_tips}</span>
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                </div>

                                {/* Activity Delete Button */}
                                <div className="no-print">
                                  <button
                                    onClick={() => handleDeleteActivity(activity.id)}
                                    className="text-slate-400 hover:text-rose-500 text-xs p-1"
                                    title="Remove activity"
                                  >
                                    ✕
                                  </button>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}

                {/* INTERACTIVE ROUTE MAP COMPONENT */}
                <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm no-print">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h3 className="font-bold text-slate-900 text-base">Interactive Route Map</h3>
                      <p className="text-xs text-slate-500">
                        Day stops and optimized transit path for {activeTrip.destination}
                      </p>
                    </div>
                    <span className="text-xs font-semibold px-2 py-1 bg-slate-100 rounded-md text-slate-600">
                      OpenStreetMap
                    </span>
                  </div>
                  <MapView trip={activeTrip} selectedDay={selectedDay} />
                </div>

                {/* PACKING & LOCAL INSIGHTS */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
                    <h4 className="text-sm font-bold text-slate-900 flex items-center mb-2">
                      🎒 Packing Essentials
                    </h4>
                    <ul className="text-xs text-slate-600 space-y-1.5 list-disc list-inside">
                      {activeTrip.packing_essentials.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
                    <h4 className="text-sm font-bold text-slate-900 flex items-center mb-2">
                      💡 Local Logistics & Insights
                    </h4>
                    <ul className="text-xs text-slate-600 space-y-1.5 list-disc list-inside">
                      {activeTrip.local_insights.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* REGENERATE DAY MODAL */}
      {regenDayModal.isOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100">
            <h3 className="text-lg font-bold text-slate-900 mb-1">
              Regenerate Day {regenDayModal.dayNum}
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Tell the AI what you'd like to adjust for this specific day (e.g. more romantic dining, relaxed pace, indoor rainy day alternatives).
            </p>

            <textarea
              rows="3"
              value={regenDayModal.prompt}
              onChange={(e) => setRegenDayModal({ ...regenDayModal, prompt: e.target.value })}
              placeholder="e.g. Replace museums with scenic coastal walks and fine seafood dining..."
              className="w-full p-3 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 mb-4"
            />

            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setRegenDayModal({ isOpen: false, dayNum: 1, prompt: '' })}
                className="px-4 py-2 text-xs font-semibold rounded-lg text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                onClick={handleRegenerateDay}
                className="px-4 py-2 text-xs font-bold rounded-lg bg-brand-600 hover:bg-brand-700 text-white shadow-sm"
              >
                Apply AI Regeneration
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ADD STOP MODAL */}
      {addActivityModal.isOpen && (
        <AddStopModal
          dayNum={addActivityModal.dayNum}
          tripId={activeTrip.id}
          onClose={() => setAddActivityModal({ isOpen: false, dayNum: 1 })}
          onSuccess={(updated) => {
            setActiveTrip(updated);
            setAddActivityModal({ isOpen: false, dayNum: 1 });
          }}
        />
      )}

      {/* SAVED TRIPS MODAL */}
      {isSavedModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-xl border border-slate-100 max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between border-b pb-3 mb-4">
              <h3 className="text-lg font-bold text-slate-900">Saved Itineraries</h3>
              <button
                onClick={() => setIsSavedModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3">
              {savedTrips.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-6">No saved trips found yet.</p>
              ) : (
                savedTrips.map((trip) => (
                  <div
                    key={trip.id}
                    className="p-3.5 rounded-xl border border-slate-200 hover:border-brand-500 transition flex items-center justify-between"
                  >
                    <div>
                      <h4 className="font-bold text-slate-800 text-sm">{trip.title}</h4>
                      <p className="text-xs text-slate-500">
                        {trip.destination} • {trip.duration_days} Days • Est. ${trip.budget_breakdown.total_estimated_cost}
                      </p>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => {
                          setActiveTrip(trip);
                          setSelectedDay(1);
                          setIsSavedModalOpen(false);
                        }}
                        className="px-3 py-1.5 text-xs font-bold rounded-lg bg-brand-50 text-brand-700 hover:bg-brand-100"
                      >
                        Open
                      </button>
                      <button
                        onClick={async () => {
                          if (confirm('Delete this trip?')) {
                            await fetch(`/api/trips/${trip.id}`, { method: 'DELETE' });
                            fetchSavedTrips();
                            if (activeTrip && activeTrip.id === trip.id) {
                              setActiveTrip(null);
                            }
                          }
                        }}
                        className="p-1.5 text-xs text-slate-400 hover:text-rose-600"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* AI TRAVEL COPILOT DRAWER */}
      {isCopilotOpen && (
        <div className="fixed bottom-4 right-4 w-96 max-w-[calc(100vw-2rem)] bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col h-[520px] z-50 overflow-hidden">
          {/* Copilot Header */}
          <div className="bg-slate-900 text-white p-4 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <h3 className="font-bold text-sm">AI Travel Copilot</h3>
            </div>
            <button
              onClick={() => setIsCopilotOpen(false)}
              className="text-slate-400 hover:text-white text-sm"
            >
              ✕
            </button>
          </div>

          {/* Copilot Message Feed */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-slate-50 text-xs">
            {copilotMessages.map((msg, i) => (
              <div
                key={i}
                className={`p-3 rounded-xl max-w-[85%] ${
                  msg.sender === 'user'
                    ? 'ml-auto bg-brand-600 text-white'
                    : 'bg-white border border-slate-200 text-slate-800 shadow-2xs'
                }`}
              >
                <p>{msg.text}</p>
                {msg.actions && (
                  <div className="mt-2 pt-2 border-t border-slate-100 flex flex-wrap gap-1">
                    {msg.actions.map((act, j) => (
                      <span
                        key={j}
                        onClick={() => setCopilotInput(`Tell me more about: ${act}`)}
                        className="text-[10px] bg-slate-100 hover:bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded cursor-pointer"
                      >
                        {act}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {isCopilotLoading && (
              <div className="p-3 bg-white border rounded-xl text-slate-400 italic">
                Copilot is thinking...
              </div>
            )}
          </div>

          {/* Quick Prompts */}
          <div className="p-2 border-t border-slate-100 bg-white flex overflow-x-auto gap-1 text-[11px]">
            {['Packing list?', 'Local transit tips?', 'Emergency numbers?', 'Tipping etiquette?'].map((q) => (
              <button
                key={q}
                onClick={() => setCopilotInput(q)}
                className="whitespace-nowrap px-2 py-0.5 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-600"
              >
                {q}
              </button>
            ))}
          </div>

          {/* Copilot Input */}
          <form onSubmit={handleSendCopilot} className="p-3 bg-white border-t border-slate-200 flex space-x-2">
            <input
              type="text"
              value={copilotInput}
              onChange={(e) => setCopilotInput(e.target.value)}
              placeholder="Ask a trip question..."
              className="flex-1 px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            <button
              type="submit"
              className="px-3.5 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold"
            >
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

// -------------------------------------------------------------
// ADD STOP MODAL COMPONENT
// -------------------------------------------------------------
function AddStopModal({ dayNum, tripId, onClose, onSuccess }) {
  const [form, setForm] = useState({
    title: '',
    category: 'attraction',
    time_slot: 'morning',
    start_time: '10:00 AM',
    end_time: '11:30 AM',
    description: '',
    location: '',
    cost_estimate: 20,
    transit_info: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await fetch(`/api/trips/${tripId}/days/${dayNum}/activities`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error('Failed to add activity');
      const updated = await res.json();
      onSuccess(updated);
    } catch (err) {
      alert(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100">
        <h3 className="text-lg font-bold text-slate-900 mb-4">Add Stop to Day {dayNum}</h3>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Title</label>
            <input
              type="text"
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="e.g. Montmartre Art Walk"
              className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Category</label>
              <select
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300"
              >
                <option value="attraction">Attraction</option>
                <option value="dining">Dining</option>
                <option value="accommodation">Accommodation</option>
                <option value="transit">Transit</option>
                <option value="leisure">Leisure</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Est. Cost ($)</label>
              <input
                type="number"
                value={form.cost_estimate}
                onChange={(e) => setForm({ ...form, cost_estimate: parseFloat(e.target.value) || 0 })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Location / Address</label>
            <input
              type="text"
              value={form.location}
              onChange={(e) => setForm({ ...form, location: e.target.value })}
              placeholder="e.g. Place du Tertre"
              className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Description</label>
            <textarea
              rows="2"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300"
            />
          </div>

          <div className="flex justify-end space-x-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold rounded-lg text-slate-600 hover:bg-slate-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 text-xs font-bold rounded-lg bg-brand-600 hover:bg-brand-700 text-white"
            >
              Save Activity
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// -------------------------------------------------------------
// LEAFLET MAP VIEW COMPONENT
// -------------------------------------------------------------
function MapView({ trip, selectedDay }) {
  const mapRef = useRef(null);
  const leafletMapInstance = useRef(null);

  useEffect(() => {
    if (!mapRef.current || !window.L || !trip) return;

    // Collect activities to display
    const daysToMap = selectedDay === 0 ? trip.days : trip.days.filter((d) => d.day_number === selectedDay);
    const points = [];

    daysToMap.forEach((day) => {
      day.activities.forEach((act) => {
        if (act.lat && act.lng) {
          points.push({
            lat: act.lat,
            lng: act.lng,
            title: act.title,
            category: act.category,
            cost: act.cost_estimate,
          });
        }
      });
    });

    if (points.length === 0) return;

    // Destroy existing instance if any
    if (leafletMapInstance.current) {
      leafletMapInstance.current.remove();
      leafletMapInstance.current = null;
    }

    const firstPt = points[0];
    const map = window.L.map(mapRef.current).setView([firstPt.lat, firstPt.lng], 13);
    leafletMapInstance.current = map;

    window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map);

    const latlngs = [];
    points.forEach((pt, idx) => {
      latlngs.push([pt.lat, pt.lng]);
      const marker = window.L.marker([pt.lat, pt.lng]).addTo(map);
      marker.bindPopup(`
        <div style="font-family: sans-serif; font-size: 12px;">
          <strong>#${idx + 1} ${pt.title}</strong><br/>
          <span style="color: #64748b;">${pt.category} • $${pt.cost}</span>
        </div>
      `);
    });

    // Draw route polyline
    if (latlngs.length > 1) {
      window.L.polyline(latlngs, { color: '#0d9488', weight: 4, dashArray: '6, 8' }).addTo(map);
      map.fitBounds(window.L.latLngBounds(latlngs), { padding: [30, 30] });
    }

    return () => {
      if (leafletMapInstance.current) {
        leafletMapInstance.current.remove();
        leafletMapInstance.current = null;
      }
    };
  }, [trip, selectedDay]);

  return <div ref={mapRef} className="map-container border border-slate-200"></div>;
}

// Mount React Root
const rootElement = document.getElementById('root');
const root = ReactDOM.createRoot(rootElement);
root.render(<App />);
