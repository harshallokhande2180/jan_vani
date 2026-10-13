/**
 * Jan-Vani Main Application Logic
 * Integrates Voice Perception, Geolocation, Backend API, Offline Buffering,
 * Audio Synthesis and Officer Console.
 */

let currentLang = "mr"; // Default Marathi
let recordedAudioBlob = null;
let recordingSeconds = 0;
let recordingTimerInterval = null;
let currentRole = "commissioner"; // commissioner, ward_2, ward_4
let activeWardFilter = "ALL";
let allTicketsCache = [];
let mapInstance = null;
let mapMarkers = [];

// Vernacular UI string dictionary
const I18N = {
  mr: {
    heroTitle: "जन-वाणी",
    heroSub: "स्थानिक भाषेत बोला, नागरिक समस्या सोडवा",
    micPrompt: "येथे स्पर्श करा आणि तुमची समस्या सांगा",
    micRecording: "आम्ही ऐकत आहोत... बोलणे संपल्यावर पुन्हा स्पर्श करा",
    audioPromptText: "नमस्कार! फक्त मायक्रोफोन बटण दाबा आणि तुमच्या भाषेत तक्रार सांगा.",
    instantAck: "तक्रार प्राप्त झाली! विश्लेषण सुरू आहे...",
    consentText: "मी माझा आवाज आणि स्थान महापालिकेस पाठवण्यास संमती देतो/देते (DPDP कायदा २०२३).",
    waterLeak: "पाणी गळती (मराठी)",
    pothole: "रस्त्यावरील खड्डा (मराठी)",
    drainage: "ड्रेनेज तुंबले (मराठी)",
    powerCut: "वीज पुरवठा खंडित (मराठी)",
    listenStatus: "आवाज ऐका"
  },
  hi: {
    heroTitle: "जन-वाणी",
    heroSub: "अपनी भाषा में बोलें, नागरिक समस्याओं का समाधान पाएं",
    micPrompt: "यहाँ दबाएं और अपनी समस्या बोलें",
    micRecording: "हम सुन रहे हैं... बोलना समाप्त होने पर दोबारा दबाएं",
    audioPromptText: "नमस्ते! बस माइक बटन दबाएं और अपनी भाषा में शिकायत बताएं।",
    instantAck: "शिकायत प्राप्त हुई! विश्लेषण जारी है...",
    consentText: "मैं अपनी आवाज और स्थान नगर निगम को भेजने की सहमति देता/देती हूँ (DPDP एक्ट 2023)।",
    waterLeak: "पानी की आपूर्ति (हिंदी)",
    pothole: "सड़क पर गड्ढा (हिंदी)",
    drainage: "नाली जाम (हिंदी)",
    powerCut: "बिजली गुल (हिंदी)",
    listenStatus: "स्थिति सुनें"
  },
  en: {
    heroTitle: "Jan-Vani",
    heroSub: "Speak in your dialect, get civic issues resolved",
    micPrompt: "Tap here and speak your problem",
    micRecording: "Listening... Tap again when finished",
    audioPromptText: "Welcome! Simply tap the microphone button and report your problem.",
    instantAck: "Complaint Received! Processing...",
    consentText: "I consent to share voice and GPS location with Municipal Corporation (DPDP Act 2023).",
    waterLeak: "Water Leakage",
    pothole: "Road Pothole",
    drainage: "Drain Blockage",
    powerCut: "Power Outage",
    listenStatus: "Listen Voice"
  }
};

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  setupNavigation();
  setupLanguageToggles();
  setupMicrophone();
  setupPresets();
  setupOfficerConsole();
  loadTicketsAndKPIs();

  // Check offline buffered count
  if (window.offlineBuffer) {
    window.offlineBuffer.getAll().then(items => {
      if (items.length > 0) {
        showToast(`IndexedDB: ${items.length} तक्रारी ऑफलाइन साठवलेल्या आहेत.`);
      }
    });
  }
});

function initTheme() {
  const saved = localStorage.getItem("jv_theme") || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  document.documentElement.setAttribute("data-theme", saved);
  const btn = document.getElementById("themeToggleBtn");
  if (btn) btn.innerHTML = saved === "dark" ? "☀️" : "🌙";
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("jv_theme", next);
  const btn = document.getElementById("themeToggleBtn");
  if (btn) btn.innerHTML = next === "dark" ? "☀️" : "🌙";
}

function setupNavigation() {
  const tabs = document.querySelectorAll(".nav-tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      const targetId = tab.getAttribute("data-target");
      document.querySelectorAll(".tab-pane").forEach(pane => pane.classList.remove("active"));
      const activePane = document.getElementById(targetId);
      if (activePane) activePane.classList.add("active");

      if (targetId === "pane-officer" && !mapInstance) {
        setTimeout(initNagpurMap, 200);
      }
    });
  });
}

function setupLanguageToggles() {
  const langBtns = document.querySelectorAll(".lang-btn");
  langBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      langBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentLang = btn.getAttribute("data-lang");
      window.janVaniRecorder.setLanguage(currentLang);
      updateUILanguage();
    });
  });
}

function updateUILanguage() {
  const dict = I18N[currentLang] || I18N.mr;
  document.getElementById("heroTitle").textContent = dict.heroTitle;
  document.getElementById("heroSub").textContent = dict.heroSub;
  if (!window.janVaniRecorder.isRecording) {
    document.getElementById("micPromptText").textContent = dict.micPrompt;
  }
  document.getElementById("consentLabelText").textContent = dict.consentText;
}

function playVoiceInstructions() {
  const dict = I18N[currentLang] || I18N.mr;
  window.janVaniRecorder.speakText(dict.audioPromptText, currentLang);
}

// -------------------------------------------------------------
// MICROPHONE RECORDING & SUBMISSION
// -------------------------------------------------------------
function setupMicrophone() {
  const micBtn = document.getElementById("giantMicBtn");
  const micWrapper = document.getElementById("micWrapper");
  const visualizer = document.getElementById("audioVisualizer");
  const promptText = document.getElementById("micPromptText");
  const subprompt = document.getElementById("micSubprompt");

  window.onSpeechTranscriptUpdate = (text) => {
    if (text) {
      subprompt.innerHTML = `<span>🗣️ "${text.slice(-50)}"</span>`;
    }
  };

  micBtn.addEventListener("click", async () => {
    const consent = document.getElementById("consentCheckbox").checked;
    if (!consent) {
      alert("कृपया रेकॉर्डिंग सुरू करण्यापूर्वी संमती द्या (Please check the DPDP consent box).");
      return;
    }

    if (!window.janVaniRecorder.isRecording) {
      // START RECORDING
      const started = await window.janVaniRecorder.startRecording();
      if (started) {
        micWrapper.classList.add("recording");
        micBtn.classList.add("recording");
        visualizer.classList.add("active");
        promptText.textContent = I18N[currentLang].micRecording;
        recordingSeconds = 0;
        recordingTimerInterval = setInterval(() => {
          recordingSeconds++;
          subprompt.textContent = `⏱️ 00:0${recordingSeconds}s (रेकॉर्डिंग सुरू)`;
        }, 1000);
      }
    } else {
      // STOP RECORDING & SUBMIT
      clearInterval(recordingTimerInterval);
      micWrapper.classList.remove("recording");
      micBtn.classList.remove("recording");
      visualizer.classList.remove("active");
      promptText.textContent = I18N[currentLang].instantAck;
      subprompt.textContent = "प्रक्रिया सुरू आहे...";

      const res = await window.janVaniRecorder.stopRecording();
      const transcript = res.transcript;

      // Submit
      submitVoiceComplaint({
        raw_text: transcript || "आमच्या गल्लीत पिण्याच्या पाण्याची मुख्य पाइपलाइन फुटली आहे, तीन दिवसांपासून पाणी वाहत आहे.",
        language: currentLang
      });
    }
  });
}

async function submitVoiceComplaint(payload) {
  const coords = window.janVaniRecorder.coords;
  const userSeverity = document.getElementById("severitySelector")?.value || "Medium";

  const requestBody = {
    raw_text: payload.raw_text,
    sample_id: payload.sample_id,
    language: payload.language || currentLang,
    latitude: coords.latitude,
    longitude: coords.longitude,
    user_severity_pick: userSeverity
  };

  // Instant acknowledgement banner
  showInstantAckNotification();

  // If offline, buffer in IndexedDB
  if (!navigator.onLine) {
    if (window.offlineBuffer) {
      await window.offlineBuffer.saveComplaint(requestBody);
      showToast("इंटरनेट नाही! तक्रार स्थानिकरित्या सेव्ह केली गेली. ऑनलाइन येताच पाठवली जाईल.");
    }
    return;
  }

  try {
    const res = await fetch("/api/submit-complaint", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody)
    });
    const data = await res.json();
    if (data.success) {
      displayConfirmation(data);
      loadTicketsAndKPIs();
    } else {
      alert("Error submitting complaint");
    }
  } catch (err) {
    console.error("Submission failed, buffering locally:", err);
    if (window.offlineBuffer) {
      await window.offlineBuffer.saveComplaint(requestBody);
      showToast("सर्व्हर संपर्क नाही. तक्रार IndexedDB मध्ये सुरक्षित सेव्ह केली.");
    }
  }
}

function showInstantAckNotification() {
  const el = document.getElementById("instantAckBanner");
  if (el) {
    el.style.display = "flex";
    setTimeout(() => { el.style.display = "none"; }, 3500);
  }
}

function displayConfirmation(data) {
  const card = document.getElementById("confirmationCard");
  const ticket = data.ticket;
  const tts = data.tts_confirmation;

  document.getElementById("confTicketId").textContent = ticket.id;
  document.getElementById("confWard").textContent = `${ticket.ward_name} (${ticket.ward_id})`;
  document.getElementById("confCategory").textContent = `${ticket.category} - ${ticket.sub_category}`;
  document.getElementById("confUrgency").textContent = ticket.urgency;
  document.getElementById("confSummary").textContent = ticket.summary_en;

  const mergeBanner = document.getElementById("confMergeAlert");
  if (data.is_merged) {
    mergeBanner.style.display = "flex";
    document.getElementById("mergeCountText").textContent =
      `जवळपासच्या ${ticket.duplicate_count} नागरिकांनी हीच समस्या नोंदवली आहे. प्राधान्य स्वयंचलितरित्या वाढवले गेले! (Merged duplicate)`;
  } else {
    mergeBanner.style.display = "none";
  }

  card.classList.add("active");
  card.scrollIntoView({ behavior: "smooth" });

  // Play spoken feedback immediately (Voice First principle)
  if (tts && tts.spoken_text) {
    window.janVaniRecorder.speakText(tts.spoken_text, data.ticket.language);
  }

  const playBtn = document.getElementById("btnPlayConfirmationVoice");
  if (playBtn) {
    playBtn.onclick = () => {
      window.janVaniRecorder.speakText(tts.spoken_text, data.ticket.language);
    };
  }
}

// -------------------------------------------------------------
// PRESET DEMONSTRATIONS (One-Click Scenarios)
// -------------------------------------------------------------
function setupPresets() {
  const presetCards = document.querySelectorAll(".preset-card");
  presetCards.forEach(card => {
    card.addEventListener("click", () => {
      const sampleId = card.getAttribute("data-sample-id");
      const lang = card.getAttribute("data-lang");
      currentLang = lang;
      window.janVaniRecorder.setLanguage(lang);

      // Play audio preview then submit
      const sampleText = card.querySelector(".preset-quote").textContent;
      window.janVaniRecorder.speakText(sampleText, lang);

      setTimeout(() => {
        submitVoiceComplaint({
          sample_id: sampleId,
          language: lang
        });
      }, 600);
    });
  });
}

// -------------------------------------------------------------
// OFFICER CONSOLE & MAP
// -------------------------------------------------------------
function setupOfficerConsole() {
  const roleSelect = document.getElementById("officerRoleSelect");
  if (roleSelect) {
    roleSelect.addEventListener("change", (e) => {
      currentRole = e.target.value;
      if (currentRole === "ward_2") {
        activeWardFilter = "WARD-02";
      } else if (currentRole === "ward_4") {
        activeWardFilter = "WARD-04";
      } else {
        activeWardFilter = "ALL";
      }
      renderTicketsTable();
      updateKPIsView();
    });
  }

  const searchInput = document.getElementById("ticketSearchInput");
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      renderTicketsTable();
    });
  }
}

async function loadTicketsAndKPIs() {
  try {
    const res = await fetch("/api/tickets");
    allTicketsCache = await res.json();
    renderTicketsTable();
    renderCitizenTrackingList();
    updateKPIsView();
    if (mapInstance) updateMapMarkers();
  } catch (err) {
    console.error("Error fetching tickets:", err);
  }
}

function updateKPIsView() {
  const filtered = activeWardFilter === "ALL" 
    ? allTicketsCache 
    : allTicketsCache.filter(t => t.ward_id === activeWardFilter);

  const total = filtered.length;
  const openCount = filtered.filter(t => t.status === "Open").length;
  const inProg = filtered.filter(t => t.status === "In Progress").length;
  const resolved = filtered.filter(t => t.status === "Resolved").length;
  const merged = filtered.reduce((acc, t) => acc + (t.duplicate_count - 1), 0);

  setKPI("kpiTotal", total);
  setKPI("kpiOpen", openCount);
  setKPI("kpiInProgress", inProg);
  setKPI("kpiResolved", resolved);
  setKPI("kpiMerged", merged);
}

function setKPI(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function renderTicketsTable() {
  const tbody = document.getElementById("ticketsTableBody");
  if (!tbody) return;

  const search = (document.getElementById("ticketSearchInput")?.value || "").toLowerCase();
  const filtered = allTicketsCache.filter(t => {
    if (activeWardFilter !== "ALL" && t.ward_id !== activeWardFilter) return false;
    if (search) {
      return (
        t.id.toLowerCase().includes(search) ||
        t.category.toLowerCase().includes(search) ||
        t.ward_name.toLowerCase().includes(search) ||
        t.transcript.toLowerCase().includes(search)
      );
    }
    return true;
  });

  tbody.innerHTML = "";
  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 20px;">कोणत्याही तक्रारी सापडल्या नाहीत.</td></tr>`;
    return;
  }

  filtered.forEach(t => {
    const tr = document.createElement("tr");
    const urgencyClass = t.urgency === "High" ? "badge-high" : (t.urgency === "Medium" ? "badge-med" : "badge-low");
    const statusClass = t.status === "Open" ? "badge-open" : (t.status === "In Progress" ? "badge-inprog" : "badge-resolved");

    tr.innerHTML = `
      <td><strong>${t.id}</strong></td>
      <td>${t.ward_name} <br><small style="color:var(--text-muted)">${t.ward_id}</small></td>
      <td>
        <strong>${t.category}</strong><br>
        <small style="color:var(--text-muted)">${t.sub_category}</small>
      </td>
      <td>
        <span class="badge ${urgencyClass}">
          ${t.urgency === "High" ? "🔴" : (t.urgency === "Medium" ? "🟠" : "🟢")} ${t.urgency}
        </span>
        ${t.duplicate_count > 1 ? `<span class="badge" style="background:#fef3c7;color:#92400e;margin-top:4px;display:block;">⚡ ${t.duplicate_count} एकत्र (Merged)</span>` : ''}
      </td>
      <td><span class="badge ${statusClass}">${t.status}</span></td>
      <td>
        <button class="btn-icon" title="आवाज ऐका (Speak)" onclick="playTicketSpoken('${t.id}')">🔊</button>
      </td>
      <td>
        <select onchange="updateTicketStatus('${t.id}', this.value)" style="padding:6px;border-radius:6px;border:1px solid var(--border-color);background:var(--bg-surface);color:var(--text-primary);cursor:pointer;">
          <option value="Open" ${t.status === 'Open' ? 'selected' : ''}>Open</option>
          <option value="In Progress" ${t.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
          <option value="Resolved" ${t.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
        </select>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderCitizenTrackingList() {
  const container = document.getElementById("citizenTicketsList");
  if (!container) return;

  container.innerHTML = "";
  allTicketsCache.slice(0, 5).forEach(t => {
    const card = document.createElement("div");
    card.className = "preset-card";
    card.innerHTML = `
      <div class="preset-card-header">
        <span style="font-weight:700;font-size:0.95rem;">${t.id} - ${t.ward_name}</span>
        <span class="badge ${t.status === 'Open' ? 'badge-open' : (t.status === 'In Progress' ? 'badge-inprog' : 'badge-resolved')}">${t.status}</span>
      </div>
      <p style="font-size:0.95rem;color:var(--text-primary);margin:4px 0;">"${t.transcript}"</p>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;">
        <small style="color:var(--text-muted)">${t.category} | ${t.duplicate_count > 1 ? `👥 ${t.duplicate_count} नागरिकांनी नोंदवले` : '१ नागरिक'}</small>
        <button class="btn-play-voice" style="padding:6px 12px;font-size:0.82rem;" onclick="playTicketSpoken('${t.id}')">
          🔊 ${I18N[currentLang].listenStatus}
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

window.playTicketSpoken = function(ticketId) {
  const t = allTicketsCache.find(x => x.id === ticketId);
  if (!t) return;
  const msg = t.language === "mr"
    ? `तिकीट क्रमांक ${t.id}. ${t.category} समस्या. सद्य स्थिती ${t.status} आहे. ${t.ward_name} प्रभाग अधिकारी काम पाहत आहेत.`
    : `टिकट संख्या ${t.id}. ${t.category} समस्या. वर्तमान स्थिति ${t.status} है। ${t.ward_name} वार्ड अधिकारी काम देख रहे हैं।`;
  window.janVaniRecorder.speakText(msg, t.language);
};

window.updateTicketStatus = async function(ticketId, newStatus) {
  try {
    const res = await fetch(`/api/tickets/${ticketId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus, note: `Status updated by ward officer to ${newStatus}` })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`तिकीट ${ticketId} स्थिती: ${newStatus}`);
      loadTicketsAndKPIs();
    }
  } catch (err) {
    console.error(err);
  }
};

// -------------------------------------------------------------
// NAGPUR LEAFLET MAP
// -------------------------------------------------------------
function initNagpurMap() {
  const mapDiv = document.getElementById("nagpurMapDiv");
  if (!mapDiv || typeof L === "undefined") return;

  // Center on Nagpur
  mapInstance = L.map("nagpurMapDiv").setView([21.1458, 79.0882], 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 18
  }).addTo(mapInstance);

  // Load ward polygons
  fetch("/api/wards")
    .then(r => r.json())
    .then(geo => {
      L.geoJSON(geo, {
        style: {
          color: "#0072B2",
          weight: 2,
          fillColor: "#56B4E9",
          fillOpacity: 0.15
        },
        onEachFeature: (feature, layer) => {
          const p = feature.properties;
          layer.bindPopup(`<strong>${p.ward_name} (${p.ward_id})</strong><br>Zone: ${p.zone}`);
        }
      }).addTo(mapInstance);
    });

  updateMapMarkers();
}

function updateMapMarkers() {
  if (!mapInstance || typeof L === "undefined") return;

  mapMarkers.forEach(m => mapInstance.removeLayer(m));
  mapMarkers = [];

  allTicketsCache.forEach(t => {
    const color = t.urgency === "High" ? "#D55E00" : (t.urgency === "Medium" ? "#E69F00" : "#009E73");
    const marker = L.circleMarker([t.latitude, t.longitude], {
      radius: t.duplicate_count > 1 ? 10 : 7,
      color: "#ffffff",
      weight: 2,
      fillColor: color,
      fillOpacity: 0.85
    });

    marker.bindPopup(`
      <strong>${t.id} - ${t.category}</strong><br>
      Ward: ${t.ward_name}<br>
      Urgency: ${t.urgency}<br>
      Status: ${t.status}<br>
      ${t.duplicate_count > 1 ? `<b>Merged Duplicates: ${t.duplicate_count}</b><br>` : ''}
      <em>"${t.transcript.slice(0, 60)}..."</em>
    `);

    marker.addTo(mapInstance);
    mapMarkers.push(marker);
  });
}

function showToast(msg) {
  const toast = document.createElement("div");
  toast.style.position = "fixed";
  toast.style.bottom = "24px";
  toast.style.right = "24px";
  toast.style.background = "#1f2937";
  toast.style.color = "#ffffff";
  toast.style.padding = "12px 20px";
  toast.style.borderRadius = "8px";
  toast.style.boxShadow = "0 4px 12px rgba(0,0,0,0.3)";
  toast.style.zIndex = "9999";
  toast.style.fontSize = "0.95rem";
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

window.exportTicketsCSV = function() {
  if (allTicketsCache.length === 0) return;
  const headers = ["ID", "Ward", "Category", "SubCategory", "Urgency", "Status", "Duplicates", "Created"];
  const rows = allTicketsCache.map(t => [
    t.id, t.ward_name, t.category, t.sub_category, t.urgency, t.status, t.duplicate_count, t.created_at
  ]);
  const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `jan_vani_tickets_${new Date().toISOString().slice(0,10)}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};
