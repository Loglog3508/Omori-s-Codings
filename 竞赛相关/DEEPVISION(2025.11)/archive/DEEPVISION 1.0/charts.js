// 重建后的简化 ChartManager（单一定义）
class ChartManager {
  constructor(){
    this.charts={};
    this._overlays=new Map();
    if(typeof window.Chart==='undefined'){
      console.warn('[ChartManager] Chart.js 未就绪，等待 chart-ready 事件...');
      document.addEventListener('chart-ready',()=>this.init(),{once:true});
    } else {
      this.init();
    }
    try { window.chartManager=this; } catch(e){}
  }
  init(){
    if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',()=>this.safeCreateCharts());
    else this.safeCreateCharts();
  }
  safeCreateCharts(){
    if(typeof window.Chart==='undefined') return setTimeout(()=>this.safeCreateCharts(),250);
    this.createCharts();
  }
  createCharts(){
    this.createDensityChart();
    this.createSourceChart();
    this.createTrendChart();
  // 已移除物种分类面板，跳过 createSpeciesImpactChart()
    this.createMarineBioLossChart();
    this.createWaterQualityChart();
  this.createRubbishChart();
    this.createOceanCurrentChart();
    setTimeout(()=>window.dispatchEvent(new Event('resize')),300);
  }
  /* -------- 通用工具 -------- */
  showLoadingOverlay(canvas,text='加载中...'){
    try{const p=canvas.parentElement; if(!p) return; p.style.position=p.style.position||'relative';
      const div=document.createElement('div'); div.className='chart-loading-overlay';
      div.style.cssText='position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.28);color:#a8dadc;font-size:12px;font-family:Roboto;letter-spacing:.5px;z-index:10;backdrop-filter:blur(2px)';
      div.textContent=text; p.appendChild(div); this._overlays.set(canvas,div);
    }catch(e){}}
  hideLoadingOverlay(canvas){ const ov=this._overlays.get(canvas); if(ov&&ov.parentElement) ov.parentElement.removeChild(ov); this._overlays.delete(canvas);} 
  appendDataNote(canvas,note){ try{const p=canvas.parentElement; if(!p||p.querySelector('.data-note')) return; p.style.position=p.style.position||'relative'; const n=document.createElement('div'); n.className='data-note'; n.style.cssText='position:absolute;left:6px;bottom:4px;font-size:10px;color:#89c2d9;opacity:.8;font-family:Roboto;pointer-events:none;'; n.textContent=note; p.appendChild(n);}catch(e){} }
  /* -------- 占位图表 -------- */
  createDensityChart(){ const ctx=document.getElementById('density-chart'); if(!ctx) return; this.charts.density=new Chart(ctx,{type:'bar',data:{labels:['北太平洋','北大西洋','印度洋','南太平洋','南大西洋'],datasets:[{label:'塑料密度 kg/km²',data:[8.5,3.2,2.8,2.1,1.9],backgroundColor:'rgba(77,171,247,0.6)',borderColor:'rgba(77,171,247,1)',borderWidth:2,borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#a8dadc'}}},scales:{x:{ticks:{color:'#a8dadc'},grid:{color:'rgba(168,218,220,0.15)'}},y:{ticks:{color:'#a8dadc'},grid:{color:'rgba(168,218,220,0.15)'}}}}}); }
  createSourceChart(){
    const ctx=document.getElementById('source-chart'); if(!ctx) return;
    // 数据优先从 dataService.getSourceAttribution() 获取；失败再回退静态默认
    let labels=['河流与陆源输入','沿海径流','渔业与渔具','航运活动','旅游与海滩','其他'];
    let data=[40,22,16,8,7,7];
    const palette=['rgba(255,107,107,0.8)','rgba(78,205,196,0.8)','rgba(255,230,109,0.8)','rgba(255,107,157,0.8)','rgba(168,218,220,0.8)','rgba(106,90,205,0.8)'];
    if(window.dataService?.getSourceAttribution){
      window.dataService.getSourceAttribution().then(res=>{
        try{
          const list=res?.data?.categories; if(Array.isArray(list)&&list.length){
            labels=list.map(i=>i.name); data=list.map(i=>i.percent);
            if(this.charts.source){ this.charts.source.data.labels=labels; this.charts.source.data.datasets[0].data=data; this.charts.source.update(); }
          }
        }catch(e){ console.warn('[SourceChart] 动态来源数据解析失败',e); }
      }).catch(e=>console.warn('[SourceChart] 来源数据获取失败',e));
    }
    // 如果已经存在则只更新，避免重复 new 引发 Canvas is already in use
    if(this.charts.source){
      this.charts.source.data.labels=labels;
      this.charts.source.data.datasets[0].data=data;
      this.charts.source.data.datasets[0].backgroundColor=palette;
      this.charts.source.data.datasets[0].borderColor=palette.map(c=>c.replace('0.8','1'));
      this.charts.source.update();
      return;
    }
    this.charts.source=new Chart(ctx,{
      type:'doughnut',
      data:{labels,datasets:[{data,backgroundColor:palette,borderColor:palette.map(c=>c.replace('0.8','1')),borderWidth:2}]},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{color:'#a8dadc'}}},cutout:'60%'}
    });
  }
  async createTrendChart(){
    const ctx=document.getElementById('trend-chart'); if(!ctx) return;
    // 先放占位，后续替换
    if(!this.charts.trend){
      this.charts.trend=new Chart(ctx,{type:'line',data:{labels:['…'],datasets:[{label:'加载中…',data:[0],borderColor:'rgba(255,230,109,1)',backgroundColor:'rgba(255,230,109,0.18)',tension:.35,fill:true,borderWidth:3,pointRadius:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#a8dadc'}}},scales:{x:{ticks:{color:'#a8dadc'}},y:{ticks:{color:'#a8dadc'}}}}});
    }
    if(!window.dataService){ console.warn('[Trend] dataService 缺失，使用占位'); return; }
    try{
      const res=await window.dataService.getPlasticWasteTimeSeries({forceRefresh:false});
      const ts=res?.data; if(!ts?.years||!ts?.values){ throw new Error('结构缺失'); }
      let years=ts.years.slice(); let vals=ts.values.slice();
      // 年度筛选：截断到所选年份（若存在）
      const selYearStr=window.__wallFilters?.['filter-year'];
      const selYear=selYearStr? parseInt(selYearStr,10):null;
      if(selYear && years.includes(selYear)){
        const idx=years.indexOf(selYear);
        years=years.slice(Math.max(0,idx-29), idx+1); // 仍保持最多30年窗口
        vals=vals.slice(Math.max(0,idx-29), idx+1);
      } else {
        years=years.slice(-30); vals=vals.slice(-30);
      }
      // 季度筛选：简单按比例对最后一年末值做线性分摊（模拟 Q1/Q2/Q3 部分增长，Q4=完整）
      const q=window.__wallFilters?.['filter-quarter'];
      if(q && ['Q1','Q2','Q3'].includes(q) && vals.length){
        const frac={Q1:0.25,Q2:0.50,Q3:0.75}[q];
        vals=vals.slice(); vals[vals.length-1]=+(vals[vals.length-1]*frac).toFixed(2);
      }
      const ch=this.charts.trend; ch.data.labels=years.map(String); ch.data.datasets[0].data=vals; ch.data.datasets[0].label='全球误管理塑料 (百万吨)'+(q&&q!=='Q4'?` - ${q} 估算`:''); ch.update(); this.appendDataNote(ctx,'来源: OWID MISMANAGED PLASTIC');
    }catch(err){ console.warn('[Trend] 获取失败，保留占位',err); }
  }
  async createSpeciesImpactChart(){
    const ctx=document.getElementById('species-impact-chart'); if(!ctx) return;
    if(!this.charts.speciesImpact){
      this.charts.speciesImpact=new Chart(ctx,{type:'bar',data:{labels:['…'],datasets:[{label:'加载中…',data:[0],backgroundColor:'rgba(106,90,205,0.75)',borderColor:'rgba(106,90,205,1)',borderWidth:2,borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#a8dadc'}}},scales:{x:{ticks:{color:'#a8dadc'}},y:{ticks:{color:'#a8dadc'}}}}});
    }
    if(!window.dataService){ console.warn('[SpeciesImpact] dataService 缺失'); return; }
    try{
      const res=await window.dataService.getBiodiversityComposition({forceRefresh:false});
      const list=res?.data; if(!Array.isArray(list) || !list.length) throw new Error('空数据');
      const top=list.slice(0,5);
      const labels=top.map(i=> i.taxonRank|| i.scientificName || '—');
      const values=top.map(i=> i.count || 0);
      const ch=this.charts.speciesImpact; ch.data.labels=labels; ch.data.datasets[0].data=values; ch.data.datasets[0].label='物种分类出现数量 (OBIS)'; ch.update(); this.appendDataNote(ctx,'来源: OBIS 物种记录 (Top5)');
    }catch(err){ console.warn('[SpeciesImpact] 获取失败，保留占位',err); }
  }
  async createMarineBioLossChart(){
    const ctx=document.getElementById('marine-bio-loss-chart'); if(!ctx) return;
    // 初始化占位图
    if(!this.charts.marineBioLoss){
      this.charts.marineBioLoss=new Chart(ctx,{type:'bar',data:{labels:['…'],datasets:[{label:'加载中…',data:[0],backgroundColor:'rgba(255,107,157,0.60)',borderColor:'rgba(255,107,157,1)',borderWidth:2,borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#a8dadc'}}},scales:{x:{ticks:{color:'#a8dadc'}},y:{ticks:{color:'#a8dadc'}}}}});
    }
    try{
      let usedSource='cities-api';
      let latestYear;
      let entries=[];
      // 优先调用数据服务（未来可替换为真实 OBIS 聚合）
      if(window.dataService?.getCoastalCityBiodiversityLoss){
        const apiRes=await window.dataService.getCoastalCityBiodiversityLoss({forceRefresh:false});
        const list=apiRes?.data;
        if(Array.isArray(list) && list.length){
          latestYear=Math.max(...list.map(r=>r.year||0));
          const latest=list.filter(r=>r.year===latestYear);
          // 展开 groups -> city-cat-loss
          latest.forEach(r=>{ if(r.groups){ Object.entries(r.groups).forEach(([cat,val])=>{ if(isFinite(val)) entries.push({city:r.city,cat,loss:val}); }); } });
        }
      }
      // 如果服务为空则回退 CSV
      if(!entries.length){
        usedSource='csv';
        let text;
        if(window.__FILE_MODE__){
          text=`城市,年份,生物类别,减少数量\n示例市,2025,珊瑚,120\n示例市,2025,鱼类,95\n示例市,2025,海洋植物,140`;
        } else {
            const resp=await fetch('china_coastal_marine_bio_loss.csv');
            if(!resp.ok) throw new Error('无法读取CSV');
            text=await resp.text();
        }
        const lines=text.split(/\r?\n/).filter(l=>l.trim());
        if(lines.length>1){
          const headerRaw=lines[0].split(',');
          const header=headerRaw.map(s=>s.trim().toLowerCase());
          function findIdx(cands){ return header.findIndex(h=> cands.some(k=> h===k || h.includes(k))); }
          const cityIdx=findIdx(['城市','city','区域','region']);
          const yearIdx=findIdx(['年份','year']);
          const catIdx=findIdx(['生物类别','类别','category','class']);
          const lossIdx=findIdx(['减少数量','减少','loss','value','数量']);
          if(cityIdx>-1 && yearIdx>-1 && catIdx>-1 && lossIdx>-1){
            const rows=[]; for(let i=1;i<lines.length;i++){ const cols=lines[i].split(','); if(cols.length<headerRaw.length) continue; const city=cols[cityIdx].trim(); const year=parseInt(cols[yearIdx],10); const cat=cols[catIdx].trim(); const loss=parseFloat(cols[lossIdx]); if(!city||!cat||!isFinite(year)||!isFinite(loss)) continue; rows.push({city,year,cat,loss}); }
            if(rows.length){ latestYear=Math.max(...rows.map(r=>r.year)); const subset=rows.filter(r=>r.year===latestYear); const agg=new Map(); subset.forEach(r=>{ const key=r.city+'|'+r.cat; agg.set(key,(agg.get(key)||0)+r.loss); }); entries=[...agg.entries()].map(([k,v])=>{ const [city,cat]=k.split('|'); return {city,cat,loss:v}; }); }
          }
        }
      }
      if(!entries.length) throw new Error('无有效数据');
      entries.sort((a,b)=>b.loss-a.loss); entries=entries.slice(0,8);
      const labels=entries.map(e=> e.city+'-'+e.cat);
      const values=entries.map(e=> +e.loss.toFixed(0));
      const ch=this.charts.marineBioLoss; ch.data.labels=labels; ch.data.datasets[0].data=values; ch.data.datasets[0].label=`沿海城市生物类群减少(${latestYear||'—'})`; ch.update();
      const note= usedSource==='csv' ? '来源: 本地CSV Top8 (最新年份)' : '来源: 数据服务(模拟 OBIS 聚合) Top8';
      this.appendDataNote(ctx,note);
    }catch(err){ console.warn('[MarineBioLoss] 加载失败，使用占位',err); }
  }
  async createWaterQualityChart(){
    const ctx=document.getElementById('water-quality-chart'); if(!ctx) return;
    if(!this.charts.waterQuality){
      this.charts.waterQuality=new Chart(ctx,{type:'bar',data:{labels:['…'],datasets:[{label:'加载中…',data:[0],backgroundColor:'rgba(78,205,196,0.65)',borderColor:'rgba(78,205,196,1)',borderWidth:2,borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#a8dadc'}}},scales:{x:{ticks:{color:'#a8dadc'}},y:{ticks:{color:'#a8dadc'}}}}});
    }
    if(!window.dataService){ console.warn('[WaterQuality] dataService 缺失'); return; }
    try{
      const res=await window.dataService.getCoastalWaterQuality({forceRefresh:false});
      const metrics=res?.data?.metrics; if(!metrics) throw new Error('缺少 metrics');
      const mapLabels={ chlorophyll:'叶绿素(mg/m³)', sst:'SST(°C)', turbidity:'浊度(NTU)', oxygen:'溶解氧(mg/L)' };
      const labels=Object.keys(metrics).map(k=> mapLabels[k]||k);
      const values=Object.values(metrics).map(v=> +(+v).toFixed(2));
      const ch=this.charts.waterQuality; ch.data.labels=labels; ch.data.datasets[0].data=values; ch.data.datasets[0].label='近岸水质关键指标'; ch.update(); this.appendDataNote(ctx,'来源: 模拟/接口近岸水质 (Coastal Water)');
    }catch(err){ console.warn('[WaterQuality] 获取失败，保留占位',err); }
  }
  /* -------- 真实数据：OWID 垃圾 -------- */
  async createRubbishChart(updateOnly=false){
    if(this._busyRubbish){ this._pendingRubbish=true; return; }
    this._busyRubbish=true;
    const yearlyCtx=document.getElementById('rubbish-yearly-chart');
  const yearlyMiniCtx=document.getElementById('rubbish-yearly-mini-chart');
  const yoyCanvas=document.getElementById('rubbish-yearly-yoy-chart');
  const forecastTableDiv=document.getElementById('rubbish-forecast-table');
    const barCtx=document.getElementById('rubbish-city-bar-chart');
    // 主页面才存在的占比饼图 canvas；数据大屏 display_wall.html 没有该元素 -> 自动跳过
    const pieCtx=document.getElementById('rubbish-city-chart');
    // 如果城市面板已被外部嵌入 iframe 替换（data-embed=external-city），跳过城市 TopN 图的创建
    const cityEmbedHost=document.querySelector('[data-key="city"][data-embed="external-city"]');
    const skipCityCharts= !!cityEmbedHost;
    if(!yearlyCtx && !barCtx) return;
    if(!window.dataService){ console.warn('[RubbishChart] dataService 缺失'); return; }
    if(yearlyCtx) this.showLoadingOverlay(yearlyCtx,'加载趋势...');
  // 仅柱状图模式
    try{
      const [tsRes,summaryRes]=await Promise.all([
        window.dataService.getPlasticWasteTimeSeries({forceRefresh:updateOnly}),
        window.dataService.getPlasticWasteSummary({forceRefresh:updateOnly})
      ]);
      if(yearlyCtx && tsRes?.data?.years){
        // ========== 新增：范围 + 移动均值 + 预测 + 同比（YoY） + 迷你图 ==========
        const allYears=tsRes.data.years.slice();
        const allVals=tsRes.data.values.slice();
        // 读取控制项
        const rangeSel=document.getElementById('rubbish-range');
        const maChk=document.getElementById('rubbish-ma');
        const forecastChk=document.getElementById('rubbish-forecast');
        const yoyChk=document.getElementById('rubbish-yoy');
        const range=parseInt(rangeSel?.value||'20',10);
        const years=allYears.slice(-range);
        const vals=allVals.slice(-range);
        // 同比序列 (单独图 + 可叠加 y2) -- 叠加保留保证旧逻辑兼容
        let yoySeries=null;
        if(yoyChk && yoyChk.checked && years.length>1){
          yoySeries=vals.map((v,i)=> i===0? null : ( (v - vals[i-1]) / (vals[i-1]||1) * 100 ));
        }
        // 移动均值 (窗口=5)
        let maSeries=null;
        if(maChk && maChk.checked && vals.length>=3){
          const w=5; maSeries=vals.map((_,i)=>{ const start=Math.max(0,i-w+1); const seg=vals.slice(start,i+1); return +(seg.reduce((a,b)=>a+b,0)/seg.length).toFixed(2); });
        }
        // 简单线性回归预测 +5 年（基于选中窗口）
        let forecastYears=[], forecastVals=[];
        if(forecastChk && forecastChk.checked && years.length>=4){
          const n=years.length; const xs=years.map(y=>y); const ys=vals.map(v=>v);
          const xMean=xs.reduce((a,b)=>a+b,0)/n; const yMean=ys.reduce((a,b)=>a+b,0)/n;
          let num=0,den=0; for(let i=0;i<n;i++){ num+=(xs[i]-xMean)*(ys[i]-yMean); den+=(xs[i]-xMean)**2; }
          const slope= den? num/den : 0; const intercept=yMean - slope*xMean;
          const lastYear=years[years.length-1];
          for(let k=1;k<=5;k++){ const fy=lastYear+k; forecastYears.push(fy); forecastVals.push(+(intercept + slope*fy).toFixed(2)); }
        }
        const dsMain={label:'全球误管理塑料 (百万吨)',data:vals,borderColor:'rgba(255,107,107,1)',backgroundColor:'rgba(255,107,107,0.18)',fill:true,tension:.35,borderWidth:3,pointRadius:2};
        const datasets=[dsMain];
        if(maSeries){ datasets.push({label:'移动均值(5)',data:maSeries,borderColor:'rgba(78,205,196,1)',backgroundColor:'rgba(78,205,196,0.0)',fill:false,tension:.25,borderWidth:2,pointRadius:0}); }
        if(forecastVals.length){
          // 将预测衔接 last -> 虚线
          datasets.push({label:'预测(+5)',data:[...new Array(vals.length-1).fill(null), vals[vals.length-1], ...forecastVals],borderColor:'rgba(255,230,109,1)',backgroundColor:'rgba(255,230,109,0.15)',fill:false,tension:.35,borderWidth:2,borderDash:[6,4],pointRadius:0});
        }
  if(yoySeries){ datasets.push({label:'同比(%)',yAxisID:'y2',data:yoySeries,borderColor:'rgba(106,90,205,1)',backgroundColor:'rgba(106,90,205,0.15)',fill:false,tension:.3,borderWidth:2,pointRadius:2}); }
        const labels=[...years];
        if(forecastYears.length){ labels.push(...forecastYears); }
        // 主图创建/更新
        if(this.charts.rubbishYearly){
          this.charts.rubbishYearly.data.labels=labels.map(String);
          this.charts.rubbishYearly.data.datasets=datasets;
          if(this.charts.rubbishYearly.options?.scales?.y2){ this.charts.rubbishYearly.options.scales.y2.display=!!yoySeries; }
          this.charts.rubbishYearly.update();
        } else {
          this.charts.rubbishYearly=new Chart(yearlyCtx,{type:'line',data:{labels:labels.map(String),datasets},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:'#a8dadc',boxHeight:10,boxWidth:22}}},scales:{x:{ticks:{color:'#a8dadc'}},y:{ticks:{color:'#a8dadc'},grid:{color:'rgba(168,218,220,0.15)'}},y2:{display:!!yoySeries,position:'right',grid:{display:false},ticks:{color:'#cdbaff',callback:v=>v+'%'}}}}});
          this.appendDataNote(yearlyCtx,'来源: OWID MISMANAGED PLASTIC');
        }
        // ===== 独立 YoY 柱图 (如果开启) =====
        if(yoyCanvas){ if(!(yoyChk && yoyChk.checked)) { yoyCanvas.style.display='none'; }
          else {
            yoyCanvas.style.display='block';
            const yoyLabels=years.map(String);
            if(!this.charts.rubbishYearlyYoY){
              this.charts.rubbishYearlyYoY=new Chart(yoyCanvas,{type:'bar',data:{labels:yoyLabels,datasets:[{label:'同比%',data:yoySeries.slice(1),backgroundColor:yoySeries.slice(1).map(v=> v>=0?'rgba(78,205,196,0.75)':'rgba(255,107,107,0.75)'),borderColor:yoySeries.slice(1).map(v=> v>=0?'rgba(78,205,196,1)':'rgba(255,107,107,1)'),borderWidth:2,borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#a8dadc',callback:(val,idx)=>yoyLabels[idx+1]||''},grid:{display:false}},y:{ticks:{color:'#a8dadc',callback:v=>v+'%'},grid:{color:'rgba(168,218,220,0.12)'}}}}});
            } else {
              this.charts.rubbishYearlyYoY.data.labels=yoyLabels;
              this.charts.rubbishYearlyYoY.data.datasets[0].data=yoySeries.slice(1);
              const bg=yoySeries.slice(1).map(v=> v>=0?'rgba(78,205,196,0.75)':'rgba(255,107,107,0.75)');
              this.charts.rubbishYearlyYoY.data.datasets[0].backgroundColor=bg;
              this.charts.rubbishYearlyYoY.data.datasets[0].borderColor=bg.map(c=>c.replace('0.75','1'));
              this.charts.rubbishYearlyYoY.update();
            }
          }
        }
        // 迷你图（主序列 + MA 不带预测）
        if(yearlyMiniCtx){
          const miniLabels=years.map(String);
          if(!this.charts.rubbishYearlyMini){
            const miniConfig={
              type:'line',
              data:{
                labels:miniLabels,
                datasets:[
                  { label:'主序列', data:vals, borderColor:'rgba(255,107,107,0.9)', backgroundColor:'rgba(255,107,107,0.0)', tension:.3, borderWidth:1.5, pointRadius:0 },
                  { label:'MA', data:maSeries||vals, borderColor:'rgba(78,205,196,0.9)', backgroundColor:'rgba(78,205,196,0.0)', tension:.25, borderWidth:1, pointRadius:0 }
                ]
              },
              options:{
                responsive:true, maintainAspectRatio:false,
                plugins:{ legend:{ display:false } },
                scales:{ x:{ display:false }, y:{ display:false } },
                elements:{ line:{ spanGaps:true } }
              }
            };
            this.charts.rubbishYearlyMini=new Chart(yearlyMiniCtx,miniConfig);
          } else {
            this.charts.rubbishYearlyMini.data.labels=miniLabels;
            this.charts.rubbishYearlyMini.data.datasets[0].data=vals;
            this.charts.rubbishYearlyMini.data.datasets[1].data=maSeries||vals;
            this.charts.rubbishYearlyMini.update();
          }
        }
        // ===== 预测结果表 =====
        if(forecastTableDiv){ if(!(forecastChk && forecastChk.checked && forecastVals.length)) { forecastTableDiv.style.display='none'; forecastTableDiv.innerHTML=''; }
          else {
            forecastTableDiv.style.display='block';
            const rows=forecastYears.map((y,i)=>{ const base=vals[vals.length-1]; const fv=forecastVals[i]; const inc=((fv-base)/base*100).toFixed(2); return `<tr><td style="text-align:left;color:#e0fbfc;">${y}</td><td>${fv.toFixed(2)}</td><td class="${inc>=0?'positive':'negative'}">${inc}%</td></tr>`; });
            forecastTableDiv.innerHTML=`<table><thead><tr><th style="text-align:left;">年份</th><th>预测值</th><th>较基年%</th></tr></thead><tbody>${rows.join('')}</tbody></table>`;
          } }
        // ===== KPI 统计 (使用裁剪后原始 vals，不含预测) =====
        try {
          const kpiHost=document.getElementById('rubbish-yearly-kpis');
          if(kpiHost){
            const firstVal=vals[0]; const lastVal=vals[vals.length-1];
            const yearsCount=vals.length-1;
            const cagr = yearsCount>0 && firstVal>0 ? Math.pow(lastVal/firstVal,1/yearsCount)-1 : 0;
            let maxJump=-Infinity, maxJumpYear='-';
            for(let i=1;i<vals.length;i++){ const d=vals[i]-vals[i-1]; if(d>maxJump){ maxJump=d; maxJumpYear=years[i]; } }
            const recent5=vals.slice(-5); const early5=vals.slice(0,5);
            const avgRecent = recent5.reduce((a,b)=>a+b,0)/recent5.length;
            const avgEarly = early5.reduce((a,b)=>a+b,0)/early5.length;
            const avgDelta = avgRecent-avgEarly;
            const items=[
              {label:'CAGR', value: (cagr*100).toFixed(2)+'%'},
              {label:'总增量', value: (lastVal-firstVal).toFixed(1)},
              {label:'最大年度增幅', value: maxJump> -Infinity ? maxJump.toFixed(1)+' ('+maxJumpYear+')' : '—'},
              {label:'近5年均值', value: avgRecent.toFixed(1)},
              {label:'早期5年均值', value: avgEarly.toFixed(1)},
              {label:'均值差', value: avgDelta.toFixed(1)}
            ];
            kpiHost.innerHTML=items.map(it=>`<div class="ykpi" style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);padding:4px 6px;border-radius:8px;font-size:10px;line-height:1.3;display:flex;flex-direction:column;min-width:70px;">
              <span style="opacity:.68;letter-spacing:.5px;">${it.label}</span>
              <b style="color:#ffb4b4;font-weight:600;">${it.value}</b>
            </div>`).join('');
          }
        }catch(kerr){ console.warn('[RubbishChart][KPI] 渲染失败',kerr); }
        // 更新标题右侧范围标签
        const rangeLabel=document.getElementById('rubbish-yearly-range-label');
        if(rangeLabel){ rangeLabel.textContent='近'+range+'年'+(forecastVals.length? ' + 预测':''); }
        // 事件绑定（一次）
        if(!this._boundRubbishControls){
          this._boundRubbishControls=true;
          ['rubbish-range','rubbish-ma','rubbish-forecast','rubbish-yoy'].forEach(id=>{
            const el=document.getElementById(id); if(el){ el.style.pointerEvents='auto'; el.addEventListener('change',()=>this.createRubbishChart(true)); }
          });
          // 强制一次 resize 以修复 zoom 下初始高度错误
          setTimeout(()=>window.dispatchEvent(new Event('resize')),60);
        }
      } // end yearlyCtx block
  if(!skipCityCharts && Array.isArray(summaryRes?.data)){
        // 原始列表（当前 dataService 限制为 ~8 个）
        let rawList=summaryRes.data.slice();
        // 区域筛选：静态映射简单分类（示例）
        const regionSel=window.__wallFilters?.['filter-region'];
        if(regionSel && regionSel!=='global'){
          const regionMap={
            pacific:['China','Japan','United States','Australia','Mexico','Peru','Chile','Indonesia','Philippines','Russia','Canada'],
            atlantic:['United States','Brazil','United Kingdom','France','Spain','Nigeria','South Africa','Morocco','Portugal','Argentina','Canada'],
            indian:['India','Indonesia','Australia','South Africa','Kenya','Tanzania','Somalia','Sri Lanka','Thailand']
          };
            const allow=new Set(regionMap[regionSel]||[]);
            rawList=rawList.filter(r=> allow.has(r.country));
        }
        // 计算全球总量（使用时间序列的最后一个值：百万吨 -> 吨）
        const globalTotalMillion = tsRes?.data?.values?.length ? tsRes.data.values[tsRes.data.values.length-1] : null;
        const globalTotalTons = globalTotalMillion? globalTotalMillion*1e6 : null;
        // 保留现有状态（模式 top5 / top8），刷新时不重置
        if(!this._rubbishState){ this._rubbishState={ mode:'auto' }; }
        // 自适应模式: 根据容器可用高度自动选择 top5 / top8
        if(this._rubbishState.mode==='auto'){
          try{
            const host=document.querySelector('[data-key="city"]');
            const legendBox=host?.querySelector('#rubbish-city-legend');
            const hostH=host?.clientHeight||0; // 卡片总高
            // 估算 legend 行高：按钮区 ~40px + 每条约 44px (含间距) + 汇总 34
            // 如果使用 top8 预计高度 > (hostH * 0.62) 则退回 top5
            const estTop8 = 40 + 8*44 + 34;
            this._rubbishState._autoChoice = estTop8 < hostH*0.62 ? 'top8':'top5';
          }catch(e){ this._rubbishState._autoChoice='top5'; }
        }
        const mode = this._rubbishState.mode==='auto' ? (this._rubbishState._autoChoice||'top5') : this._rubbishState.mode;
  const sliceCount = mode==='top8'? 8 : 5;
        const list=rawList.slice(0,sliceCount);
        const subtotal=list.reduce((a,b)=>a+(b.mismanaged||0),0)||1;
        const labels=list.map(r=>r.country.replace(/\s*\(.*\)/,''));
        const values=list.map(r=>+((r.mismanaged/subtotal)*100).toFixed(1)); // 图内归一化百分比
        const colors=['rgba(255,107,107,0.85)','rgba(78,205,196,0.85)','rgba(255,230,109,0.85)','rgba(106,90,205,0.75)','rgba(255,107,157,0.80)','rgba(168,218,220,0.85)','rgba(106,90,205,0.60)','rgba(77,171,247,0.80)'].slice(0,sliceCount);
        const solid=colors.map(c=>c.replace(/0\.[0-9]+\)/,'1)'));
        // ========== (主页面) 更新 / 创建 占比饼图 (归一化百分比 TopN) ==========
        if(pieCtx){
          if(this.charts.rubbishCityPie){
            this.charts.rubbishCityPie.data.labels=labels;
            this.charts.rubbishCityPie.data.datasets[0].data=values;
            this.charts.rubbishCityPie.data.datasets[0].backgroundColor=colors;
            this.charts.rubbishCityPie.data.datasets[0].borderColor=solid;
            this.charts.rubbishCityPie.update();
          } else {
            this.charts.rubbishCityPie=new Chart(pieCtx,{
              type:'doughnut',
              data:{labels,datasets:[{data:values,backgroundColor:colors,borderColor:solid,borderWidth:2}]},
              options:{
                responsive:true,maintainAspectRatio:false,cutout:'62%',
                plugins:{legend:{display:false},tooltip:{callbacks:{label:(ctx)=>`${ctx.label}: ${ctx.parsed}%`}}}
              }
            });
            this.appendDataNote(pieCtx,'来源: OWID 国家误管理 (归一化 TopN)');
          }
        }
        // ========== 柱状图 (千吨绝对值) ==========
        if(barCtx){ const abs=list.map(r=>Math.round((r.mismanaged||0)/1000)); const barBg=colors.map(c=>c.replace(/0\.[0-9]+\)/,'0.55)'));
          if(this.charts.rubbishCityBar){ this.charts.rubbishCityBar.data.labels=labels; this.charts.rubbishCityBar.data.datasets[0].data=abs; this.charts.rubbishCityBar.data.datasets[0].backgroundColor=barBg; this.charts.rubbishCityBar.data.datasets[0].borderColor=solid; this.charts.rubbishCityBar.update(); }
          else { this.charts.rubbishCityBar=new Chart(barCtx,{type:'bar',data:{labels,datasets:[{label:'误管理塑料 (千吨)',data:abs,backgroundColor:barBg,borderColor:solid,borderWidth:2,borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#a8dadc'},grid:{display:false}},y:{ticks:{color:'#a8dadc'},grid:{color:'rgba(168,218,220,0.10)'}}}}}); this.appendDataNote(barCtx,'来源: OWID 国家误管理 TopN'); }
        }
        // 保存状态用于 legend 渲染
        this._rubbishState.rawList=rawList;
        this._rubbishState.globalTotalTons = globalTotalTons;
        this._rubbishState.colorsBase=['rgba(255,107,107,0.85)','rgba(78,205,196,0.85)','rgba(255,230,109,0.85)','rgba(106,90,205,0.75)','rgba(255,107,157,0.80)','rgba(168,218,220,0.85)','rgba(106,90,205,0.60)','rgba(77,171,247,0.80)'];
        // legend 仍可使用（如果对应 DOM 在）
        this.updateCityLegend(list,colors,globalTotalTons,mode,subtotal);
      }
    }catch(err){ console.warn('[RubbishChart] 获取失败',err); }
    finally{ if(yearlyCtx) this.hideLoadingOverlay(yearlyCtx); this._busyRubbish=false; if(this._pendingRubbish){ this._pendingRubbish=false; this.createRubbishChart(true); } }
    // 同步 Top5/Top8 标记
    try{ if(!skipCityCharts) this.ensureCityLabels(); }catch(e){}
  }
  updateCityLegend(list,colors,globalTotalTons,mode,subtotal){
    const box=document.getElementById('rubbish-city-legend'); if(!box) return; box.innerHTML='';
    // 容器增强: 滚动 + 玻璃态 + 内边距，使条目不拥挤
    if(!box.dataset.enhanced){
      box.dataset.enhanced='1';
      Object.assign(box.style,{
        // 无滚动紧凑模式: overflow:visible; 高度由压缩条目适配
        display:'flex',flexDirection:'column',gap:'4px',overflow:'visible',
        padding:'8px 10px 6px',background:'linear-gradient(145deg,rgba(255,255,255,0.10),rgba(255,255,255,0.04))',
        border:'1px solid rgba(255,255,255,0.15)',borderRadius:'14px',backdropFilter:'blur(10px) saturate(1.25)',
        WebkitBackdropFilter:'blur(10px) saturate(1.25)'
      });
    }
    if(!Array.isArray(list) || !list.length){
      const empty=document.createElement('div'); empty.style.cssText='padding:6px 4px;font-size:12px;color:#89c2d9;opacity:.7;'; empty.textContent='(暂无数据)'; box.appendChild(empty); return;
    }
    // 控制区 (置顶 sticky)
    const ctrl=document.createElement('div'); ctrl.style.cssText='display:flex;gap:8px;margin-bottom:4px;flex-wrap:wrap;position:sticky;top:0;padding:4px 0 6px;background:linear-gradient(145deg,rgba(8,30,45,0.75),rgba(8,30,45,0.35));backdrop-filter:blur(6px);border-bottom:1px solid rgba(255,255,255,0.08);z-index:2;';
  ['auto','top5','top8'].forEach(m=>{ const btn=document.createElement('button'); btn.dataset.mode=m; btn.textContent=m==='auto'?'自适应':(m==='top5'?'Top5':'Top8'); const active = (this._rubbishState.mode==='auto' && m==='auto') || (this._rubbishState.mode!=='auto' && mode===m); btn.style.cssText='cursor:pointer;padding:3px 12px;border:1px solid '+(active?'rgba(168,218,220,0.85)':'rgba(168,218,220,0.35)')+';background:'+(active?'rgba(168,218,220,0.22)':'rgba(0,0,0,0.22)')+';color:#a8dadc;font-size:11px;border-radius:14px;backdrop-filter:blur(4px);transition:all .25s;'; btn.onmouseenter=()=>{btn.style.borderColor='rgba(168,218,220,0.85)';}; btn.onmouseleave=()=>{ if(!active) btn.style.borderColor='rgba(168,218,220,0.35)'; }; btn.onclick=()=>{ this.switchRubbishMode(m); }; ctrl.appendChild(btn); });
    box.appendChild(ctrl);
    // 列表条目
    list.forEach((r,i)=>{
      const div=document.createElement('div');
      div.className='legend-item';
      const shareGlobal = globalTotalTons? (r.mismanaged/globalTotalTons*100):null;
      const absMt = (r.mismanaged/1e6).toFixed(2);
      div.style.cssText='position:relative;display:grid;grid-template-columns:16px 1fr 60px;grid-template-rows:auto auto;row-gap:2px;column-gap:10px;align-items:center;padding:6px 10px 6px 6px;border-radius:10px;background:linear-gradient(90deg,rgba(255,255,255,0.055),rgba(255,255,255,0.015));border:1px solid rgba(255,255,255,0.08);';
      div.innerHTML=`<div style="width:14px;height:14px;border-radius:4px;background:${colors[i]};box-shadow:0 0 0 1px rgba(0,0,0,0.25) inset;"></div>
        <div style="font-size:12px;color:#e0fbfc;font-weight:500;letter-spacing:.03em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${i+1}. ${r.country.replace(/\s*\(.*\)/,'')}</div>
        <div style="font-size:12px;color:#ffce99;font-weight:600;text-align:right;">${(r.mismanaged/subtotal*100).toFixed(1)}%</div>
        <div style="grid-column:2 / 4;display:flex;justify-content:space-between;font-size:10px;color:#89c2d9;opacity:.85;">
          <span>${absMt} Mt</span>
          <span>${shareGlobal? shareGlobal.toFixed(2)+'% 全球':''}</span>
        </div>`;
      box.appendChild(div);
    });
    if(globalTotalTons){
      const sumDiv=document.createElement('div');
      const sumMt=(list.reduce((a,b)=>a+(b.mismanaged||0),0)/1e6).toFixed(2);
      const pct=(list.reduce((a,b)=>a+(b.mismanaged||0),0)/globalTotalTons*100).toFixed(1);
      sumDiv.style.cssText='margin-top:4px;padding:6px 8px;border:1px solid rgba(168,218,220,0.28);border-radius:10px;font-size:11px;color:#a8dadc;line-height:1.4;background:linear-gradient(135deg,rgba(0,40,60,0.55),rgba(0,40,60,0.25));backdrop-filter:blur(6px);';
      sumDiv.textContent=`${mode==='top5'?'前5':'前8'}合计: ${sumMt} Mt (~${pct}% 全球)`;
      box.appendChild(sumDiv);
    }
    // === 紧凑自适应: 若宿主高度 <=270 (260 卡片) 则压缩为单行条目，无需滚动条 ===
    const host=document.querySelector('[data-key="city"]');
    const compact = host && host.clientHeight <= 270; // 260 方块
    if(compact){
      // 压缩：去掉第二行 (Mt / 全球%)，把条目改成单行 (国名 + 本面板百分比)
      [...box.querySelectorAll('.legend-item')].forEach(div=>div.remove()); // 重新渲染一次简化版本
      box.style.gap='3px';
      list.forEach((r,i)=>{
        const one=document.createElement('div');
        one.className='legend-item compact';
        const pct=(r.mismanaged/subtotal*100).toFixed(1);
        one.style.cssText='display:flex;align-items:center;gap:6px;padding:3px 6px 3px 6px;border-radius:8px;background:rgba(255,255,255,0.05);font-size:11px;line-height:1.1;letter-spacing:.3px;';
        one.innerHTML=`<span style="width:12px;height:12px;border-radius:4px;background:${colors[i]};flex-shrink:0;box-shadow:0 0 0 1px rgba(0,0,0,.35) inset;"></span>`+
          `<span style="flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#e0fbfc;">${i+1}. ${r.country.replace(/\s*\(.*\)/,'')}</span>`+
          `<span style="color:#ffce99;font-weight:600;">${pct}%</span>`;
        box.appendChild(one);
      });
      // 合计 (紧凑单行)
      if(globalTotalTons){
        const sumLine=document.createElement('div');
        const sumMt=(list.reduce((a,b)=>a+(b.mismanaged||0),0)/1e6).toFixed(2);
        const pct=(list.reduce((a,b)=>a+(b.mismanaged||0),0)/globalTotalTons*100).toFixed(1);
        sumLine.style.cssText='margin-top:2px;padding:3px 6px;border:1px solid rgba(168,218,220,0.30);border-radius:8px;font-size:10px;color:#a8dadc;display:flex;justify-content:space-between;';
        sumLine.innerHTML=`<span>${mode==='top8'?'前8':'前5'}合计</span><span style="color:#ffbfa0;">${sumMt}Mt · ${pct}%</span>`;
        box.appendChild(sumLine);
      }
    }
    // 调整图表区域
    requestAnimationFrame(()=>this.resizeCityCharts({compact}));
  }
  switchRubbishMode(m){ if(!this._rubbishState) this._rubbishState={mode:'auto'}; if(this._rubbishState.mode!==m){ this._rubbishState.mode=m; this.createRubbishChart(true); this.ensureCityLabels(); } }
  // 面板放大时外部可调用: window.chartManager?.resizeCityCharts()
  ensureCityLabels(){
    try{
      const mode=this._rubbishState?.mode||'top5';
      const modeSpan=document.getElementById('rubbish-city-mode');
  if(modeSpan) modeSpan.textContent= (this._rubbishState.mode==='auto' ? (mode==='top8'?'自适应·Top8':'自适应·Top5') : (mode==='top8'?'Top8':'Top5'));
  const foot=document.getElementById('rubbish-city-footnote');
  if(foot) foot.textContent= (mode==='top8'?'Top8 国家 (归一化)':'Top5 国家 (归一化)');
    }catch(e){}
  }
  // 覆盖 createRubbishChart 完成后的标签同步 (调用点在 createRubbishChart 内最后)
  resizeCityCharts(opts={}){
    const host=document.querySelector('[data-key="city"]'); if(!host) return;
    const legend=host.querySelector('#rubbish-city-legend');
    const row=host.querySelector('.city-charts-row'); if(!row) return;
    const hostH=host.clientHeight; const lH=legend?legend.offsetHeight:0;
    const compact=opts.compact || hostH<=270;
    let target = Math.max(80, hostH - lH - 8);
    const barCanvas = row.querySelector('#rubbish-city-bar-chart');
    if(compact){
      // 紧凑模式：隐藏柱状图，仅留饼图；饼图缩放到 target 的 90%
      if(barCanvas) barCanvas.parentElement.style.display='none';
    } else if(barCanvas){
      barCanvas.parentElement.style.display='flex';
    }
    row.style.display='flex'; row.style.flex='1 1 auto'; row.style.height=target+'px';
    row.querySelectorAll('.city-chart-box').forEach(box=>{ box.style.height='100%'; box.style.display='flex'; box.style.alignItems='center'; box.style.justifyContent='center'; });
    // 让饼图保持正方
    const pieBox = row.querySelector('.city-chart-box.large'); if(pieBox){ const side = Math.min(pieBox.clientWidth, target); pieBox.style.alignItems='center'; pieBox.style.justifyContent='center'; const cvs=pieBox.querySelector('canvas'); if(cvs){ cvs.style.width= side+'px'; cvs.style.height= side+'px'; } }
    this.charts.rubbishCityPie?.resize(); this.charts.rubbishCityBar?.resize();
    this.ensureCityLabels();
  }
  /* -------- 真实数据：OSCAR 洋流 -------- */
  async createOceanCurrentChart(updateOnly=false){
    const speedCtx=document.getElementById('ocean-river-chart');
    const overviewCtx=document.getElementById('ocean-overview-chart');
    if(!speedCtx && !overviewCtx) return;
    if(!window.dataService){ console.warn('[OceanCurrent] dataService 缺失'); return; }
    if(speedCtx) this.showLoadingOverlay(speedCtx,'加载洋流...');
    try{
      const res=await window.dataService.getOceanCurrentField({forceRefresh:updateOnly});
      let uVals=[],vVals=[];
      // ERDDAP JSON (table.rows) 结构
      if(res?.table?.rows && Array.isArray(res.table.rows)){
        res.table.rows.forEach(r=>{ // 典型: [time, lat, lon, u, v]
          const u=r[3], v=r[4];
          if(isFinite(u)&&isFinite(v)){ uVals.push(u); vVals.push(v); }
        });
      }
      // 另一种聚合结构: u.data / v.data 数组 (假设已扁平)
      else if(res?.u?.data && res?.v?.data){
        const du=res.u.data, dv=res.v.data;
        for(let i=0;i<Math.min(du.length,dv.length);i++){
          const u=du[i], v=dv[i];
            if(isFinite(u)&&isFinite(v)){ uVals.push(u); vVals.push(v); }
        }
      }
      // 如果 experimental 或数据为空，构造合成小样本 fallback
      if(!uVals.length || !vVals.length){
        console.warn('[OceanCurrent] 无有效原始数据，使用 fallback 合成');
        for(let i=0;i<500;i++){
          // 随机缓慢流速 (0~0.25) + 少量高值点
          const angle=Math.random()*Math.PI*2; const mag=(Math.random()**2)*0.22 + (Math.random()>0.985?0.3:0); // 偶发峰值
          uVals.push(+ (Math.cos(angle)*mag).toFixed(3));
          vVals.push(+ (Math.sin(angle)*mag).toFixed(3));
        }
      }
      const speeds=uVals.map((u,i)=>{const v=vVals[i]; return Math.sqrt(u*u+v*v);}).filter(s=>isFinite(s));
      if(!speeds.length) throw new Error('无有效速度样本(fallback 也失败)');
      const bins=[0,0.05,0.10,0.15,0.20,Infinity]; const binLabels=['<0.05','0.05-0.10','0.10-0.15','0.15-0.20','≥0.20'];
      const counts=new Array(5).fill(0); speeds.forEach(s=>{ for(let b=0;b<bins.length-1;b++){ if(s>=bins[b] && s<bins[b+1]){ counts[b]++; break; } } });
      const mean=speeds.reduce((a,b)=>a+b,0)/speeds.length; const max=Math.max(...speeds); const nonZero=speeds.filter(s=>s>0.01).length;
      const palette=['rgba(78,205,196,0.85)','rgba(77,171,247,0.80)','rgba(255,230,109,0.80)','rgba(255,107,157,0.75)','rgba(106,90,205,0.70)'];
      if(speedCtx){ const solid=palette.map(c=>c.replace(/0\.[0-9]+\)/,'1)'));
        if(this.charts.oceanRiver){ this.charts.oceanRiver.data.labels=binLabels; this.charts.oceanRiver.data.datasets[0].data=counts; this.charts.oceanRiver.update(); }
        else { this.charts.oceanRiver=new Chart(speedCtx,{type:'bar',data:{labels:binLabels,datasets:[{label:'洋流速度分布(计数)',data:counts,backgroundColor:palette,borderColor:solid,borderWidth:2,borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#a8dadc'},grid:{display:false}},y:{ticks:{color:'#a8dadc'},grid:{color:'rgba(168,218,220,0.12)'}}}}}); this.appendDataNote(speedCtx,'来源: OSCAR 洋流 (子样本速度)'); }
      }
      if(overviewCtx){
        const metrics=[
          {label:'采样点数',value:speeds.length,unit:''},
          {label:'平均速度',value:+mean.toFixed(3),unit:'m/s'},
          {label:'最大速度',value:+max.toFixed(3),unit:'m/s'},
          {label:'>0.01m/s 点',value:nonZero,unit:''},
          {label:'非零比例',value:+(nonZero/speeds.length*100).toFixed(1),unit:'%'}
        ];
        const L=metrics.map(m=>m.label), V=metrics.map(m=>m.value), U=metrics.map(m=>m.unit);
        const c2=['rgba(168,218,220,0.85)','rgba(255,107,107,0.75)','rgba(78,205,196,0.80)','rgba(255,230,109,0.80)','rgba(106,90,205,0.75)'];
        const solid2=c2.map(c=>c.replace(/0\.[0-9]+\)/,'1)'));
        if(this.charts.oceanOverview){ this.charts.oceanOverview.data.labels=L; this.charts.oceanOverview.data.datasets[0].data=V; this.charts.oceanOverview.update(); }
        else { this.charts.oceanOverview=new Chart(overviewCtx,{type:'bar',data:{labels:L,datasets:[{label:'洋流指标',data:V,backgroundColor:c2,borderColor:solid2,borderWidth:2,borderRadius:8,barThickness:28}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${c.label}: ${c.parsed}${U[c.dataIndex]}`}}},scales:{x:{ticks:{color:'#a8dadc'},grid:{color:'rgba(168,218,220,0.12)'}},y:{ticks:{color:'#a8dadc'},grid:{display:false}}}}}); this.appendDataNote(overviewCtx,'来源: OSCAR 洋流 (统计样本)'); }
      }
    }catch(err){ console.warn('[OceanCurrent] 获取失败',err); }
    finally{ if(speedCtx) this.hideLoadingOverlay(speedCtx); }
  }
}

// 初始化（确保只定义一次）
window.addEventListener('load',()=>{ if(!window.chartManager) window.chartManager=new ChartManager(); });
// 全局便捷切换 (Top5 / Top8)
window.switchRubbishMode=(m)=>{ try{ window.chartManager?.switchRubbishMode(m); }catch(e){ console.warn('switchRubbishMode failed',e);} };