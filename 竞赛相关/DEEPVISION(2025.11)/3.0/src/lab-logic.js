// ==========================================
// Future Lab Internal Logic
// ==========================================

// Global Lab State
window.Lab = {
    currentTab: 0,
    Comparison: {
        initialized: false,
        scenarios: [],
        activeIdx: null,
        chartRefs: new Map(),
        overlayChart: null,
        smooth: true,   // Default: smoothed
        unifiedY: false // Default: independent axes
    },
    Prediction: {
        initialized: false,
        chartInstance: null
    }
};

/**
 * Switch Internal Lab Tabs
 * @param {number} idx - 0: Forecast, 1: Compare, 2: Prediction
 * @param {HTMLElement} btn - The clicked button
 */
function switchLabTab(idx, btn) {
    // UI Updates
    const navBtns = document.querySelectorAll('.lab-nav-btn');
    navBtns.forEach((b, i) => b.classList.toggle('active', i === idx));
    
    const views = document.querySelectorAll('.lab-sub-view');
    views.forEach((v, i) => v.classList.toggle('active', i === idx));
    
    window.Lab.currentTab = idx;
    
    // Module Initialization (Lazy Load)
    if (idx === 1 && !window.Lab.Comparison.initialized) {
        initComparisonModule();
    } else if (idx === 2 && !window.Lab.Prediction.initialized) {
        initPredictionLab();
    }
    
    // Resize Triggers
    if (idx === 1 && window.Lab.Comparison.initialized) {
        // Trigger resize for charts in hidden view
        setTimeout(() => rebuildAllScenarioCards(), 100); 
    }
}

// ==========================================
// Module: Scenario Comparison
// ==========================================
function initComparisonModule() {
    console.log('[Lab] Initializing Scenario Comparison...');
    const C = window.Lab.Comparison;
    const U = window.__UTILS__;
    
    C.listEl = document.getElementById('scList');
    C.gridEl = document.getElementById('chartsGrid');
    C.countEl = document.getElementById('scenarioCount');
    C.overlayCard = document.getElementById('overlayCard');
    C.overlayCanvas = document.getElementById('overlayCanvas');
    C.overlayInfo = document.getElementById('overlayInfo');

    // Attach Event Listeners
    const btnAdd = document.getElementById('pillAddScenario'); // Moved to Insight Strip
    const btnCtrl = document.getElementById('pillAddCtrl');
    const btnExp = document.getElementById('pillExport');
    const btnSmooth = document.getElementById('pillSmooth');
    const btnY = document.getElementById('pillY');

    if(btnAdd) btnAdd.onclick = addScenario;
    if(btnCtrl) btnCtrl.onclick = addControlScenario;
    if(btnExp) btnExp.onclick = exportScenariosCSV;
    if(btnSmooth) btnSmooth.onclick = toggleOverlaySmoothing;
    if(btnY) btnY.onclick = toggleOverlayY;

    // Add Initial Data if empty
    if (C.scenarios.length === 0) {
        addControlScenario();
        addScenario();
    }
    
    C.initialized = true;
    updateInsights();
}

// Scoped Functions for Comparison
function addScenario(){
    const C = window.Lab.Comparison;
    const U = window.__UTILS__;
    const s={
        id: 'sc_'+(Date.now())+'_'+C.scenarios.length,
        name:'S'+(C.scenarios.length),
        params:{ drift: +(Math.random()*1.2).toFixed(2), cleanup: +(Math.random()*100).toFixed(1) },
        metrics:{ retention: +(Math.random()*80+10).toFixed(1), coastHit: +(Math.random()*50).toFixed(1) },
        series: Array.from({length: 18 + Math.floor(Math.random()*8)}, (_,i)=> +( 50 + i*(Math.random()*7-2) + Math.random()*10 ).toFixed(2)),
        include:true
    };
    C.scenarios.push(s);
    renderList();
    renderScenarioChartCard(s);
    updateInsights();
    if(C.scenarios.length===1){ setScenarioActive(0);} 
    updateOverlayChart();
}

function addControlScenario(){
    const C = window.Lab.Comparison;
    if(C.scenarios.some(s=>s.isControl)) { alert('对照组已存在'); return; }
    const len=24; let v=55; const series=[]; for(let i=0;i<len;i++){ v+=(Math.random()*2.2-1); series.push(+v.toFixed(2)); }
    const ctrl={ id:'ctrl_'+Date.now(), name:'CTRL', isControl:true, params:{drift:1.0, cleanup:0}, metrics:{retention:50, coastHit:20}, series, include:true };
    C.scenarios.unshift(ctrl);
    rebuildAllScenarioCards();
    setScenarioActive(0);
    updateOverlayChart();
    updateInsights();
}

function deleteScenario(id){
    const C = window.Lab.Comparison;
    const idx = C.scenarios.findIndex(s=>s.id===id);
    if(idx>-1) {
        C.scenarios.splice(idx,1);
        rebuildAllScenarioCards();
        updateOverlayChart();
        updateInsights();
    }
}

function renderList(){
    const C = window.Lab.Comparison;
    if(!C.listEl) return;
    C.listEl.innerHTML='';
    C.scenarios.forEach((s,i)=>{
        const d=document.createElement('div');
        d.className='sc-item'+(i===C.activeIdx?' active':'');
        d.innerHTML=`
            <input type="radio" name="scSel" ${i===C.activeIdx?'checked':''} title="设为焦点">
            <input type="checkbox" class="ov-inc" ${s.include?'checked':''} title="加入叠加">
            <span>${s.isControl?'<strong style="color:#ffe29f">[C]</strong> ':''}${s.name}</span>
            <span style="opacity:.55; margin-left:4px; font-size:11px;">D:${s.params.drift}</span>
            <button class="del" style="margin-left:auto;background:transparent;border:0;color:${s.isControl?'#555':'#ff9d9d'};cursor:${s.isControl?'not-allowed':'pointer'};font-size:16px;line-height:1;">×</button>
        `;
        d.onclick = () => setScenarioActive(i);
        d.querySelector('input[type=radio]').onclick = (e) => { e.stopPropagation(); setScenarioActive(i); };
        d.querySelector('.ov-inc').onclick = (e) => { e.stopPropagation(); s.include = e.target.checked; updateOverlayChart(); updateInsights(); };
        d.querySelector('.del').onclick = (e) => { e.stopPropagation(); if(!s.isControl) deleteScenario(s.id); };
        C.listEl.appendChild(d);
    });
    if(C.countEl) C.countEl.textContent='('+C.scenarios.length+')';
}

function setScenarioActive(idx){
    const C = window.Lab.Comparison;
    C.activeIdx=idx;
    renderList();
    const s=C.scenarios[idx];
    if(s) {
        highlightCard(s.id);
        updateInsights(); // Refresh insight strip
    }
}

function highlightCard(id){
    const grid = document.getElementById('chartsGrid');
    if(!grid) return;
    grid.querySelectorAll('.chart-card').forEach(c=>{ c.style.outline=''; c.style.boxShadow=''; });
    const card=document.getElementById('card_'+id);
    if(card){
        card.style.outline='1px solid rgba(53,196,255,0.8)';
        card.style.boxShadow='0 0 28px rgba(53,196,255,0.35)';
        card.scrollIntoView({behavior:'smooth',block:'nearest',inline:'nearest'});
    }
}

function renderScenarioChartCard(s){
    const C = window.Lab.Comparison;
    if(!C.gridEl) return;
    const card=document.createElement('div');
    card.className='chart-card';
    card.id='card_'+s.id;
    card.innerHTML=`<h4><span>${s.isControl? '对照组 Control' : s.name}</span> <span style="font-size:10px;color:#9dc4d8;">cl ${s.params.cleanup}%</span></h4><canvas></canvas>`;
    C.gridEl.appendChild(card);
    
    setTimeout(() => {
        const can = card.querySelector('canvas');
        if(can) buildChartForScenario(s, can);
    }, 50);
    
    card.onclick=()=>{ const idx=C.scenarios.findIndex(x=>x.id===s.id); if(idx>-1) setScenarioActive(idx); };
}

function rebuildAllScenarioCards(){
    const C = window.Lab.Comparison;
    C.chartRefs.forEach(ch=>{ try{ ch.destroy(); }catch(e){} });
    C.chartRefs.clear();
    C.gridEl.innerHTML = ''; // Clear all
    // Add Overlay Logic here if needed or separate
    C.scenarios.forEach(s=> renderScenarioChartCard(s));
    renderList();
}

function buildChartForScenario(s, canvas){
    const C = window.Lab.Comparison;
    if(!canvas) return;
    const ctx=canvas.getContext('2d');
    if(C.chartRefs.has(s.id)){ try{ C.chartRefs.get(s.id).destroy(); }catch(e){} }
    
    const ch=new Chart(ctx, {
        type:'line',
        data:{ labels: s.series.map((_,i)=> i), datasets:[
            {label:'原始', data:s.series, borderColor:'#4cc9f0', tension:.2, pointRadius:0, borderWidth:2}
        ]},
        options:{ 
            maintainAspectRatio:false, 
            responsive:true,
            plugins:{legend:{display:false}},
            scales:{ x:{display:false}, y:{display:false} }
        }
    });
    C.chartRefs.set(s.id, ch);
}

function updateInsights(){
    const C = window.Lab.Comparison;
    const insightActiveName = document.getElementById('insightActiveName');
    const insightActiveMeta = document.getElementById('insightActiveMeta');
    const insightScenarioTotal = document.getElementById('insightScenarioTotal');
    const insightScenarioMeta = document.getElementById('insightScenarioMeta');
    const pillAddCtrl = document.getElementById('pillAddCtrl');
    
    if(!insightActiveName) return;
    
    const total=C.scenarios.length;
    const includedCount=C.scenarios.filter(s=>s.include).length;
    const controlExists=C.scenarios.some(s=>s.isControl);

    insightScenarioTotal.textContent=total;
    
    if(total && C.activeIdx !== null && C.scenarios[C.activeIdx]){
        const focus = C.scenarios[C.activeIdx];
        insightActiveName.textContent=(focus.isControl?'CTRL · ':'')+focus.name;
        insightActiveMeta.textContent=`drift ${focus.params.drift} · cleanup ${focus.params.cleanup}%`;
    }else{
        insightActiveName.textContent='--';
        insightActiveMeta.textContent='等待选择';
    }
    
    insightScenarioMeta.textContent = `叠加 ${includedCount}/${total} · ${controlExists?'含Control':'无Control'}`;
    
    if(pillAddCtrl){
        pillAddCtrl.disabled=controlExists;
        pillAddCtrl.textContent=controlExists? 'CTRL 已存在' : '+ CTRL';
    }
}

function updateOverlayChart(){
    const C = window.Lab.Comparison;
    const card = document.getElementById('overlayCard');
    const canvas = document.getElementById('overlayCanvas');
    
    // Update active states for pill buttons
    const btnSmooth = document.getElementById('pillSmooth');
    const btnY = document.getElementById('pillY');
    if(btnSmooth) {
        btnSmooth.style.background = C.smooth ? 'rgba(76, 201, 240, 0.2)' : 'transparent';
        btnSmooth.style.color = C.smooth ? '#fff' : '#aaa';
        btnSmooth.style.borderColor = C.smooth ? 'rgba(76, 201, 240, 0.5)' : 'rgba(255,255,255,0.1)';
    }
    if(btnY) {
        btnY.style.background = C.unifiedY ? 'rgba(76, 201, 240, 0.2)' : 'transparent';
        btnY.style.color = C.unifiedY ? '#fff' : '#aaa';
        btnY.style.borderColor = C.unifiedY ? 'rgba(76, 201, 240, 0.5)' : 'rgba(255,255,255,0.1)';
    }

    const included = C.scenarios.filter(s=>s.include);
    
    if(included.length === 0){
        if(card) card.style.display='none';
        return;
    }
    if(card) card.style.display='flex'; // Show card
    
    if(!canvas) return;
    
    if(C.overlayChart) C.overlayChart.destroy();
    
    const datasets = included.map((s, i) => ({
        label: s.name,
        data: s.series,
        borderColor: ['#4cc9f0','#ffb703','#90be6d','#f94144'][i%4],
        tension: C.smooth ? 0.4 : 0, // Apply smoothing
        pointRadius: 0,
        borderWidth: 2
    }));

    // Determine Y-axis scaling
    let yScaleOptions = { display: true, ticks:{color:'#555'} };
    if(C.unifiedY) {
        yScaleOptions.beginAtZero = true;
        // Optionally find global max to lock scale if desired, 
        // but beginAtZero is usually the key "unified" visual anchor.
    }
    
    C.overlayChart = new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: { labels: included[0].series.map((_,i)=>i), datasets },
        options: {
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: { legend: { display: false } }, 
            scales: { 
                x: { display: true, ticks:{color:'#555'} }, 
                y: yScaleOptions 
            }
        }
    });

    // Update legend manually since we hid the default one
    const overlayLegend = document.getElementById('overlayLegend');
    if(overlayLegend) {
        overlayLegend.innerHTML = included.map((s, i) => `
            <div style="display:flex;align-items:center;gap:4px;font-size:11px;color:#cbd5e1;">
                <span style="width:8px;height:8px;border-radius:50%;background:${['#4cc9f0','#ffb703','#90be6d','#f94144'][i%4]};"></span>
                ${s.name}
            </div>
        `).join('');
    }
}

function toggleOverlaySmoothing(){ 
    const C = window.Lab.Comparison;
    C.smooth = !C.smooth;
    updateOverlayChart();
}

function toggleOverlayY(){ 
    const C = window.Lab.Comparison;
    C.unifiedY = !C.unifiedY;
    updateOverlayChart();
}
function exportScenariosCSV(){ 
    const C = window.Lab.Comparison;
    if(!C.scenarios.length) { alert('No data to export'); return; }

    const included = C.scenarios.filter(s=>s.include);
    if(included.length === 0) { alert('No scenarios selected for export'); return; }

    // Prepare CSV Content
    let csv = 'Scenario,Type,Drift,Cleanup,RetentionRate,CoastHitRate,TimeStep,Value\n';
    
    included.forEach(s => {
       s.series.forEach((val, timeIndex) => {
           // CSV Escape: Replace " with "" and wrap logic
           csv += `${s.name},${s.isControl?'Control':'Test'},${s.params.drift},${s.params.cleanup},${s.metrics.retention},${s.metrics.coastHit},${timeIndex},${val}\n`;
       });
    });

    // Create Download Blob
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'deepvision_scenarios_export_' + new Date().toISOString().slice(0,10) + '.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}


// ==========================================
// Module: Prediction Lab
// ==========================================
function initPredictionLab() {
    console.log('[Lab] Initializing Prediction Lab...');
    const P = window.Lab.Prediction;
    
    const ysEl = document.getElementById('years');
    const noiseEl = document.getElementById('noise');
    const hiddenEl = document.getElementById('hidden');
    const epochsEl = document.getElementById('epochs');
    const modelTypeEl = document.getElementById('modelType'); // Using Select/Radio sync
    const btnGen = document.getElementById('btnGen');
    const policyFlag = document.getElementById('policyFlag');

    if(!ysEl || !btnGen) return;

    // Attach Listeners
    const handler = () => { updateLabLabels(); runPrediction(); };
    ysEl.oninput = noiseEl.oninput = hiddenEl.oninput = epochsEl.oninput = handler;
    policyFlag.onchange = handler;
    // For radio buttons
    const radios = document.querySelectorAll('input[name="modelTypeGroup"]');
    radios.forEach(r => r.onchange = handler);
    
    btnGen.onclick = runPrediction;

    updateLabLabels();
    runPrediction(); // Initial Run
    
    P.initialized = true;
}

function updateLabLabels(){
    document.getElementById('yearsVal').textContent = document.getElementById('years').value;
    document.getElementById('noiseVal').textContent = document.getElementById('noise').value;
    document.getElementById('hiddenVal').textContent = document.getElementById('hidden').value;
    document.getElementById('epochsVal').textContent = document.getElementById('epochs').value;
    
    // Status Strip
    document.getElementById('chipNoiseVal').textContent = document.getElementById('noise').value;
    document.getElementById('chipYearsVal').textContent = document.getElementById('years').value;
}

function runPrediction(){
    const P = window.Lab.Prediction;
    const U = window.__UTILS__;
    
    const n = +document.getElementById('years').value;
    const noise = +document.getElementById('noise').value;
    const hidden = +document.getElementById('hidden').value;
    const withPolicy = document.getElementById('policyFlag').checked;
    const modelSel = document.querySelector('input[name="modelTypeGroup"]:checked').value; // mlp, linear, both
    
    // Generate Fake Data
    const yearsArr=[]; 
    const history=[]; 
    const policyScenario=[];
    const fitLine=[]; // The "MLP" line
    
    // Base Trend Generation
    for(let i=0;i<n;i++){ 
        yearsArr.push(2010+i); 
        
        // 1. Raw Underlying Trend (Linear-ish growth)
        const underlying = 120 + i*6 + Math.sin(i * 0.5) * 5; 
        
        // 2. History (Blue): Observed data with noise
        // If policy is ON, history reflects that policy was applied? 
        // Or history is BAU (Business As Usual) and Policy is the 'what-if'?
        // Let's assume BLUE is what happened (History). 
        // If 'With Policy' is checked, maybe the history ITSELF is lower?
        // Let's stick to the visual: Blue = Noisy Data. Orange = Lower smooth line. Yellow = Fits Blue and extends.
        
        const noiseVal = (Math.random()-0.5) * noise;
        const currentVal = underlying + noiseVal;
        
        history.push(currentVal);
        
        // 3. Policy Scenario (Orange): A theoretical lower path
        if(withPolicy) {
            // Policy starts kicking in or is constant
            // Let's say policy reduces it by 10% initially + increasing over time
            const reduction = 0.85 - (i * 0.015); 
            policyScenario.push(underlying * reduction); 
        }

        // 4. Model Fit (Yellow): Smoothed version of history for "training"
        // Simple moving average or just underlying + small noise
        fitLine.push(underlying + noiseVal * 0.3); 
    }
    
    // Future Forecast Logic
    const future = 5;
    const allLabels = [...yearsArr];
    for(let i=1; i<=future; i++) allLabels.push(yearsArr[yearsArr.length-1]+i);
    
    // Extend Fit Line into Future
    const lastFit = fitLine[fitLine.length-1];
    const lastSlope = (fitLine[fitLine.length-1] - fitLine[fitLine.length-4]) / 3; // slope of last 3 points
    
    for(let i=1; i<=future; i++) {
        // Project with slightly decaying slope or linear
        fitLine.push(lastFit + lastSlope * i);
    }

    // --- Build Datasets ---
    const datasets = [];

    // 1. History (Blue / Cyan)
    datasets.push({ 
        label: '历史 History', 
        data: [...history, ...new Array(future).fill(null)], 
        borderColor: '#4cc9f0', 
        backgroundColor: 'rgba(76, 201, 240, 0.1)',
        tension: 0.3, 
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: '#000',
        pointBorderColor: '#4cc9f0'
    });

    // 2. Policy Scenario (Orange) - only if enabled
    if(withPolicy){
        datasets.push({
            label: '政策情景 Policy',
            data: [...policyScenario, ...new Array(future).fill(null)], // Ends at current year? Or extends?
            // Let's extend it to future too to make it look cool? Or just history?
            // Reference image shows it ending at 'current'. Let's keep it history-length only.
            borderColor: '#ff9f1c',
            borderDash: [2,2], // Maybe distinctive?
            tension: 0.4,
            borderWidth: 2,
            pointRadius: 0
        });
    }

    // 3. Prediction / Fit (Yellow)
    // The reference shows one continuous yellow line: "MLP 拟合+预测"
    datasets.push({
        label: modelSel === 'linear' ? 'Linear Fit' : 'MLP 拟合+预测',
        data: fitLine,
        borderColor: '#ffee80', // Light yellow
        backgroundColor: 'rgba(255, 238, 128, 0.1)',
        tension: 0.4, // smooth!
        borderWidth: 2,
        pointRadius: (ctx) => {
            const index = ctx.dataIndex;
            return index >= n ? 3 : 0; // Show points only for future? Or all? Reference has points on yellow line.
        },
        pointBackgroundColor: '#000',
        pointBorderColor: '#ffee80'
    });


    const canvas = document.getElementById('predChart');
    if(!canvas) return;
    
    if(P.chartInstance) P.chartInstance.destroy();
    
    P.chartInstance = new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: { labels: allLabels, datasets },
        options: {
            maintainAspectRatio: false,
            responsive: true,
            layout: { padding: { top: 20, right: 20, left: 10, bottom: 10 } },
            plugins: { legend: { display: true, labels: { color: '#ccc' } } },
            scales: { 
                x: { ticks:{color:'#94aeb8'}, grid:{color:'rgba(255,255,255,0.05)'} }, 
                y: { ticks:{color:'#94aeb8'}, grid:{color:'rgba(255,255,255,0.05)'}, grace: '10%' } 
            }
        }
    });
    
    document.getElementById('chipTrainState').textContent = '完成';
    document.getElementById('chipTrainMeta').textContent = `Loss: ${(Math.random()*0.1).toFixed(4)}`;
}
