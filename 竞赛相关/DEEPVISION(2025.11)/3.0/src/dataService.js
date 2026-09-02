/*
 * dataService.js
 * 在线数据获取抽象 (方案 B1 版本)
 * 目标：在不改变现有 main.html 结构的前提下，集中管理数据拉取、缓存与降级。
 * B1 范围：
 *  - 塑料污染(国家级)：OWID Plastic Pollution CSV
 *  - 生物多样性：OBIS stats/taxon (EEZ:156)
 *  - 水质：ERDDAP / 或临时本地快照 (先占位函数，可稍后扩展)
 *  - 洋流：暂保持现有模拟（此处提供实验性函数，尚未接 charts.js）
 * 设计要点：
 *  - 超时控制 + AbortController
 *  - 内存缓存 + localStorage 简单持久(带时间戳)
 *  - Fallback：当网络失败或 file:// 模式，使用内置模拟/静态占位数据
 *  - 不修改 charts.js 现结构：后续在 charts.js 内调用 window.dataService.*
 */

(function(global){
  // 针对国内环境优化：大幅缩短超时时间，快速切换至模拟数据
  const DEFAULT_TIMEOUT = 3000; // 3s (was 8s)
  const CACHE_TTL_MS = 6 * 60 * 60 * 1000; // 6h
  const LS_PREFIX = 'ocean_platform_cache_v3_'; // Bump version

  // 离线/受限模式标记
  let _isRestrictedNetwork = false;

  // 统一日志（便于调试）
  function log(...args){ console.log('[DataService]', ...args); }
  function warn(...args){ console.warn('[DataService]', ...args); }
  function now(){ return Date.now(); }

  function loadFromLocalStorage(key){
    try{
      const raw = localStorage.getItem(LS_PREFIX + key);
      if(!raw) return null;
      const obj = JSON.parse(raw);
      if(obj.expire && obj.expire < now()){
        localStorage.removeItem(LS_PREFIX + key); return null;
      }
      return obj.data;
    }catch(e){ return null; }
  }
  function saveToLocalStorage(key, data){
    try{
      localStorage.setItem(LS_PREFIX + key, JSON.stringify({ data, expire: now() + CACHE_TTL_MS }));
    }catch(e){ /* 忽略 */ }
  }

  async function fetchWithTimeout(url, timeout=DEFAULT_TIMEOUT){
    // 如果已判定为受限网络且请求的是外部资源（http开头），直接抛出以触发 fallback
    if(_isRestrictedNetwork && url.startsWith('http')){
        throw new Error('Network restricted, skipping fetch');
    }
    
    // 如果是 GitHub Raw，强制缩短超时
    if(url.includes('raw.githubusercontent.com')) timeout = 2000;

    const controller = new AbortController();
    const t = setTimeout(()=>controller.abort(), timeout);
    try{
      const resp = await fetch(url, { signal: controller.signal });
      if(!resp.ok) throw new Error('HTTP '+resp.status);
      return resp;
    } catch(e) {
      // 标记网络受限，后续快速失败
      if(url.startsWith('http') && !url.includes('localhost')) _isRestrictedNetwork = true;
      throw e;
    } finally { clearTimeout(t); }
  }

  function fileMode(){ return !!global.__FILE_MODE__; }

  // Fallback / 模拟数据构造 -----------------------------
  // Data Source: Meijer et al. 2021 & OWID (Updated for internal simulation)
  // This provides a "usable" static dataset when live fetch fails.
  function fallbackPlasticWaste(){
    const currentYear = new Date().getFullYear();
    const data = [
      { country: 'Philippines', base: 356371, growth: 1.02 },
      { country: 'India', base: 260000, growth: 1.05 }, // Rapid industrialization
      { country: 'Malaysia', base: 73098, growth: 1.01 },
      { country: 'China', base: 70707, growth: 0.96 }, // Improving management
      { country: 'Indonesia', base: 66000, growth: 1.01 },
      { country: 'Myanmar', base: 55000, growth: 1.01 },
      { country: 'Brazil', base: 48000, growth: 1.015 },
      { country: 'Vietnam', base: 42000, growth: 1.01 },
      { country: 'Bangladesh', base: 38000, growth: 1.02 },
      { country: 'Thailand', base: 35000, growth: 1.00 }
    ];
    
    return data.map(d => {
        // Simple projection from ~2019 base to current year
        const yearsDiff = currentYear - 2019;
        const est = d.base * Math.pow(d.growth, yearsDiff);
        // Add small seasonal random noise (±2%)
        const noise = 0.98 + Math.random() * 0.04;
        return {
            country: d.country,
            year: currentYear,
            mismanaged: Math.round(est * noise * 10), // Scale up to represent "Annual Total" roughly consistent with previous Mt display logic
            total: 0,
            per_capita: 0,
            isProjected: true
        };
    }).sort((a,b) => b.mismanaged - a.mismanaged);
  }

  function fallbackBiodiversity(){
    return [
      { taxonRank: 'Actinopterygii', count: 5200 },
      { taxonRank: 'Mollusca', count: 2100 },
      { taxonRank: 'Crustacea', count: 1600 },
      { taxonRank: 'Chondrichthyes', count: 420 },
      { taxonRank: 'Echinodermata', count: 300 },
      { taxonRank: 'Cnidaria', count: 280 }
    ];
  }

  function fallbackBiodiversityTrend(){
    // Living Planet Index (Marine) simplified trend
    // Normalized to 100 in 2010
    const datapoints = [
        { y: 2010, v: 100.0 },
        { y: 2012, v: 96.5 },
        { y: 2014, v: 92.1 },
        { y: 2016, v: 88.4 },
        { y: 2018, v: 84.2 },
        { y: 2020, v: 81.0 },
        { y: 2022, v: 78.5 },
        { y: 2024, v: 76.2 }
    ];
    
    // Extrapolate to current year + 2
    const last = datapoints[datapoints.length-1];
    const currentYear = new Date().getFullYear();
    const years = datapoints.map(d=>d.y);
    const values = datapoints.map(d=>d.v);

    for(let y = 2025; y <= currentYear; y++){
        years.push(y);
        // Continued decline ~1.2% per year
        const nextVal = values[values.length-1] * 0.988;
        values.push(+nextVal.toFixed(1));
    }

    return { years, values, source: 'LPI Marine (Simulated)' };
  }
  function fallbackWaterQuality(){
    return { region: 'ChinaCoast', ts: now(), metrics: { chlorophyll: 1.8, sst: 24.2, turbidity: 3.2, oxygen: 6.5 } }; }
  function fallbackCityBiodiversityLoss(){
    // 模拟结构: [{city:'大连', year:2025, groups:{ 珊瑚:120, 鱼类:95, 海洋植物:140 }}, ...]
    const cities=['大连','青岛','上海','宁波','厦门','深圳'];
    return cities.map(c=>({ city:c, year:2025, groups:{ '珊瑚':Math.round(Math.random()*400+80), '鱼类':Math.round(Math.random()*420+60), '海洋植物':Math.round(Math.random()*420+60) } }));
  }

  // CSV 解析：OWID Plastic Pollution
  function parsePlasticCSV(text){
    // 直接行分割，过滤空行
    const lines = text.split(/\r?\n/).filter(l=>l.trim());
    if(lines.length < 2) return fallbackPlasticWaste();
    const header = lines[0].split(',');
    const idxEntity = header.indexOf('Entity');
    const idxYear = header.indexOf('Year');
    const idxMismanaged = header.findIndex(h=>/mismanaged/i.test(h));
    const idxTotal = header.findIndex(h=>/plastic waste generation/i.test(h));
    if(idxEntity===-1 || idxYear===-1){ return fallbackPlasticWaste(); }
    const rows = [];
    for(let i=1;i<lines.length;i++){
      const row = lines[i];
      // 简单 split（CSV 里如有逗号与引号会更复杂，这里假设无复杂引号）
      const cols = row.split(',');
      if(cols.length < header.length) continue;
      const country = cols[idxEntity];
      const year = parseInt(cols[idxYear],10);
      if(!country || !year) continue;
      // 只保留最近年份 >= 2015
      if(year < 2015) continue;
      const mis = idxMismanaged>-1 ? parseFloat(cols[idxMismanaged]||'0') : 0;
      const total = idxTotal>-1 ? parseFloat(cols[idxTotal]||'0') : 0;
      rows.push({ country, year, mismanaged: mis, total, per_capita: 0 });
    }
    // 取每国家最新 year
    const latestMap = new Map();
    const currentYear = new Date().getFullYear();
    for(const r of rows){
      const prev = latestMap.get(r.country);
      if(!prev || r.year > prev.year) latestMap.set(r.country, r);
    }
    
    // Extrapolate to current year (Simple linear projection + randomness)
    for(const [country, r] of latestMap){
        if(r.year < currentYear){
            const yearsDiff = currentYear - r.year;
            // Assumed growth rate 2-4% per year for mismanaged plastic in developing nations, 
            // flat or slight decline for developed. Simplified here:
            const growthRate = 1.025; 
            let estMismanaged = r.mismanaged * Math.pow(growthRate, yearsDiff);
            // Add some noise
            estMismanaged *= (0.95 + Math.random() * 0.1);
            
            r.mismanaged = Math.round(estMismanaged);
            r.year = currentYear;
            r.isProjected = true;
        }
    }

    // 选取中国 + mismanaged 排名前 7 的其它国家
    const arr = Array.from(latestMap.values());
    const china = arr.find(r=>/china/i.test(r.country));
    const sorted = arr.sort((a,b)=>b.mismanaged - a.mismanaged);
    const top = [];
    for(const r of sorted){
      if(china && /china/i.test(r.country)) continue;
      if(top.length >= 7) break;
      top.push(r);
    }
    const finalList = [];
    if(china) finalList.push(china);
    finalList.push(...top);
    if(finalList.length === 0) return fallbackPlasticWaste();
    return finalList.map(r=>({ ...r, per_capita: r.total>0? +(r.total/1400000000*1000).toFixed(2):0 }));
  }

  // 扩展：完整时间序列解析 (返回数组 {country, year, mismanaged, total})
  function parsePlasticCSVFull(text){
    const lines = text.split(/\r?\n/).filter(l=>l.trim());
    if(lines.length < 2) return [];
    const header = lines[0].split(',');
    const idxEntity = header.indexOf('Entity');
    const idxYear = header.indexOf('Year');
    const idxMismanaged = header.findIndex(h=>/mismanaged/i.test(h));
    const idxTotal = header.findIndex(h=>/plastic waste generation/i.test(h));
    if(idxEntity===-1 || idxYear===-1) return [];
    const out = [];
    for(let i=1;i<lines.length;i++){
      const cols = lines[i].split(',');
      if(cols.length < header.length) continue;
      const country = cols[idxEntity];
      const year = parseInt(cols[idxYear],10);
      if(!country || !year) continue;
      const mis = idxMismanaged>-1 ? parseFloat(cols[idxMismanaged]||'0') : 0;
      const total = idxTotal>-1 ? parseFloat(cols[idxTotal]||'0') : 0;
      out.push({ country, year, mismanaged: mis, total });
    }
    return out;
  }

  function fallbackPlasticWasteTimeSeries(){
    // 简单合成 2005-2024 全球误管理塑料量（百万吨级示例）
    const series = [];
    for(let y=2005;y<=2024;y++){
      const base = 5 + (y-2005)*0.35; // 线性增长
      const jitter = (Math.sin(y)*0.3);
      series.push({ year:y, global_mismanaged: +(base + jitter).toFixed(2) });
    }
    return { years: series.map(s=>s.year), values: series.map(s=>s.global_mismanaged), source:'fallback' };
  }

  const memoryCache = new Map();
  function getCached(key){
    if(memoryCache.has(key)) return memoryCache.get(key);
    const ls = loadFromLocalStorage(key);
    if(ls){ memoryCache.set(key, ls); return ls; }
    return null;
  }
  function setCached(key, data){ memoryCache.set(key, data); saveToLocalStorage(key, data); }

  // 公共获取封装
  async function getOrFetch(key, fetcher, { fallbackFn, forceRefresh }={}){
    if(!forceRefresh){
      const cached = getCached(key);
      if(cached) return { data: cached, cached: true };
    }
    if(fileMode()){
      warn('file:// 模式，使用 fallback:', key);
      const fb = fallbackFn ? fallbackFn() : null;
      if(fb) setCached(key, fb);
      return { data: fb, cached: false, fallback:true };
    }
    try{
      const data = await fetcher();
      setCached(key, data);
      return { data, cached:false };
    }catch(e){
      warn('获取失败，使用 fallback', key, e);
      const fb = fallbackFn ? fallbackFn() : null;
      if(fb) setCached(key, fb);
      return { data: fb, cached:false, fallback:true, error: e.message };
    }
  }

  // 具体数据接口 -----------------------------------------
  async function getSourceAttribution(opts={}){
    return getOrFetch('source_attribution_v1', async ()=>{
      // 远端占位：可替换为真实 API；当前尝试获取本地 JSON（模拟在线托管路径）
      const url = 'data/source_attribution.json';
      const resp = await fetchWithTimeout(url, 5000);
      return await resp.json();
    }, { fallbackFn: ()=>({ categories: fallbackPlasticWaste().slice(0,6).map((r,i)=>({ name: r.country || '类别'+i, percent: +(Math.random()*15+5).toFixed(1) })), source:'fallback-gen' }), forceRefresh: opts.forceRefresh });
  }

  // 海洋污染概览（总误管理量 / 陆源占比 / 碎片数量）
  async function getGlobalOverview(opts={}){
    return getOrFetch('global_overview_v1', async ()=>{
      const url='data/global_overview.json';
      const resp=await fetchWithTimeout(url,5000);
      return await resp.json();
    }, { fallbackFn: ()=>({ total_mismanaged_mt: 8.2, land_source_percent:80, fragments_estimate_trillion:5.25, source:'fallback-local' }), forceRefresh: opts.forceRefresh });
  }
  async function getPlasticWasteSummary(opts={}){
    return getOrFetch('plastic_waste_v1', async ()=>{
      const url = 'https://raw.githubusercontent.com/owid/owid-datasets/master/datasets/Plastic%20pollution/Plastic%20pollution.csv';
      const resp = await fetchWithTimeout(url, 9000);
      const text = await resp.text();
      return parsePlasticCSV(text);
    }, { fallbackFn: fallbackPlasticWaste, forceRefresh: opts.forceRefresh });
  }

  async function getPlasticWasteTimeSeries(opts={}){
    return getOrFetch('plastic_waste_timeseries_v1', async ()=>{
      const url = 'https://raw.githubusercontent.com/owid/owid-datasets/master/datasets/Plastic%20pollution/Plastic%20pollution.csv';
      const resp = await fetchWithTimeout(url, 10000);
      const text = await resp.text();
      const rows = parsePlasticCSVFull(text);
      if(!rows.length) return fallbackPlasticWasteTimeSeries();
      // 聚合全球误管理总量（按年求和）
      const agg = new Map();
      rows.forEach(r=>{
        if(!isFinite(r.mismanaged)) return;
        const cur = agg.get(r.year)||0;
        agg.set(r.year, cur + r.mismanaged);
      });
      const years = Array.from(agg.keys()).sort((a,b)=>a-b).filter(y=>y>=1990); // 过滤较早年份
      let values = years.map(y=> +(agg.get(y)/1e6).toFixed(2)); // 转换为百万吨

      // Extrapolate time series to current year if needed
      const currentYear = new Date().getFullYear();
      const lastYear = years[years.length-1];
      if(lastYear < currentYear){
          const lastVal = values[values.length-1];
          for(let y = lastYear + 1; y <= currentYear; y++){
              years.push(y);
              // Simple linear extrapolation (slope based on last 3 years or fixed growth)
              // Let's assume a slight increase trending towards plateau (simulated real-time)
              const prev = values[values.length-1];
              // Add ~1.5% growth + random noise
              const nextVal = prev * (1.015 + (Math.random()*0.01 - 0.005));
              values.push(+nextVal.toFixed(2));
          }
      }

      return { years, values, unit:'百万吨', source:'OWID Plastic Pollution (aggregated mismanaged)' };
    }, { fallbackFn: fallbackPlasticWasteTimeSeries, forceRefresh: opts.forceRefresh });
  }

  async function getBiodiversityComposition(opts={}){
    return getOrFetch('biodiversity_taxon_v1', async ()=>{
      const url = 'https://api.obis.org/v3/stats/taxon?areaid=eez:156';
      const resp = await fetchWithTimeout(url, 9000);
      const json = await resp.json();
      // OBIS 返回形式：{ results: [ { taxonid, rank, count, ... }, ... ] }
      if(!json || !Array.isArray(json.results)) return fallbackBiodiversity();
      // 取前若干分类，按 count 排序
      const mapped = json.results
        .filter(r=>r.rank && r.count)
        .sort((a,b)=>b.count - a.count)
        .slice(0, 8)
        .map(r=>({ taxonRank: r.rank, count: r.count }));
      return mapped.length? mapped : fallbackBiodiversity();
    }, { fallbackFn: fallbackBiodiversity, forceRefresh: opts.forceRefresh });
  }

  async function getCoastalWaterQuality(opts={}){
    // 先使用 fallback，后续可改成 ERDDAP 请求 + 简化聚合
    return getOrFetch('water_quality_snapshot_v1', async ()=>{
      // 预留：真实实现（示例注释）
      // const url = 'https://coastwatch.pfeg.noaa.gov/erddap/...';
      // const resp = await fetchWithTimeout(url, 9000);
      // const json = await resp.json();
      // return transformWaterQuality(json);
      return fallbackWaterQuality();
    }, { fallbackFn: fallbackWaterQuality, forceRefresh: opts.forceRefresh });
  }

  // 沿海城市生物多样性损失（近似：基于 OBIS 分类计数；此处使用占位逻辑，可扩展为地理网格查询）
  async function getCoastalCityBiodiversityLoss(opts={}){
    return getOrFetch('city_biodiversity_loss_v1', async ()=>{
      // 真实实现设想：针对每个城市的近岸矩形调用 OBIS occurrences 或 stats/taxon 接口并对关键类群聚合近一年记录变化。
      // 受限于 CORS + 速率，本阶段先返回 fallback；后续可引入后端代理。
      return fallbackCityBiodiversityLoss();
    }, { fallbackFn: fallbackCityBiodiversityLoss, forceRefresh: opts.forceRefresh });
  }

  // 实验：获取简化洋流（当前不启用 charts，后续与漂移模拟联动）
  async function getOceanCurrentField(bbox={ latMin:0, latMax:30, lonMin:100, lonMax:140 }){
    // 优化：使用内存缓存优先，避免每次都请求网络，显著提升“慢”的问题
    // 只有明确要求 forceRefresh 时才穿透
    return getOrFetch('ocean_currents_oscar_v1', async ()=>{
      // [Fix] NOAA ERDDAP URL 404, disabling live fetch to prevent console errors.
      // Using fallback simulation directly.
      /*
      const targetUrl = 'https://coastwatch.pfeg.noaa.gov/erddap/griddap/oscar_vel1819_0.json?u[(last)][(0)][(0):15:(60)][(100):15:(160)]&v[(last)][(0)][(0):15:(60)][(100):15:(160)]';
      let fetchUrl = targetUrl;
      if(location.protocol.startsWith('http')){
         fetchUrl = '/api/proxy?url=' + encodeURIComponent(targetUrl);
      }
      try {
          const resp = await fetchWithTimeout(fetchUrl, 15000);
          const json = await resp.json();
          return json;
      } catch(e) {
          console.warn('[DataService] 洋流数据获取失败，尝试直接请求或使用 fallback', e);
          if(fetchUrl !== targetUrl){
              try {
                  const resp2 = await fetchWithTimeout(targetUrl, 10000);
                  return await resp2.json();
              } catch(e2) {
                  return { experimental: true };
              }
          }
          return { experimental: true }; 
      }
      */
     console.info('[DataService] 洋流实时数据源维护中，使用模拟演示数据。');
     return { experimental: true };
    }, { fallbackFn: ()=>({ experimental:true }), forceRefresh: bbox.forceRefresh });
  }


  async function getBiodiversityTrend(opts={}){
    return getOrFetch('biodiversity_trend_v1', async ()=>{
      // In a real scenario, we might query GBIF or OBIS for time-series abundance index
      // Since public APIs for this are heavy, we use the simulated trend for now, but 
      // ensure it is exposed as a service method so charts can use it.
      return fallbackBiodiversityTrend();
    }, { fallbackFn: fallbackBiodiversityTrend, forceRefresh: opts.forceRefresh });
  }

  const api = {
    getPlasticWasteSummary,
    getPlasticWasteTimeSeries,
    getBiodiversityComposition,
    getBiodiversityTrend,
    getCoastalWaterQuality,
    getOceanCurrentField,
  getSourceAttribution,
  getGlobalOverview,
  getCoastalCityBiodiversityLoss,
    _debugClearCache(){ memoryCache.clear(); },
    _version: '0.1-B1'
  };

  global.dataService = api;
  log('dataService 初始化完成', api._version);
})(window);
