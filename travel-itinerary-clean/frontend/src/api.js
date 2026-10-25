const API_BASE = '/api';

export const api = {
  // Trips
  generateTrip: async (payload) => {
    const res = await fetch(`${API_BASE}/trips/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Trip generation failed');
    return res.json();
  },

  listTrips: async () => {
    const res = await fetch(`${API_BASE}/trips`);
    if (!res.ok) throw new Error('Failed to load trips');
    return res.json();
  },

  getTrip: async (tripId) => {
    const res = await fetch(`${API_BASE}/trips/${tripId}`);
    if (!res.ok) throw new Error('Trip not found');
    return res.json();
  },

  deleteTrip: async (tripId) => {
    const res = await fetch(`${API_BASE}/trips/${tripId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete trip');
    return res.json();
  },

  regenerateDay: async (tripId, dayNumber, refinementPrompt) => {
    const res = await fetch(`${API_BASE}/trips/${tripId}/regenerate-day`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        day_number: dayNumber,
        refinement_prompt: refinementPrompt,
      }),
    });
    if (!res.ok) throw new Error('Day regeneration failed');
    return res.json();
  },

  addActivity: async (tripId, dayNumber, activityData) => {
    const res = await fetch(`${API_BASE}/trips/${tripId}/days/${dayNumber}/activities`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(activityData),
    });
    if (!res.ok) throw new Error('Failed to add activity');
    return res.json();
  },

  deleteActivity: async (tripId, activityId) => {
    const res = await fetch(`${API_BASE}/trips/${tripId}/activities/${activityId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete activity');
    return res.json();
  },

  // Scenarios
  listScenarios: async () => {
    const res = await fetch(`${API_BASE}/scenarios`);
    if (!res.ok) throw new Error('Failed to load scenarios');
    return res.json();
  },

  getScenario: async (scenarioId) => {
    const res = await fetch(`${API_BASE}/scenarios/${scenarioId}`);
    if (!res.ok) throw new Error('Failed to load scenario');
    return res.json();
  },

  // Copilot Chat
  askCopilot: async (destination, question) => {
    const res = await fetch(`${API_BASE}/trips/copilot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ destination, question }),
    });
    if (!res.ok) throw new Error('Copilot inquiry failed');
    return res.json();
  },
};
