// realtime-city.js  国家误管理实时概览组件 (piece-6)
// 功能: 定时(60s)从 dataService 获取最新 summary / time series, 生成 Top5/Top8 瓷砖 + 迷你趋势 sparkline。
// 离线(file:// 或接口失败) -> 使用内置模拟数据 (保持结构稳定)。
// 公开 API: window.realtimeCity.reload(), window.realtimeCity.setMode(mode)
(function(){
  const host=document.querySelector('[data-key="city"][data-embed="realtime-city"]');
  if(!host) return;
  const listEl=host.querySelector('#rt-country-list');
  const sparkCanvas=document.getElementById('rt-mini-spark');
  const statusText=document.getElementById('rt-status-text');
  const dot=host.querySelector('.rt-dot');
  const focusCountryEl=document.getElementById('rt-focus-country');
  const focusDeltaEl=document.getElementById('rt-focus-delta');
  const modeBtns=[...host.querySelectorAll('.rt-mode-btn')];
  const refreshBtn=document.getElementById('rt-refresh-btn');
  let mode='auto';
  const PALETTE=['#ff6b6b','#4ecdc4','#ffe66d','#6a5acd','#ff6b9d','#a8dadc','#6a5acd99','#4dabf7'];
  let timer=null; let lastData=null; let sparkChart=null;
  const REFRESH_MS=60000; // 60s

  function setStatus(s,color){ if(statusText){ statusText.textContent=s; } if(dot){ dot.style.background=color; } }

  function chooseMode(list){
    if(mode==='top5'||mode==='top8') return mode;
    // 使用实际容器高度（若未渲染取 CSS 最小值 300）估算可显示数量
    const hostH = host.getBoundingClientRect().height || 300;
    // 估算单 tile 高度 ~44px，头部/工具栏/火花/底部及内边距预留 ~150px
    const remain = hostH - 150;
    const capacity = Math.floor(remain / 44);
    return capacity >= 8 && list.length>=8 ? 'top8' : 'top5';
  }
  function fakeSummary(){
    // 8 国模拟 (单位: 吨 mismanaged) 数值在 5e6~2.2e7
    const names=['China','United States','India','Indonesia','Brazil','Philippines','Vietnam','Turkey'];
    return names.map((n,i)=>({country:n, mismanaged: (5e6 + (names.length-i)*1.6e6) * (1+Math.random()*0.15)}));
  }
  function fakeSeries(){
    const years=[]; const now=new Date().getFullYear();
    for(let y=now-24;y<=now;y++) years.push(y);
    const vals=years.map((_,i)=> +(40 + i*0.8 + Math.sin(i/3)*2 + (Math.random()-0.5)*1.4).toFixed(2));
    return {years, values:vals};
  }
  async function fetchData(){
    const offline= window.__FILE_MODE__ || !window.dataService;
    if(offline){ return { summary: fakeSummary(), series: fakeSeries() }; }
    try{
      const [sumRes, tsRes]= await Promise.all([
        window.dataService.getPlasticWasteSummary({forceRefresh:false}),
        window.dataService.getPlasticWasteTimeSeries({forceRefresh:false})
      ]);
      if(!Array.isArray(sumRes?.data) || !tsRes?.data?.years) throw new Error('结构不完整');
      return { summary: sumRes.data, series: tsRes.data };
    }catch(e){ console.warn('[RealtimeCity] 远程失败，使用模拟',e); return { summary: fakeSummary(), series: fakeSeries(), fallback:true }; }
  }
  function render(){
    if(!lastData) return;
    const { summary, series }=lastData;
    const m=chooseMode(summary);
    const slice= summary.slice(0, m==='top5'?5:8).map((r,i)=>({...r, rank:i+1}));
    const enlarged = host.classList.contains('panel-enlarging');
    if(enlarged){
      // 放大态：清除任何内联高度，允许 CSS 扩展
      host.style.minHeight='';
      host.style.height='';
    } else {
      // 普通态：不再强制写死高度，交给 CSS min-height 控制
      host.style.height='';
      host.style.minHeight='';
    }
    // 使用真实高度；若未渲染高度不足（可能初次），用 CSS 最小高度 300 代替
    const hostH = host.getBoundingClientRect().height || 300;
    // 获取各结构实际高度（若不存在则为 0）
    const headerH = host.querySelector('.panel-title')?.offsetHeight || 0;
    const toolbarH = host.querySelector('.rt-toolbar')?.offsetHeight || 0;
    const sparkRow = document.getElementById('rt-spark-row');
    const sparkH = sparkRow ? sparkRow.offsetHeight : 0;
    const footH = host.querySelector('.panel-info')?.offsetHeight || 0;
    // 估算垂直内边距 (上下 padding + 间隙) 保守取 24
    const paddingReserve = 24;
    let maxList = hostH - (headerH + toolbarH + sparkH + footH + paddingReserve);
    // 留出最小高度兜底 & 放大态上限不强制（由容器滚动）
    maxList = Math.max(80, maxList);
    listEl.style.maxHeight = maxList + 'px';
    listEl.style.overflow = 'auto';
    listEl.innerHTML='';
    const total = summary.reduce((a,b)=>a+(b.mismanaged||0),0) || 1;
    slice.forEach((r,i)=>{
      const pctGlobal = r.mismanaged/total*100;
      const tile=document.createElement('div');
      tile.className='rt-tile';
      tile.style.cssText='position:relative;display:flex;flex-direction:column;gap:2px;padding:5px 8px 5px 6px;border:1px solid rgba(255,255,255,0.10);border-radius:9px;background:linear-gradient(135deg,rgba(255,255,255,0.045),rgba(255,255,255,0.02));font-size:11px;min-width:0;cursor:pointer;transition:background .25s,border-color .25s;';
      const color=PALETTE[i%PALETTE.length];
      tile.innerHTML=`<div style="display:flex;align-items:center;gap:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
         <span style=\"width:12px;height:12px;border-radius:4px;background:${color};box-shadow:0 0 0 1px rgba(0,0,0,.4) inset;\"></span>
         <span style=\"color:#e2f9ff;font-weight:600;letter-spacing:.35px;\">${r.rank}. ${r.country.replace(/\s*\(.*\)/,'')}</span>
       </div>
       <div style=\"display:flex;gap:6px;justify-content:space-between;align-items:center;font-size:10px;\">
         <span style=\"color:#ffce99;font-weight:600;\">${(r.mismanaged/1e6).toFixed(2)}Mt</span>
         <span style=\"color:#9dd4e8;\">${pctGlobal.toFixed(1)}%</span>
       </div>`;
      tile.addEventListener('click',()=>focusCountry(r));
      listEl.appendChild(tile);
    });
    const label=document.getElementById('rt-mode-label'); if(label) label.textContent= (mode==='auto'? 'Auto·'+ (m==='top8'?'Top8':'Top5') : (mode==='top8'?'Top8':'Top5'));
    modeBtns.forEach(b=> b.classList.toggle('active', b.dataset.mode===mode));
    buildSpark(series);
  }
  function focusCountry(rec){
    if(!rec) return;
    focusCountryEl.textContent=rec.country;
    // 模拟 delta：最近值相对 15 年前差异 (使用 series)
    if(lastData?.series?.values?.length>=16){
      const vals=lastData.series.values;
      const delta = vals[vals.length-1] - vals[vals.length-16];
      focusDeltaEl.textContent = (delta>=0?'+':'') + delta.toFixed(1);
    }
  }
  function buildSpark(ts){
    if(!sparkCanvas || !ts?.years) return;
    const labels=ts.years.slice(-30).map(String);
    const data=ts.values.slice(-30);
    if(!window.Chart){ return; }
    if(sparkChart){ sparkChart.data.labels=labels; sparkChart.data.datasets[0].data=data; sparkChart.update(); return; }
    sparkChart=new Chart(sparkCanvas,{type:'line',data:{labels,datasets:[{data, borderColor:'rgba(255,190,120,1)', backgroundColor:'rgba(255,190,120,0.15)', tension:.3, fill:true, borderWidth:2, pointRadius:0}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{display:false},y:{display:false}}}});
  }
  async function reload(){
    setStatus('更新中...','#ffb347');
    const data=await fetchData();
    lastData=data; setStatus(data.fallback? '模拟':'在线','#3ddc97');
    render();
  }
  function schedule(){ clearInterval(timer); timer=setInterval(()=>reload(), REFRESH_MS); }
  // 事件绑定
  refreshBtn.addEventListener('click',()=>reload());
  modeBtns.forEach(btn=> btn.addEventListener('click',()=>{ mode=btn.dataset.mode; reload(); }));
  // Panel 放大时重新渲染 (确保 auto 模式尺寸变化)
  // 旧的自定义事件可能不存在，这里改用 MutationObserver 监听 class 变化（进入/退出放大）
  const mo = new MutationObserver(muts=>{
    for(const m of muts){
      if(m.type==='attributes' && m.attributeName==='class'){
        if(host.classList.contains('panel-enlarging')){
          // 放大后延迟重新计算一次高度
          setTimeout(()=>render(), 90);
        } else {
          // 关闭放大后恢复固定高度再渲染（避免高度残留）
          setTimeout(()=>render(), 60);
        }
      }
    }
  });
  mo.observe(host, {attributes:true, attributeFilter:['class']});

  window.realtimeCity={ reload, setMode:(m)=>{ mode=m; render(); }, _get:()=>lastData };
  // 等 Chart.js 后再初始 (为 spark)；若已经加载立即执行
  function initWhenReady(){ if(window.Chart){ reload(); schedule(); } else setTimeout(initWhenReady,200); }
  initWhenReady();
})();
