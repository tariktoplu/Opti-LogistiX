/**
 * Opti-Logistix Dashboard - OSMnx Entegrasyonu
 * Gerçek harita verileri ile çalışan versiyon
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

// =============================================================================
// State
// =============================================================================
const state = {
    map: null,
    layers: {
        roads: null,
        route: null,
        hospitals: null,
        depots: null,
        zones: null
    },
    markers: {
        start: null,
        end: null
    },
    currentScenario: null,
    selecting: null,
    mapBounds: null
};

// =============================================================================
// Initialization
// =============================================================================
document.addEventListener('DOMContentLoaded', async () => {
    showLoading(true);

    // API'den harita sınırlarını al
    try {
        const boundsRes = await fetch(`${API_BASE_URL}/map/bounds`);
        state.mapBounds = await boundsRes.json();
    } catch (e) {
        state.mapBounds = { center_lat: 40.9907, center_lon: 29.0230 };
    }

    initMap();
    initEventListeners();
    await loadMapData();
    startClock();

    showLoading(false);
});

function initMap() {
    const center = [
        state.mapBounds.center_lat || 40.9907,
        state.mapBounds.center_lon || 29.0230
    ];

    state.map = L.map('map', {
        center: center,
        zoom: 15,
        zoomControl: true
    });

    // Dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap, &copy; CARTO',
        maxZoom: 19
    }).addTo(state.map);

    // Layer groups
    state.layers.roads = L.layerGroup().addTo(state.map);
    state.layers.route = L.layerGroup().addTo(state.map);
    state.layers.hospitals = L.layerGroup().addTo(state.map);
    state.layers.depots = L.layerGroup().addTo(state.map);
    state.layers.zones = L.layerGroup().addTo(state.map);

    state.map.on('click', handleMapClick);
}

function initEventListeners() {
    document.querySelectorAll('.scenario-btn').forEach(btn => {
        btn.addEventListener('click', () => handleScenarioSelect(btn.dataset.scenario));
    });

    document.getElementById('btnCalculateRoute').addEventListener('click', calculateRoute);
    document.getElementById('btnClearRoute').addEventListener('click', clearRoute);

    document.getElementById('startPoint').addEventListener('focus', () => { state.selecting = 'start'; });
    document.getElementById('endPoint').addEventListener('focus', () => { state.selecting = 'end'; });
}

// =============================================================================
// Data Loading
// =============================================================================
async function loadMapData() {
    try {
        // Yolları yükle
        const edgesRes = await fetch(`${API_BASE_URL}/map/edges`);
        const edgesData = await edgesRes.json();
        drawRoads(edgesData.features);

        // Düğümleri yükle (hastane, depo)
        const nodesRes = await fetch(`${API_BASE_URL}/map/nodes`);
        const nodesData = await nodesRes.json();
        drawSpecialNodes(nodesData);

        // Kaynakları yükle
        const resourcesRes = await fetch(`${API_BASE_URL}/resources`);
        const resources = await resourcesRes.json();
        updateResourcesPanel(resources);

        // İstatistikleri güncelle
        const statsRes = await fetch(`${API_BASE_URL}/stats`);
        const stats = await statsRes.json();
        updateStats(stats);

        showToast('success', `Harita yüklendi: ${stats.nodes} kavşak, ${stats.edges} yol`);

    } catch (error) {
        console.error('Veri yükleme hatası:', error);
        showToast('error', 'Harita yüklenemedi. API çalışıyor mu?');
    }
}

// =============================================================================
// Map Drawing
// =============================================================================
function drawRoads(edges) {
    state.layers.roads.clearLayers();

    edges.forEach(edge => {
        if (!edge.path || edge.path.length < 2) return;

        const color = getDamageColor(edge.damage_prob || 0);
        const weight = getLineWeight(edge.highway);

        const polyline = L.polyline(edge.path, {
            color: color,
            weight: weight,
            opacity: 0.8,
            smoothFactor: 1
        });

        // Popup
        const popupContent = `
            <div style="font-size: 12px;">
                <strong>${edge.name || 'Yol'}</strong><br>
                Uzunluk: ${(edge.length || 0).toFixed(0)} m<br>
                Tip: ${edge.highway || 'road'}<br>
                Hasar: ${((edge.damage_prob || 0) * 100).toFixed(0)}%
            </div>
        `;
        polyline.bindPopup(popupContent);

        state.layers.roads.addLayer(polyline);
    });
}

function drawSpecialNodes(nodesData) {
    state.layers.hospitals.clearLayers();
    state.layers.depots.clearLayers();

    // Hastaneler
    nodesData.hospitals.forEach(node => {
        const marker = L.marker([node.lat, node.lon], {
            icon: L.divIcon({
                className: 'custom-marker hospital-marker',
                html: '🏥',
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        });
        marker.bindPopup(`<strong>${node.name || 'Hastane'}</strong>`);
        state.layers.hospitals.addLayer(marker);
    });

    // Depolar
    nodesData.depots.forEach(node => {
        const marker = L.marker([node.lat, node.lon], {
            icon: L.divIcon({
                className: 'custom-marker depot-marker',
                html: '📦',
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        });
        marker.bindPopup(`<strong>${node.name || 'Depo'}</strong>`);
        state.layers.depots.addLayer(marker);
    });
}

function getDamageColor(damage) {
    if (damage > 0.8) return '#e74c3c';  // Kritik - Kırmızı
    if (damage > 0.5) return '#f1c40f';  // Orta - Sarı
    if (damage > 0.2) return '#f39c12';  // Düşük - Turuncu
    return '#2ecc71';  // Güvenli - Yeşil
}

function getLineWeight(highway) {
    const weights = {
        'motorway': 4,
        'trunk': 4,
        'primary': 3,
        'secondary': 2.5,
        'tertiary': 2,
        'residential': 1.5,
        'unclassified': 1
    };

    if (Array.isArray(highway)) highway = highway[0];
    return weights[highway] || 1.5;
}

function handleMapClick(e) {
    const { lat, lng } = e.latlng;

    if (state.selecting === 'start') {
        setMarker('start', lat, lng);
        document.getElementById('startPoint').value = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
    } else if (state.selecting === 'end') {
        setMarker('end', lat, lng);
        document.getElementById('endPoint').value = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
    }
}

function setMarker(type, lat, lng) {
    if (state.markers[type]) {
        state.map.removeLayer(state.markers[type]);
    }

    const icon = L.divIcon({
        className: 'custom-marker',
        html: type === 'start' ? '📍' : '🎯',
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });

    state.markers[type] = L.marker([lat, lng], { icon }).addTo(state.map);
}

// =============================================================================
// Scenario Management
// =============================================================================
async function handleScenarioSelect(scenario) {
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

        document.getElementById('scenarioStatus').textContent =
            `Senaryo: ${scenario.toUpperCase()} (M${result.magnitude})`;

        // Yolları yeniden çiz (hasarla)
        await refreshRoads();

        // Önerileri yükle
        await loadRecommendations();

        // İstatistikleri güncelle
        await updateStatsFromAPI();

        showToast('warning', `${scenario.toUpperCase()} senaryosu aktif!`);

    } catch (error) {
        console.error('Senaryo hatası:', error);
        showToast('error', 'Senaryo yüklenemedi');
    }
    showLoading(false);
}

async function clearScenario() {
    try {
        await fetch(`${API_BASE_URL}/scenarios/current`, { method: 'DELETE' });
    } catch (e) { }

    state.currentScenario = null;
    document.getElementById('scenarioStatus').textContent = 'Senaryo: Normal';

    await refreshRoads();

    document.getElementById('damagedRoads').textContent = '0';
    document.getElementById('damagedBridges').textContent = '0';
    document.getElementById('recommendationCount').textContent = '0';

    document.getElementById('recommendations').innerHTML = `
        <div class="recommendation-empty">
            <span class="empty-icon">🔍</span>
            <p>Senaryo seçildiğinde AI önerileri burada görünecek</p>
        </div>
    `;

    showToast('success', 'Senaryo temizlendi');
}

async function refreshRoads() {
    try {
        const edgesRes = await fetch(`${API_BASE_URL}/map/edges`);
        const edgesData = await edgesRes.json();
        drawRoads(edgesData.features);
    } catch (e) {
        console.error('Yol yenileme hatası:', e);
    }
}

// =============================================================================
// Route Calculation
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
                urgency: 0.8
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
        console.error('Rota hatası:', error);
        showToast('error', 'Rota hesaplanamadı');
    }
    showLoading(false);
}

function drawRoute(routeData) {
    state.layers.route.clearLayers();

    if (!routeData.path_coords || routeData.path_coords.length < 2) return;

    const coords = routeData.path_coords.map(c => [c.lat, c.lon]);

    // Glow effect
    const glowLine = L.polyline(coords, {
        color: '#00bcd4',
        weight: 12,
        opacity: 0.3
    });

    // Main route
    const routeLine = L.polyline(coords, {
        color: '#00bcd4',
        weight: 5,
        opacity: 0.9,
        lineCap: 'round',
        lineJoin: 'round'
    });

    state.layers.route.addLayer(glowLine);
    state.layers.route.addLayer(routeLine);

    state.map.fitBounds(routeLine.getBounds(), { padding: [50, 50] });
}

function updateRouteInfo(route) {
    const infoPanel = document.getElementById('routeInfo');
    infoPanel.style.display = 'block';

    document.getElementById('routeTime').textContent = `${route.estimated_time.toFixed(1)} dk`;
    document.getElementById('routeDistance').textContent = `${route.distance_km.toFixed(2)} km`;
    document.getElementById('routeRisk').textContent = `${(route.risk_score * 100).toFixed(0)}%`;
    document.getElementById('routeMethod').textContent = 'DIJKSTRA';
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
// Stats & Recommendations
// =============================================================================
async function updateStatsFromAPI() {
    try {
        const statsRes = await fetch(`${API_BASE_URL}/stats`);
        const stats = await statsRes.json();
        updateStats(stats);
    } catch (e) { }
}

function updateStats(stats) {
    const damageStats = stats.damage_levels || {};
    document.getElementById('damagedRoads').textContent =
        (damageStats.moderate || 0) + (damageStats.critical || 0);
    document.getElementById('damagedBridges').textContent = damageStats.critical || 0;
}

async function loadRecommendations() {
    try {
        const response = await fetch(`${API_BASE_URL}/recommendations`);
        const data = await response.json();
        displayRecommendations(data.recommendations);
    } catch (e) {
        console.error('Öneri hatası:', e);
    }
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
    return { warning: '⚠️', route: '🧭', allocation: '📦' }[type] || '💡';
}

// =============================================================================
// Resources Panel
// =============================================================================
function updateResourcesPanel(data) {
    const container = document.getElementById('resourcesList');
    const resources = data.resources || [];

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
    return { ambulance: '🚑', fire_truck: '🚒', rescue: '🚨', supply_truck: '🚛' }[type] || '🚗';
}

function getResourceLabel(type) {
    return { ambulance: 'Ambulans', fire_truck: 'İtfaiye', rescue: 'Kurtarma', supply_truck: 'Lojistik' }[type] || type;
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
