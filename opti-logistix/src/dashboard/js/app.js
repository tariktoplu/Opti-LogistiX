/**
 * Opti-Logistix Dashboard Application
 * Afet Lojistik Karar Destek Sistemi
 */

// =============================================================================
// Configuration
// =============================================================================
const API_BASE_URL = 'http://localhost:8000/api/v1';
const MAP_CENTER = [41.02, 29.02]; // Istanbul
const MAP_ZOOM = 14;

// =============================================================================
// State
// =============================================================================
const state = {
    map: null,
    layers: {
        edges: null,
        damageHeat: null,
        route: null,
        vehicles: null,
        zones: null
    },
    markers: {
        start: null,
        end: null
    },
    currentScenario: null,
    selecting: null, // 'start' or 'end'
    graphData: { nodes: [], edges: [] }
};

// =============================================================================
// Initialization
// =============================================================================
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    initEventListeners();
    loadInitialData();
    startClock();
});

function initMap() {
    // Create Leaflet map
    state.map = L.map('map', {
        center: MAP_CENTER,
        zoom: MAP_ZOOM,
        zoomControl: true
    });

    // Dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap, &copy; CARTO',
        maxZoom: 19
    }).addTo(state.map);

    // Initialize layer groups
    state.layers.edges = L.layerGroup().addTo(state.map);
    state.layers.route = L.layerGroup().addTo(state.map);
    state.layers.vehicles = L.layerGroup().addTo(state.map);
    state.layers.zones = L.layerGroup().addTo(state.map);

    // Map click handler
    state.map.on('click', handleMapClick);
}

function initEventListeners() {
    // Scenario buttons
    document.querySelectorAll('.scenario-btn').forEach(btn => {
        btn.addEventListener('click', () => handleScenarioSelect(btn.dataset.scenario));
    });

    // Route buttons
    document.getElementById('btnCalculateRoute').addEventListener('click', calculateRoute);
    document.getElementById('btnClearRoute').addEventListener('click', clearRoute);

    // Input focus handlers
    document.getElementById('startPoint').addEventListener('focus', () => { state.selecting = 'start'; });
    document.getElementById('endPoint').addEventListener('focus', () => { state.selecting = 'end'; });
}

async function loadInitialData() {
    showLoading(true);
    try {
        // Load graph data
        const [nodesRes, edgesRes, resourcesRes] = await Promise.all([
            fetch(`${API_BASE_URL}/graph/nodes`),
            fetch(`${API_BASE_URL}/graph/edges`),
            fetch(`${API_BASE_URL}/resources`)
        ]);

        state.graphData.nodes = (await nodesRes.json()).nodes;
        state.graphData.edges = (await edgesRes.json()).edges;
        const resources = (await resourcesRes.json());

        // Draw edges on map
        drawEdges(state.graphData.edges);

        // Update resources panel
        updateResourcesPanel(resources);

        showToast('success', 'Sistem hazır');
    } catch (error) {
        console.error('Load error:', error);
        showToast('error', 'Veri yüklenemedi. Demo mod aktif.');
        loadDemoData();
    }
    showLoading(false);
}

function loadDemoData() {
    // Create demo edges for visualization
    const demoEdges = [];
    for (let i = 0; i < 5; i++) {
        for (let j = 0; j < 5; j++) {
            const lat1 = 41.0 + i * 0.01;
            const lon1 = 29.0 + j * 0.01;

            if (j < 4) {
                demoEdges.push({
                    from: { lat: lat1, lon: lon1 },
                    to: { lat: lat1, lon: lon1 + 0.01 },
                    damage: 0
                });
            }
            if (i < 4) {
                demoEdges.push({
                    from: { lat: lat1, lon: lon1 },
                    to: { lat: lat1 + 0.01, lon: lon1 },
                    damage: 0
                });
            }
        }
    }
    state.graphData.edges = demoEdges;
    drawEdges(demoEdges);

    // Demo resources
    updateResourcesPanel({
        resources: [
            { resource_id: 'AMB-001', resource_type: 'ambulance', status: 'available' },
            { resource_id: 'AMB-002', resource_type: 'ambulance', status: 'available' },
            { resource_id: 'FIRE-001', resource_type: 'fire_truck', status: 'available' }
        ]
    });
}

// =============================================================================
// Map Functions
// =============================================================================
function drawEdges(edges) {
    state.layers.edges.clearLayers();

    edges.forEach(edge => {
        const color = getDamageColor(edge.damage || 0);
        const weight = edge.damage > 0.5 ? 4 : 2;

        const line = L.polyline(
            [[edge.from.lat, edge.from.lon], [edge.to.lat, edge.to.lon]],
            { color, weight, opacity: 0.7 }
        );

        line.bindPopup(`
            <strong>Yol Durumu</strong><br>
            Hasar: ${((edge.damage || 0) * 100).toFixed(0)}%<br>
            Seviye: ${getDamageLevel(edge.damage || 0)}
        `);

        state.layers.edges.addLayer(line);
    });
}

function getDamageColor(damage) {
    if (damage < 0.2) return '#10b981'; // Green
    if (damage < 0.5) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
}

function getDamageLevel(damage) {
    if (damage < 0.2) return 'Güvenli';
    if (damage < 0.5) return 'Riskli';
    return 'Hasarlı';
}

function handleMapClick(e) {
    const { lat, lng } = e.latlng;

    if (state.selecting === 'start') {
        setMarker('start', lat, lng);
        document.getElementById('startPoint').value = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
    } else if (state.selecting === 'end') {
        setMarker('end', lat, lng);
        document.getElementById('endPoint').value = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
    }
}

function setMarker(type, lat, lng) {
    // Remove existing marker
    if (state.markers[type]) {
        state.map.removeLayer(state.markers[type]);
    }

    // Create marker icon
    const icon = L.divIcon({
        className: 'custom-marker',
        html: type === 'start' ? '📍' : '🎯',
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });

    state.markers[type] = L.marker([lat, lng], { icon }).addTo(state.map);
}

function drawRoute(routeData) {
    state.layers.route.clearLayers();

    if (!routeData.path_coords || routeData.path_coords.length < 2) return;

    const coords = routeData.path_coords.map(c => [c.lat, c.lon]);

    // Draw route line
    const routeLine = L.polyline(coords, {
        color: '#3b82f6',
        weight: 5,
        opacity: 0.9,
        lineCap: 'round',
        lineJoin: 'round'
    });

    // Add glow effect
    const glowLine = L.polyline(coords, {
        color: '#3b82f6',
        weight: 12,
        opacity: 0.3,
        lineCap: 'round'
    });

    state.layers.route.addLayer(glowLine);
    state.layers.route.addLayer(routeLine);

    // Fit bounds
    state.map.fitBounds(routeLine.getBounds(), { padding: [50, 50] });
}

function drawDamageZones(zones) {
    state.layers.zones.clearLayers();

    zones.forEach(zone => {
        const color = zone.score > 0.7 ? '#ef4444' :
            zone.score > 0.4 ? '#f59e0b' : '#10b981';

        const circle = L.circle([zone.center.lat, zone.center.lon], {
            radius: zone.radius_m,
            color: color,
            fillColor: color,
            fillOpacity: 0.2,
            weight: 2
        });

        circle.bindPopup(`
            <strong>${zone.id}</strong><br>
            Hasar Seviyesi: ${zone.level}<br>
            Skor: ${(zone.score * 100).toFixed(0)}%
        `);

        state.layers.zones.addLayer(circle);
    });
}

// =============================================================================
// Scenario Functions
// =============================================================================
async function handleScenarioSelect(scenario) {
    // Update button states
    document.querySelectorAll('.scenario-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.scenario === scenario);
    });

    if (scenario === 'none') {
        await clearScenario();
        return;
    }

    showLoading(true);
    try {
        const response = await fetch(`${API_BASE_URL}/scenarios/preset/${scenario}`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Senaryo aktifleştirilemedi');

        const result = await response.json();
        state.currentScenario = result;

        // Update UI
        document.getElementById('scenarioStatus').textContent =
            `Senaryo: ${scenario.toUpperCase()} (M${result.magnitude})`;

        // Fetch and display damage map
        await loadDamageMap();

        // Load recommendations
        await loadRecommendations();

        showToast('warning', `${scenario.toUpperCase()} senaryosu aktif`);
    } catch (error) {
        console.error('Scenario error:', error);
        showToast('error', 'Senaryo yüklenemedi');
        // Demo mode
        applyDemoScenario(scenario);
    }
    showLoading(false);
}

async function clearScenario() {
    try {
        await fetch(`${API_BASE_URL}/scenarios/current`, { method: 'DELETE' });
    } catch (e) { }

    state.currentScenario = null;
    state.layers.zones.clearLayers();

    // Reset edges to green
    state.graphData.edges.forEach(e => e.damage = 0);
    drawEdges(state.graphData.edges);

    // Clear stats
    document.getElementById('damagedRoads').textContent = '0';
    document.getElementById('damagedBridges').textContent = '0';
    document.getElementById('scenarioStatus').textContent = 'Senaryo: Normal';
    document.getElementById('recommendationCount').textContent = '0';

    // Clear recommendations
    document.getElementById('recommendations').innerHTML = `
        <div class="recommendation-empty">
            <span class="empty-icon">🔍</span>
            <p>Senaryo seçildiğinde AI önerileri burada görünecek</p>
        </div>
    `;

    showToast('success', 'Senaryo temizlendi');
}

async function loadDamageMap() {
    try {
        const response = await fetch(`${API_BASE_URL}/damage-map`);
        if (!response.ok) throw new Error();

        const data = await response.json();

        // Update edge damages
        const damageMap = {};
        data.edges.forEach(e => { damageMap[e.id] = e.damage; });

        state.graphData.edges.forEach(edge => {
            const id = edge.id || `${edge.from.lat}_${edge.to.lat}`;
            edge.damage = damageMap[id] || Math.random() * 0.5;
        });

        drawEdges(state.graphData.edges);
        drawDamageZones(data.zones);

        // Update stats
        document.getElementById('damagedRoads').textContent = data.stats.damaged_edges;
        document.getElementById('damagedBridges').textContent = data.stats.critical_edges;

    } catch (e) {
        console.error('Damage map error:', e);
        applyRandomDamage();
    }
}

function applyDemoScenario(scenario) {
    const damageRate = scenario === 'hafif' ? 0.15 :
        scenario === 'orta' ? 0.35 : 0.6;

    let damagedCount = 0;
    state.graphData.edges.forEach(edge => {
        if (Math.random() < damageRate) {
            edge.damage = Math.random() * 0.5 + 0.3;
            damagedCount++;
        } else {
            edge.damage = Math.random() * 0.2;
        }
    });

    drawEdges(state.graphData.edges);

    // Update stats
    document.getElementById('damagedRoads').textContent = damagedCount;
    document.getElementById('damagedBridges').textContent = Math.floor(damagedCount / 10);

    // Demo zones
    drawDamageZones([
        { id: 'Z0_CRITICAL', center: { lat: 41.02, lon: 29.02 }, radius_m: 500, score: 0.9, level: 'critical' },
        { id: 'Z1_SEVERE', center: { lat: 41.02, lon: 29.02 }, radius_m: 1500, score: 0.6, level: 'severe' }
    ]);

    // Demo recommendations
    addDemoRecommendations(scenario);
}

function applyRandomDamage() {
    state.graphData.edges.forEach(edge => {
        edge.damage = Math.random() * 0.6;
    });
    drawEdges(state.graphData.edges);
}

// =============================================================================
// Route Functions
// =============================================================================
async function calculateRoute() {
    const startInput = document.getElementById('startPoint').value;
    const endInput = document.getElementById('endPoint').value;

    if (!startInput || !endInput) {
        showToast('error', 'Başlangıç ve hedef noktası seçin');
        return;
    }

    const [startLat, startLon] = startInput.split(',').map(s => parseFloat(s.trim()));
    const [endLat, endLon] = endInput.split(',').map(s => parseFloat(s.trim()));

    showLoading(true);
    try {
        const response = await fetch(`${API_BASE_URL}/route`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start: { lat: startLat, lon: startLon },
                end: { lat: endLat, lon: endLon },
                vehicle_type: 'ambulance',
                urgency: 0.8,
                method: 'astar'
            })
        });

        const result = await response.json();

        if (result.success && result.route) {
            drawRoute(result.route);
            updateRouteInfo(result.route);
            showToast('success', 'Rota hesaplandı');
        } else {
            showToast('error', result.message || 'Rota bulunamadı');
        }
    } catch (error) {
        console.error('Route error:', error);
        // Demo route
        createDemoRoute(startLat, startLon, endLat, endLon);
    }
    showLoading(false);
}

function createDemoRoute(startLat, startLon, endLat, endLon) {
    const steps = 5;
    const path_coords = [];

    for (let i = 0; i <= steps; i++) {
        const t = i / steps;
        path_coords.push({
            lat: startLat + (endLat - startLat) * t + (Math.random() - 0.5) * 0.002,
            lon: startLon + (endLon - startLon) * t + (Math.random() - 0.5) * 0.002
        });
    }

    const demoRoute = {
        path_coords,
        estimated_time: 12.5,
        distance_km: 2.3,
        risk_score: 0.25,
        method: 'astar',
        is_optimal: true
    };

    drawRoute(demoRoute);
    updateRouteInfo(demoRoute);
    showToast('success', 'Demo rota oluşturuldu');
}

function updateRouteInfo(route) {
    const infoPanel = document.getElementById('routeInfo');
    infoPanel.style.display = 'block';

    document.getElementById('routeTime').textContent = `${route.estimated_time.toFixed(1)} dk`;
    document.getElementById('routeDistance').textContent = `${route.distance_km.toFixed(2)} km`;
    document.getElementById('routeRisk').textContent = `${(route.risk_score * 100).toFixed(0)}%`;
    document.getElementById('routeMethod').textContent = route.method.toUpperCase();
}

function clearRoute() {
    state.layers.route.clearLayers();

    if (state.markers.start) {
        state.map.removeLayer(state.markers.start);
        state.markers.start = null;
    }
    if (state.markers.end) {
        state.map.removeLayer(state.markers.end);
        state.markers.end = null;
    }

    document.getElementById('startPoint').value = '';
    document.getElementById('endPoint').value = '';
    document.getElementById('routeInfo').style.display = 'none';

    showToast('info', 'Rota temizlendi');
}

// =============================================================================
// Recommendations
// =============================================================================
async function loadRecommendations() {
    try {
        const response = await fetch(`${API_BASE_URL}/recommendations`);
        const data = await response.json();
        displayRecommendations(data.recommendations);
    } catch (e) {
        console.error('Recommendations error:', e);
    }
}

function addDemoRecommendations(scenario) {
    const recs = [
        {
            type: 'warning',
            priority: 'high',
            message: 'Merkez bölgede kritik hasar tespit edildi'
        },
        {
            type: 'route',
            priority: 'medium',
            message: 'AMB-001 için alternatif rota önerisi: Sahil yolu üzerinden 8 dk tasarruf'
        },
        {
            type: 'allocation',
            priority: scenario === 'siddetli' ? 'high' : 'medium',
            message: 'Batı Hastanesi kapasitesi uygun. Ambulansları yönlendirin.'
        }
    ];

    displayRecommendations(recs);
}

function displayRecommendations(recs) {
    const container = document.getElementById('recommendations');
    document.getElementById('recommendationCount').textContent = recs.length;

    if (recs.length === 0) {
        container.innerHTML = `
            <div class="recommendation-empty">
                <span class="empty-icon">✅</span>
                <p>Şu anda öneri bulunmuyor</p>
            </div>
        `;
        return;
    }

    container.innerHTML = recs.map(rec => `
        <div class="recommendation ${rec.priority}">
            <div class="recommendation-header">
                <span class="recommendation-type">${getTypeIcon(rec.type)} ${rec.type}</span>
                <span class="recommendation-priority ${rec.priority}">${rec.priority.toUpperCase()}</span>
            </div>
            <div class="recommendation-message">${rec.message}</div>
        </div>
    `).join('');
}

function getTypeIcon(type) {
    const icons = { warning: '⚠️', route: '🧭', allocation: '📦' };
    return icons[type] || '💡';
}

// =============================================================================
// Resources
// =============================================================================
function updateResourcesPanel(data) {
    const container = document.getElementById('resourcesList');
    const resources = data.resources || [];

    // Update counts
    document.getElementById('ambulanceCount').textContent =
        resources.filter(r => r.resource_type === 'ambulance').length;
    document.getElementById('fireCount').textContent =
        resources.filter(r => r.resource_type === 'fire_truck').length;

    container.innerHTML = resources.map(r => `
        <div class="resource-item" data-id="${r.resource_id}">
            <span class="resource-icon">${getResourceIcon(r.resource_type)}</span>
            <div class="resource-info">
                <div class="resource-id">${r.resource_id}</div>
                <div class="resource-type">${getResourceLabel(r.resource_type)}</div>
            </div>
            <span class="resource-status ${r.status}">${r.status === 'available' ? 'Müsait' : 'Atandı'}</span>
        </div>
    `).join('');
}

function getResourceIcon(type) {
    const icons = { ambulance: '🚑', fire_truck: '🚒', rescue: '🚨', supply_truck: '🚛' };
    return icons[type] || '🚗';
}

function getResourceLabel(type) {
    const labels = { ambulance: 'Ambulans', fire_truck: 'İtfaiye', rescue: 'Kurtarma', supply_truck: 'Lojistik' };
    return labels[type] || type;
}

// =============================================================================
// UI Helpers
// =============================================================================
function showLoading(show) {
    document.getElementById('loadingOverlay').classList.toggle('visible', show);
}

function showToast(type, message) {
    const container = document.getElementById('toastContainer');
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <span class="toast-message">${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toastIn 0.3s reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function startClock() {
    const update = () => {
        const now = new Date();
        document.getElementById('currentTime').textContent =
            now.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    };
    update();
    setInterval(update, 1000);
}
