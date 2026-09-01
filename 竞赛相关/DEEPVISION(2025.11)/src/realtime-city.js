// realtime-city.js  全球重点海域实时监测 (Piece-6)
// 功能: 定时(60s) 从 Open-Meteo API 获取全球主要坐标点的波浪高度和温度数据
// 备用: 内置模拟数据 (作为快速兜底)
(function(){
  const host=document.querySelector('[data-key="city"][data-embed="realtime-city"]');
  if(!host) return;
  const listEl=host.querySelector('#rt-country-list');
  const sparkCanvas=document.getElementById('rt-mini-spark');
  const statusText=document.getElementById('rt-status-text');
  const dot=host.querySelector('.rt-dot');
  const focusCountryEl=document.getElementById('rt-focus-country');
  const focusDeltaEl=document.getElementById('rt-focus-delta');
  const footnote=document.getElementById('rt-footnote');
  const modeBtns=[...host.querySelectorAll('.rt-mode-btn')];

  // 1. Force styling for Bigger Chart to match user expectation (Strict Layout)
  if(sparkCanvas) {
      sparkCanvas.style.maxHeight = 'none';
      sparkCanvas.style.minHeight = '140px';
      sparkCanvas.height = 160;
      // Remove the right-side text container to give full width to chart
      const row = document.getElementById('rt-spark-row');
      if(row) {
          row.style.height = 'auto'; 
          row.style.marginTop = 'auto'; // push to bottom
          row.style.display = 'block'; // Block layout for full width
          // Find the text container next to canvas and hide it
          const textDiv = row.querySelector('div:not(canvas)');
          if(textDiv) textDiv.style.display = 'none';
      }
  }
  
  let mode='wave'; // 'wave' or 'temp'
  const PALETTE=['#4ecdc4','#ff6b6b','#ffe66d','#6a5acd','#ff6b9d','#a8dadc','#6a5acd99','#4dabf7'];
  let timer=null; let lastData=null; let sparkChart=null;
  const REFRESH_MS=60000;

  // 预定义全球关键监测点 (Locations)
  const LOCATIONS = [
      { name: 'Shanghai', lat: 31.00, lon: 122.80, label: '上海近海' }, // East China Sea
      { name: 'Tokyo', lat: 34.50, lon: 139.80, label: '东京外海' },    // Pacific
      { name: 'SanFrancisco', lat: 37.70, lon: -123.00, label: '旧金山' }, // Pacific
      { name: 'Sydney', lat: -34.00, lon: 151.50, label: '悉尼近海' },  // Tasman Sea
      { name: 'Honolulu', lat: 21.00, lon: -157.50, label: '夏威夷' },   // Pacific
      { name: 'Singapore', lat: 1.15, lon: 103.85, label: '新加坡' },   // Singapore Strait
      { name: 'CapeTown', lat: -34.50, lon: 18.00, label: '开普敦' },   // Atlantic
      { name: 'London', lat: 52.00, lon: 2.00, label: '北海南部' }      // North Sea (prox London)
  ];

  function setStatus(s,color){ if(statusText){ statusText.textContent=s; } if(dot){ dot.style.background=color; } }

  async function fetchMarineData(){
      // Construct Open-Meteo URL
      const lats = LOCATIONS.map(l=>l.lat).join(',');
      const lons = LOCATIONS.map(l=>l.lon).join(',');
      const url = `https://marine-api.open-meteo.com/v1/marine?latitude=${lats}&longitude=${lons}&current=wave_height,surface_temperature&hourly=wave_height&timezone=auto`;
      
      try {
          // Timeout protection
          const controller = new AbortController();
          const t = setTimeout(()=>controller.abort(), 3500); // 3.5s timeout
          
          const resp = await fetch(url, { signal: controller.signal });
          clearTimeout(t);
          if(!resp.ok) throw new Error('API Error');
          const json = await resp.json();
          
          const results = Array.isArray(json) ? json : [json];
          
          const parsed = results.map((r, i) => {
             const loc = LOCATIONS[i];
             const wave = r.current?.wave_height ?? 0;
             const temp = r.current?.surface_temperature ?? 0;
             const hourly = r.hourly?.wave_height || []; 
             const spark = hourly.slice(0, 24); 
             return { 
                 name: loc.name, 
                 label: loc.label, 
                 wave, 
                 temp,
                 spark
             };
          });
          
          return { items: parsed, source: 'Open-Meteo' };
      } catch (e) {
          console.warn('[RealtimeCity] Fetch failed, using fallback', e);
          return fallbackData();
      }
  }

  function fallbackData(){
      return {
          items: LOCATIONS.map(l => ({
              name: l.name,
              label: l.label,
              wave: +(0.5 + Math.random()*2.5).toFixed(1),
              temp: +(15 + Math.random()*15).toFixed(1),
              spark: Array(24).fill(0).map(()=> +(0.5 + Math.random()*1.5).toFixed(1))
          })),
          source: 'Simulated (Network Unavailable)'
      };
  }

  // Persistent active state
  let selectedCityName = null;

  function render(){
      if(!lastData) return;
      
      const { items, source } = lastData;
      if(footnote) {
          footnote.textContent = "Data Source: " + source;
          footnote.style.color = source.includes('Simulated') ? "rgba(255, 179, 71, 0.9)" : "rgba(142, 223, 255, 0.9)";
      }

      // Sort by chosen mode
      const sorted = [...items].sort((a,b) => mode==='wave' ? b.wave - a.wave : b.temp - a.temp);
      const displayItems = sorted.slice(0, 8); // Always show up to 8

      // Determine height availability
      const hostH = host.getBoundingClientRect().height || 300;
      const headerH = host.querySelector('.panel-title')?.offsetHeight || 30;
      const toolH = host.querySelector('.rt-toolbar')?.offsetHeight || 30;
      // We increased chart height, so allow less space for list
      const sparkR_H = 160; 
      const footH = 20;
      let listMaxH = hostH - (headerH + toolH + sparkR_H + footH + 20);
      listMaxH = Math.max(80, listMaxH); 

      // Reset list only if necessary to avoid flicker
      // Using delegation, so simplistic rebuild is fine
      listEl.innerHTML = '';
      listEl.style.maxHeight = listMaxH + 'px';
      listEl.style.overflowY = 'auto';

      if(!selectedCityName && displayItems.length > 0) selectedCityName = displayItems[0].name;
      if(displayItems.length > 0 && !displayItems.find(i=>i.name===selectedCityName)){
          selectedCityName = displayItems[0].name;
      }

      displayItems.forEach((item, i) => {
           const color = PALETTE[i % PALETTE.length];
           const valDisplay = mode==='wave' ? `${item.wave.toFixed(1)}m` : `${item.temp.toFixed(1)}°C`;
           const secondary = mode==='wave' ? `${item.temp.toFixed(0)}°C` : `${item.wave.toFixed(1)}m`;
           
           const tile = document.createElement('div');
           tile.className='rt-tile';
           tile.dataset.name = item.name; // For delegation
           tile.id = 'rt-tile-' + item.name;
           
           const isSelected = item.name === selectedCityName;
           const borderStyle = isSelected ? 'rgba(76, 201, 240, 0.6)' : 'rgba(255,255,255,0.08)';
           const bgStyle = isSelected ? 'rgba(76, 201, 240, 0.1)' : 'rgba(255,255,255,0.03)';

           tile.style.cssText=`position:relative;z-index:10;display:flex;flex-direction:column;gap:2px;padding:6px 8px;border:1px solid ${borderStyle};border-radius:6px;background:${bgStyle};cursor:pointer;margin-bottom:4px;transition:all 0.2s;`;
           
           tile.innerHTML = `
             <div style="display:flex;justify-content:space-between;align-items:center;pointer-events:none;">
                <span style="font-size:11px;font-weight:600;color:#e1f5fe;display:flex;align-items:center;gap:5px;flex:1;min-width:0;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;">
                   <span style="width:6px;height:6px;border-radius:50%;background:${color};flex-shrink:0;"></span>${item.label}
                </span>
                <span style="font-size:11px;font-weight:bold;color:${mode==='wave'?'#4cc9f0':'#ff6b6b'};flex-shrink:0;white-space:nowrap;margin-left:8px;">${valDisplay}</span>
             </div>
             <div style="font-size:9px;color:rgba(255,255,255,0.5);text-align:right;pointer-events:none;">
                ${mode==='wave'?'Temp:':'Wave:'} ${secondary}
             </div>
           `;
           listEl.appendChild(tile);
      });
      
      if(selectedCityName) {
          const activeItem = displayItems.find(i=>i.name===selectedCityName);
          if(activeItem) updateSpark(activeItem);
      }
  }

  // Event Delegation for robustness
  listEl.addEventListener('click', (e) => {
      const tile = e.target.closest('.rt-tile');
      if(!tile) return;
      
      // Stop card expansion
      e.stopPropagation();

      const name = tile.dataset.name;
      if(name && lastData) {
          console.log('[RealtimeCity] Switch to ->', name);
          selectedCityName = name;
          updateListHighlight();
          
          const item = lastData.items.find(i=>i.name===name);
          if(item) updateSpark(item);
      }
  });

  function updateListHighlight(){
      [...listEl.children].forEach(tile => {
          const isSel = tile.id === 'rt-tile-' + selectedCityName;
          tile.style.borderColor = isSel ? 'rgba(76, 201, 240, 0.6)' : 'rgba(255,255,255,0.08)';
          tile.style.background = isSel ? 'rgba(76, 201, 240, 0.1)' : 'rgba(255,255,255,0.03)';
      });
  }

  function updateSpark(item){
      if(!item || !item.spark) return;
      if(focusCountryEl) focusCountryEl.textContent = item.label;
      const unit = mode==='wave' ? ' m' : ' °C';
      const val = mode==='wave' ? item.wave : item.temp;
      if(focusDeltaEl) focusDeltaEl.textContent = (val!==undefined?val.toFixed(1):'--') + unit;
      
      if(!sparkCanvas) return;
      // Ensure Chart.js loaded
      if(typeof Chart === 'undefined') return;

      const ctx = sparkCanvas.getContext('2d');
      const existing = Chart.getChart(sparkCanvas);
      if(existing) existing.destroy();
      
      const labels = item.spark.map((_,i)=>i+'h');
      
      // Force chart styling
      sparkCanvas.style.display = 'block';
      sparkCanvas.style.width = '100%';

      sparkChart = new Chart(ctx, {
          type: 'line',
          data: {
              labels: labels,
              datasets: [{
                  data: item.spark,
                  borderColor: '#4cc9f0',
                  borderWidth: 2,
                  backgroundColor: 'rgba(76, 201, 240, 0.2)',
                  fill: true,
                  tension: 0.4,
                  pointRadius: 0
              }]
          },
          options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: { legend:{display:false}, tooltip:{mode:'index',intersect:false} },
              scales: { 
                  x: { 
                      display: true,
                      grid: { display:false, drawBorder:true, borderColor:'rgba(255,255,255,0.1)' },
                      ticks: { color: 'rgba(255,255,255,0.5)', font: { size: 9 }, maxTicksLimit: 6 }
                  }, 
                  y: { 
                      display: true,
                      grid: { color: 'rgba(255,255,255,0.05)' },
                      ticks: { color: 'rgba(255,255,255,0.5)', font: { size: 9 } } 
                  } 
              },
              animation: { duration: 0 } 
          }
      });
  }

  async function reload(){
      setStatus('Updating...','#ffd700');
      lastData = await fetchMarineData();
      render();
      setStatus('Live','#00ff88');
  }

  // Bind buttons
  modeBtns.forEach(b => {
      b.onclick = (e) => { // Use onclick property for simpler overwrite
          modeBtns.forEach(x=>x.classList.remove('active'));
          b.classList.add('active');
          mode = b.dataset.mode === 'top5' ? 'wave' : 'temp';
          render();
      };
  });

  // Init
  reload();
  setInterval(reload, REFRESH_MS);
  
  window.addEventListener('resize', ()=>render());

})();
