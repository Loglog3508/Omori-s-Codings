// utils.js - 公共工具 (轻量, 纯前端) 2025-09
// 说明: 所有新页面优先使用这里的通用函数；保持无依赖，可在 file:// 下运行
;(function(global){
  if(global.__UTILS__) return; // 防重复
  const U = {};
  U.version = '0.1.0';
  U.log = (...a)=>console.log('[UTIL]',...a);
  U.warn = (...a)=>console.warn('[UTIL]',...a);
  U.formatBytes = function(bytes){ if(isNaN(bytes)) return '-'; const units=['B','KB','MB','GB']; let i=0; while(bytes>=1024&&i<units.length-1){ bytes/=1024; i++; } return bytes.toFixed(bytes>=10?1:2)+' '+units[i]; };
  U.formatTime = ts=>{ try{ const d = ts? new Date(ts): new Date(); return d.toISOString().replace('T',' ').split('.')[0]; }catch(e){ return String(ts); } };
  U.loadScript = function(src, opts={}){ return new Promise((res,rej)=>{ if(!src){ rej('empty src'); return; } if(document.querySelector('script[data-inline-loaded="'+src+'"]')) return res(); const s=document.createElement('script'); s.src=src; s.async=opts.async!==false; s.dataset.inlineLoaded=src; s.onload=()=>res(); s.onerror=()=>rej(new Error('load fail '+src)); document.head.appendChild(s); }); };
  U.ensureChartJS = async function(){ 
    if(typeof Chart!=='undefined') return true; 
    const sources=[
        'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js',
        'https://unpkg.com/chart.js@4.4.1/dist/chart.umd.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js'
    ];
    for(const src of sources){
        try{ await U.loadScript(src); if(typeof Chart!=='undefined') return true; }catch(e){ U.warn('Chart CDN fail:',src); }
    }
    return false; 
  };
  U.linearRegression = function(xs, ys){ // 简单最小二乘
    const n = Math.min(xs.length, ys.length); if(n===0) return {m:0,b:0};
    let sumX=0,sumY=0,sumXY=0,sumXX=0; for(let i=0;i<n;i++){ const x=xs[i], y=ys[i]; sumX+=x; sumY+=y; sumXY+=x*y; sumXX+=x*x; }
    const m = (n*sumXY - sumX*sumY)/(n*sumXX - sumX*sumX || 1);
    const b = (sumY - m*sumX)/n;
    return {m,b, predict:x=>m*x+b};
  };
  U.rand = (min,max)=>Math.random()*(max-min)+min;
  U.seededRand = function(seed){ let x = Math.sin(seed||1)*10000; return x - Math.floor(x); };
  U.createFallback = function(parent, msg, extra){ const d=document.createElement('div'); d.className='fallback-box'; d.innerHTML='<div class="fb-msg">'+msg+'</div>'+(extra||''); parent.appendChild(d); return d; };
  // 简易事件总线（小型页面通信）
  const bus = {}; U.on=(ev,fn)=>{ (bus[ev]=bus[ev]||[]).push(fn); }; U.emit=(ev,data)=>{ (bus[ev]||[]).forEach(f=>{ try{ f(data); }catch(e){ U.warn(e);} }); };
  global.__UTILS__ = U;
})(window);

// 简易样式（如果主样式缺失时的后备）
;(function injectFallbackCSS(){ if(document.getElementById('utils-fallback-style')) return; const css = `
.fallback-box{padding:12px 16px;margin:8px 0;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.15);backdrop-filter:blur(6px);border-radius:10px;color:#d9e6f2;font-size:13px;}
.inline-note{font-size:12px;opacity:.75;margin-left:6px}
.panel-grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));margin-top:16px}
.card{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);padding:14px 18px;border-radius:14px;backdrop-filter:blur(8px);position:relative;overflow:hidden}
.card h3{margin:0 0 8px;font-size:15px;letter-spacing:.5px}
.param-row{display:flex;align-items:center;gap:8px;margin:6px 0;font-size:12px}
.param-row input[type=range]{flex:1}
.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}
canvas.lab-canvas{width:100%;height:260px;background:#020b14;border:1px solid rgba(255,255,255,0.08);border-radius:12px}
table.basic{width:100%;border-collapse:collapse;font-size:12px}
table.basic td,table.basic th{border:1px solid rgba(255,255,255,0.15);padding:4px 6px;text-align:center}
section.step{min-height:80vh;display:flex;flex-direction:column;justify-content:center;padding:40px 10%;position:relative}
section.step:nth-child(odd){background:linear-gradient(135deg,#031726,#062d44)}
section.step:nth-child(even){background:linear-gradient(135deg,#042234,#06344d)}
section.step h2{margin:0 0 12px;font-size:34px;letter-spacing:1px}
section.step p{max-width:780px;line-height:1.55;font-size:16px}
.step[data-active='true']{box-shadow:0 0 0 2px rgba(0,200,255,0.25) inset}
`; const style=document.createElement('style'); style.id='utils-fallback-style'; style.textContent=css; document.head.appendChild(style);} )();
