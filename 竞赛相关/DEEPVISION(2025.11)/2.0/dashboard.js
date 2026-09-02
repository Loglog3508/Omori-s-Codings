// 主要交互功能
// ================= Force Square Panels =================
// 恢复强制正方形：为所有可视卡片计算其宽度并写入 CSS 变量 --square-size，
// 通过 body.force-square-panels 与 .square-target 类控制生效。
(function setupForceSquarePanels(){
    const BODY_CLASS='force-square-panels';
    const selector='.huarong-piece, .glass-card.panel, .glass-card.square-target';
    let ro=null; let active=false; let pending=false;
    function apply(){
        if(!active) return; pending=false;
        const cards=[...document.querySelectorAll(selector)];
        cards.forEach(card=>{
            if(card.classList.contains('panel-enlarging')) return; // 放大时跳过
            const w=card.getBoundingClientRect().width;
            if(w>40){ card.style.setProperty('--square-size', w+'px'); card.classList.add('square-target'); }
        });
    }
    function schedule(){ if(!pending){ pending=true; requestAnimationFrame(apply); } }
    function enable(){
        if(active) return; active=true;
        document.body.classList.add(BODY_CLASS);
        if(!ro){
            ro=new ResizeObserver(schedule);
            document.querySelectorAll(selector).forEach(c=>{ try{ ro.observe(c); }catch(e){} });
            window.addEventListener('resize', schedule, {passive:true});
        }
        apply();
    }
    function disable(){
        if(!active) return; active=false; document.body.classList.remove(BODY_CLASS);
        if(ro){ try{ ro.disconnect(); }catch(e){} ro=null; }
        document.querySelectorAll(selector).forEach(c=>{ c.style.removeProperty('--square-size'); });
    }
    // 自动启用（已禁用，防止高度被强制正方形影响统一网格布局）
    // document.addEventListener('DOMContentLoaded', ()=> setTimeout(enable, 200));
    window.enableForceSquare=enable; window.disableForceSquare=disable; window.forceSquareApply=apply;
})();

// 新版 dashboard-grid 已替换旧 puzzle / fallback 体系；简单清理遗留控制逻辑。
window.__DASHBOARD_GRID__ = true; // 使用纯 CSS Grid 简化布局（不再需要额外 fallback）

// ============ 视口自适应卡片高度（高空间利用率） ============
// 思路：根据当前列数 + 视口剩余高度，动态计算统一高度，让卡片尽量填满可视区域。
// 步骤：
// 1. 计算列数：解析 grid-template-columns;
// 2. 计算需要的行数 rows = ceil(totalCards / cols);
// 3. 可用高度 = window.innerHeight - gridTop - bottomReserve(60)；
// 4. 目标高度 = (可用高度 - (rows-1)*gap) / rows （限制在 260~520 之间）
// 5. 赋值给所有未放大的卡片；放大时跳过；关闭后重新计算。
// 6. 横向 / 纵向拉伸都会触发 recalculation。
// 额外：如果内容实际小于目标高度，内部使用 flex column + justify-start，不会拉伸比例失真；canvas 设置 height:auto 让其自适应填满。
(function viewportAutoCardSizing(){
    const GAP_CACHE = {value:28};
    let lastCols = null; let lockedTarget = null; let lastW = window.innerWidth; let lastH = window.innerHeight;
    function getGap(grid){
        try {
            const cs = getComputedStyle(grid);
            const g = parseFloat(cs.gap || cs.rowGap || '28');
            if(!isNaN(g)) GAP_CACHE.value = g; return GAP_CACHE.value;
        } catch { return GAP_CACHE.value; }
    }
    function calc(){
        const grid=document.querySelector('.dashboard-grid'); if(!grid) return;
        const cards=[...grid.querySelectorAll('.huarong-piece')];
        if(!cards.length) return;
        // 清除旧高度（避免列数变化时产生高度死锁）
        cards.forEach(c=>{ if(!c.classList.contains('panel-enlarging')) c.style.height=''; });
        // 解析列数
        let cols=1;
        try {
            const tpl = getComputedStyle(grid).gridTemplateColumns.trim();
            // 兼容 repeat(auto-fit|minmax(...)) 形式：先按分隔符统计列片段数量（非 auto-fit 情况）
            const autoFit = /auto-(fit|fill)/.test(tpl);
            if(autoFit){
                // 动态：通过实际第一行子元素测量求列数，避免缩放导致解析不准
                const firstRowWidths = [];
                let rowTop=null;
                for(const card of cards){
                    const r=card.getBoundingClientRect();
                    if(rowTop===null) rowTop=r.top;
                    if(Math.abs(r.top-rowTop)<2){ firstRowWidths.push(r.width); }
                }
                if(firstRowWidths.length){ cols = firstRowWidths.length; }
            } else {
                const m = tpl.match(/repeat\((\d+)/);
                if(m){ cols = parseInt(m[1],10)||1; }
                else { cols = tpl.split('1fr').length-1 || 1; }
            }
        } catch{}
        const rows = Math.ceil(cards.length / cols);
        const rect = grid.getBoundingClientRect();
        const gap = getGap(grid);
        const available = window.innerHeight - rect.top - 60; // 60 预留底部
        if(available < 260) return; // 不够空间不处理
        let target;
        // 判断是否需要重新计算锁定：列数变化或窗口尺寸变化幅度大于 40px
        const significantResize = Math.abs(window.innerWidth-lastW)>40 || Math.abs(window.innerHeight-lastH)>60;
        if(lockedTarget && lastCols===cols && !significantResize){
            target = lockedTarget; // 使用锁定高度，避免轻微布局抖动
        } else {
            target = (available - (rows-1)*gap) / rows;
            target = Math.max(260, Math.min(520, Math.floor(target)));
            lockedTarget = target; lastCols = cols; lastW = window.innerWidth; lastH = window.innerHeight;
        }
        cards.forEach(c=>{ if(!c.classList.contains('panel-enlarging')) { 
            c.style.height=target+'px'; c.dataset.autoH='1';
            // 收紧：限制卡片长宽比不超过 1.3（进一步防止“超宽扁平”导致信息密度下降）/ tightened aspect ratio cap 1.3
            const r = c.offsetWidth / target;
            if(r>1.3){ // 调整高度以满足新的宽高比
                const adjH = Math.min(target * (r/1.3), 540); // 上限略放宽 540 以适配文字
                c.style.height = Math.round(adjH)+'px';
            }
            // 若启用强制平方，使用宽度覆盖高度（维持正方形）
            if(document.body.classList.contains('force-square-panels')){
                const w=c.getBoundingClientRect().width; c.style.height=w+'px';
            }
        }});
        // 限制内部并创建滚动容器（只做一次）
        cards.forEach(c=>{
            if(c.classList.contains('panel-enlarging')) return;
            if(!c.__scrollWrapped){
                // 兼容：若不存在 .panel-content，则创建并把除标题外所有内容包进去
                let content = c.querySelector('.panel-content');
                const title = c.querySelector('.panel-title');
                if(!content){
                    content = document.createElement('div');
                    content.className='panel-content';
                    // 将标题之外节点转移
                    const moves=[]; c.childNodes.forEach(n=>{ if(n!==title) moves.push(n); });
                    moves.forEach(n=>content.appendChild(n));
                    c.appendChild(content);
                }
                if(content && !content.querySelector('.card-scroll-area')){
                    const wrapper=document.createElement('div');
                    wrapper.className='card-scroll-area';
                    while(content.firstChild){ wrapper.appendChild(content.firstChild); }
                    content.appendChild(wrapper);
                }
                c.__scrollWrapped=true;
            }
            // 判断是否溢出
            const scrollArea=c.querySelector('.card-scroll-area');
            if(scrollArea){
                if(scrollArea.scrollHeight>scrollArea.clientHeight+4){ c.classList.add('card-overflow'); }
                else { c.classList.remove('card-overflow'); }
            }
        });
        window.__AUTO_GRID_STATE__ = {cols, rows, target, available};
        try { window.chartManager?.handleResize(); } catch {}
        // 初始化滚动渐进模糊监听（只做一次）
        if(!window.__CARD_SCROLL_BLUR_INIT__){
            window.__CARD_SCROLL_BLUR_INIT__=true;
            initCardScrollBlur();
        }
    }
    let timer=null; function schedule(){ clearTimeout(timer); timer=setTimeout(calc, 120); }
    window.addEventListener('resize', schedule, {passive:true});
    document.addEventListener('DOMContentLoaded', ()=> setTimeout(calc, 300));
    document.addEventListener('chart-ready', ()=> setTimeout(calc, 200));
    // 周期性兜底：防止某些设备 resize 未触发
    // 取消周期性强制重算（避免“自己抽动”）改为仅在窗口显著变化时通过 resize 触发
    window.forceAutoFit = calc;
})();

// 渐进模糊滚动边缘：根据 scrollTop 与可滚动高度添加类名
function initCardScrollBlur(){
    const areas=[...document.querySelectorAll('.huarong-piece.card-overflow .card-scroll-area')];
    if(!areas.length) return;
    areas.forEach(area=>{
        function update(){
            const max=area.scrollHeight - area.clientHeight;
            if(max <= 2){ area.classList.remove('scroll-bottom-active'); return; }
            const st=area.scrollTop;
            if(st < max - 4){ area.classList.add('scroll-bottom-active'); } else { area.classList.remove('scroll-bottom-active'); }
        }
        area.addEventListener('scroll', update, {passive:true});
        requestAnimationFrame(update);
    });
    // 后续新出现的 overflow 区域再补绑定
    setTimeout(()=>{
        document.querySelectorAll('.huarong-piece.card-overflow .card-scroll-area').forEach(a=>{
            if(!a.__blurBound){
                a.__blurBound=true;
                a.addEventListener('scroll', ()=>{
                    const max=a.scrollHeight - a.clientHeight;
                    const st=a.scrollTop;
                    if(st < max - 4){ a.classList.add('scroll-bottom-active'); } else { a.classList.remove('scroll-bottom-active'); }
                }, {passive:true});
                requestAnimationFrame(()=>{
                    const max=a.scrollHeight - a.clientHeight;
                    if(max>2){ const st=a.scrollTop; if(st < max - 4) a.classList.add('scroll-bottom-active'); }
                });
            }
        });
    },600);
}

document.addEventListener('DOMContentLoaded', ()=>{ setTimeout(()=>{ if(!window.__CARD_SCROLL_BLUR_INIT__){ window.__CARD_SCROLL_BLUR_INIT__=true; initCardScrollBlur(); } },400); });

// Flex 方阵自检：若某些缩放场景下列被压到 < 260px，自动切换 dg-flex-mode
(function ensureDashboardFlexIntegrity(){
    // 纯 CSS Grid 模式：直接跳过（无需 flex 完整性监控）
    if(!window.__DASHBOARD_GRID__) return;
    function scan(){
        const grid=document.querySelector('.dashboard-grid');
        if(!grid) return;
        const pieces=[...grid.querySelectorAll('.huarong-piece')];
        if(!pieces.length) return;
        const widths=pieces.map(p=>p.getBoundingClientRect().width).filter(w=>w>0);
        if(!widths.length) return;
        const min=Math.min(...widths);
        if(min < 260){
            if(!grid.classList.contains('dg-flex-mode')){
                grid.classList.add('dg-flex-mode');
                console.log('[DashboardGrid] 触发保护模式 dg-flex-mode (min='+min.toFixed(1)+'px)');
            }
        } else if(min > 310 && grid.classList.contains('dg-flex-mode')){
            // 宽度恢复后撤销保护
            grid.classList.remove('dg-flex-mode');
            console.log('[DashboardGrid] 退出保护模式');
        }
    }
    window.addEventListener('resize', ()=>{ requestAnimationFrame(scan); }, {passive:true});
    document.addEventListener('DOMContentLoaded', ()=> setTimeout(scan,120));
    setTimeout(scan,600);
    window.debugDashboardGrid=()=>{
        const grid=document.querySelector('.dashboard-grid');
        if(!grid) return {};
        const widths=[...grid.querySelectorAll('.huarong-piece')].map(p=>p.getBoundingClientRect().width.toFixed(1));
          return {classList:[...grid.classList], widths};
    };
})();

// 若卡片数量异常( < 5 )或全部宽度高度一致且接近容器总宽 -> 触发纯 grid 回退
// 已禁用自动 pure-grid 回退逻辑（新缩放列数控制 + dynamic-auto 已解决单列压缩问题）
(function autoSwitchPureGridDisabled(){
    window.__PURE_GRID_FALLBACK_DISABLED__ = true;
})();

// 面板动画效果
function animatePanel(panel, evt) {
    if (!panel) return;
    panel.classList.add('panel-animate');
    const e = evt || window.event; // 兼容性
    // 添加点击涟漪效果
    const ripple = document.createElement('div');
    ripple.classList.add('ripple');
    try {
        const rect = panel.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = (e?.clientX || rect.width/2) - rect.left - size / 2;
        const y = (e?.clientY || rect.height/2) - rect.top - size / 2;
        ripple.style.cssText = `position:absolute;width:${size}px;height:${size}px;left:${x}px;top:${y}px;background:rgba(255,255,255,0.12);border-radius:50%;transform:scale(0);animation:ripple 0.6s linear;pointer-events:none;z-index:10;`;
    } catch(err) {
        ripple.style.cssText = 'position:absolute;inset:0;background:rgba(255,255,255,0.08);opacity:0;';
    }
    panel.style.position = 'relative';
    panel.appendChild(ripple);
    setTimeout(() => {
        panel.classList.remove('panel-animate');
        ripple.remove?.();
    }, 650);
    // 触发相关图表动画
    const chartId = panel.querySelector('canvas')?.id;
    if (chartId && window.chartManager?.animateChart) {
        const chartName = chartId.replace('-chart', '');
        try { window.chartManager.animateChart(chartName); } catch(_) {}
    }
}

// 漂流演示快速入口已统一由侧边栏扩展功能 / 其它页面提供, 主页不再直接打开。
// 保留空函数避免旧引用报错。
function navigateToDemo(){ console.log('[navigateToDemo] 已移除主页直接打开。'); }

// 添加涟漪动画CSS
const style = document.createElement('style');
style.textContent = `
@keyframes ripple { to { transform: scale(4); opacity:0; } }
.concept-link{ position:relative; overflow:hidden; }
.concept-link::before{ content:''; position:absolute; top:0; left:-100%; width:100%; height:100%; background:linear-gradient(90deg,transparent,rgba(255,255,255,0.1),transparent); transition:left .5s; }
.concept-link:hover::before{ left:100%; }
`;
document.head.appendChild(style);

// 全局变量（若其它脚本已定义则不重复覆盖）
// Globe feature removed (UI & 3D rendering). Keep placeholder to avoid reference errors.
if (!window.globe3D) { window.globe3D = null; }
// Provide safe no-op stubs early (will be reaffirmed later)
window.toggleRotation = () => false;
window.resetGlobe = () => {};
window.setGlobeSize = () => {};

// 全局弹窗清理函数
window.clearAllPopups = function() {
    const unwantedSelectors = [
        '.simulation-result-card', '.result-modal', '.result-popup', '.modal', '.data-modal', '.chart-modal', '.results-container',
        '[class*="result"]', '[class*="popup"]', '[class*="modal"]', '[id*="immersive"]', '[class*="immersive"]', 
        '[id*="translate"]', '[class*="translate"]', '.tippy-box', '.tooltip', '.popover',
        '[style*="position: fixed"]', '[style*="z-index: 999"]', '[style*="z-index: 9999"]'
    ];
    
    unwantedSelectors.forEach(selector => {
        try {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                if (el && el.parentNode && !el.closest('.app-container, .main-content, .huarong-puzzle-container, .globe-section')) {
                    console.log('�️ 移除不需要的弹窗元素:', el.className || el.id || selector);
                    el.remove();
                }
            });
        } catch (e) {
            console.warn('清理弹窗时出错:', e);
        }
    });
    
    // 特殊处理翻译相关弹窗
    const translatePopups = document.querySelectorAll('div[style*="position: fixed"]');
    translatePopups.forEach(el => {
        if (el.textContent && (el.textContent.includes('翻译') || el.textContent.includes('translate'))) {
            console.log('🗑️ 移除翻译相关弹窗');
            el.remove();
        }
    });
};

/* ===== Quick Glance 网络状态监测 ===== */
(function initNetStatus(){
    const el=document.getElementById('qg-net-status');
    if(!el) return;
    const text=el.querySelector('.qg-net-text');
    const STATE={INIT:'init',OK:'ok',SLOW:'slow',DOWN:'down',ERROR:'error'};
    let failCount=0;
    function setState(state,msg){
        el.setAttribute('data-state',state);
        if(text){ text.textContent=msg; }
    }
    async function ping(){
        const start=performance.now();
        try{
            const resp=await fetch('charts.js',{method:'HEAD',cache:'no-store'});
            const latency=performance.now()-start;
            if(!resp.ok) throw new Error('status '+resp.status);
            failCount=0;
            if(latency<250){ setState(STATE.OK, '正常 '+Math.round(latency)+'ms'); }
            else if(latency<800){ setState(STATE.SLOW, '较慢 '+Math.round(latency)+'ms'); }
            else { setState(STATE.DOWN, '超时 '+Math.round(latency)+'ms'); }
        }catch(err){
            failCount++;
            if(failCount>=3){ setState(STATE.DOWN,'连接失败'); }
            else { setState(STATE.ERROR,'重试中('+failCount+')'); }
        }
    }
    setState(STATE.INIT,'初始化...');
    ping();
    setInterval(()=>{ ping(); },30000);
    setInterval(()=>{ if(['down','error'].includes(el.getAttribute('data-state'))){ ping(); } },10000);
})();

// === 横向滚动检测辅助 ===
window.debugHorizontalOverflow = function(threshold=window.innerWidth){
    const overs=[];
    document.querySelectorAll('body *').forEach(el=>{
        try{
            const r=el.getBoundingClientRect();
            if(r.width>threshold+2){ overs.push({el, width:r.width.toFixed(1), selector: el.className||el.id||el.tagName}); }
        }catch{}
    });
    console.log('[OverflowScan] 视口宽度=', window.innerWidth, '超宽元素数量=', overs.length);
    overs.slice(0,40).forEach(o=>console.log('> 超宽', o.width, o.selector, o.el));
    return overs;
};

// 页面加载完成后的初始化
window.addEventListener('load', () => {
    // 添加页面加载动画
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.8s ease';
    
    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 100);
    
    // 清理任何已存在的弹窗
    setTimeout(() => {
        window.clearAllPopups();
    }, 500);
    
    console.log('🌍 Globe 功能已移除，跳过 3D 地球初始化');
    
    // 初始化工具提示
    initTooltips();
    
    // 自动开始地球动画
    setTimeout(() => {
        if (globe3D) {
            globe3D.toggleAnimation();
        }
    }, 2000);
    
    console.log('DeepVision (深蓝视界) 数据可视化平台已加载完成');
    // 强制锁定缩放 90%
    if(!document.body.classList.contains('locked-zoom-90')){
        document.body.classList.add('locked-zoom-90');
        // 触发一次布局重算
        setTimeout(()=>{ try{ window.forceAutoFit && window.forceAutoFit(); }catch(_){} },150);
    }
    // 若遗留 force-square-panels 类名，主动移除（防止旧缓存或刷新后残留）
    if(document.body.classList.contains('force-square-panels')){
        document.body.classList.remove('force-square-panels');
        try{ window.disableForceSquare && window.disableForceSquare(); }catch(e){}
        console.log('[Init] 已移除遗留 force-square-panels');
    }
    // 拉取概览在线数据 (total / percent / fragments)
    (async()=>{
        if(!window.dataService?.getGlobalOverview) return;
        try{
            const res=await window.dataService.getGlobalOverview();
            const d=res?.data; if(!d) return;
            const host=document.querySelector('[data-key="overview"]');
            if(host){
                const valEl=host.querySelector('.main-value');
                const landBox=host.querySelector('.ocean-pollution-sub .sub-box:first-child .sub-value');
                const fragBox=host.querySelector('.ocean-pollution-sub .sub-box:last-child .sub-value');
                if(valEl && typeof d.total_mismanaged_mt==='number'){ valEl.textContent=d.total_mismanaged_mt.toFixed(1)+'M'; }
                if(landBox && isFinite(d.land_source_percent)) landBox.textContent=d.land_source_percent+'%';
                if(fragBox && isFinite(d.fragments_estimate_trillion)) fragBox.textContent=d.fragments_estimate_trillion+'万亿';
            }
            // 同步侧边栏快速概览
            try{
                const t=document.getElementById('qg-total');
                const l=document.getElementById('qg-land');
                const f=document.getElementById('qg-fragments');
                if(t && typeof d.total_mismanaged_mt==='number') t.textContent=d.total_mismanaged_mt.toFixed(1);
                if(l && isFinite(d.land_source_percent)) l.textContent=d.land_source_percent;
                if(f && isFinite(d.fragments_estimate_trillion)) f.textContent=d.fragments_estimate_trillion;
            }catch(e){ console.warn('[QuickGlance] 概览填充失败', e); }
            // 派发概览数据就绪事件用于关闭加载遮罩
            try { document.dispatchEvent(new Event('data-overview-ready')); } catch(e) { console.warn('[Event] data-overview-ready 派发失败', e); }
        }catch(e){ console.warn('概览数据获取失败',e); }
    })();
});

// (删除重复旧版自动刷新逻辑，统一使用下方带倒计时实现)
// 兼容：旧接口留空
window.runUnifiedSimulation = function(){ console.log('[runUnifiedSimulation] 已废弃，使用自动刷新'); };

// (登录功能已移除) 保留访客标识占位，不再读取本地存储
(function initVisitorTag(){
    try {
        const qgUser = document.getElementById('qg-user');
        if(qgUser) qgUser.textContent = '访客';
    } catch(e){ console.warn('[VisitorInit] 访客标识初始化失败', e); }
})();

// 自动刷新逻辑（15s，带环进度显示）
(function mainRingAutoRefresh(){
    const REFRESH_INTERVAL=15000; // 15s
    const wrap=document.getElementById('main-refresh');
    const textEl=document.getElementById('main-refresh-text');
    const ring=wrap?.querySelector('.ring-fg');
    const CIRC=100; if(ring){ ring.style.strokeDasharray=CIRC; ring.style.strokeDashoffset=CIRC; }
    let busy=false; let next=Date.now()+REFRESH_INTERVAL;
    async function doRefresh(){
        if(busy) return; busy=true; if(textEl) textEl.textContent='刷新中…'; if(ring) ring.style.strokeDashoffset=0;
        wrap?.classList.add('busy');
        try{
            if(window.chartManager){
                await Promise.allSettled([
                    window.chartManager.createRubbishChart(true),
                    window.chartManager.createOceanCurrentChart(true),
                    window.chartManager.createTrendChart(),
                    window.chartManager.createSpeciesImpactChart(),
                    window.chartManager.createWaterQualityChart(),
                    window.chartManager.createMarineBioLossChart()
                ]);
            }
        }catch(e){ console.warn('[MainAutoRefresh] 失败',e); }
        finally{
            busy=false; next=Date.now()+REFRESH_INTERVAL; wrap?.classList.remove('busy');
            if(textEl) textEl.textContent='下次刷新 '+Math.ceil(REFRESH_INTERVAL/1000)+'s';
            if(ring) ring.style.strokeDashoffset=CIRC; // 归位
        }
    }
    setInterval(()=>{
        if(busy) return; const remain=next-Date.now(); if(remain<=0){ doRefresh(); return; }
        const pct=(REFRESH_INTERVAL-remain)/REFRESH_INTERVAL; if(ring) ring.style.strokeDashoffset=(CIRC - CIRC*pct);
        if(textEl) textEl.textContent='下次刷新 '+Math.ceil(remain/1000)+'s';
        // 快速概览剩余时间同步
        const leftEl=document.getElementById('qg-next-refresh');
        if(leftEl){ leftEl.textContent='下次刷新: '+Math.ceil(remain/1000)+'s'; }
    },1000);
    doRefresh();
})();

// ===== 取消 transform 缩放包装：直接使用真实尺寸填满视口，避免底部空白 =====
(function removeTransformZoom(){
    try {
        const body=document.body;
        const wrapper=document.getElementById('zoom-wrapper');
        if(wrapper){
            // 将子节点移回 body，并移除包装器
            const frag=document.createDocumentFragment();
            while(wrapper.firstChild){ frag.appendChild(wrapper.firstChild); }
            body.insertBefore(frag, wrapper);
            wrapper.remove();
        }
        body.classList.remove('zoom-locked','zoom-lte90');
        body.style.overflowX='hidden';
        const mc=document.querySelector('.main-content');
        if(mc){
            mc.style.minHeight='100vh';
            mc.style.display='flex';
            mc.style.flexDirection='column';
        }
        // 触发一次卡片高度重算
        setTimeout(()=>{ try{ window.forceAutoFit && window.forceAutoFit(); }catch(_){} },120);
    } catch(e){ console.warn('[removeTransformZoom] 失败', e); }
})();

// ===== 仅禁用浏览器缩放快捷：Ctrl/⌘ + 滚轮 / +/- / 0 / 触摸板捏合 =====
// 不再进行任何视觉缩放，只阻止默认缩放行为，避免页面比例被用户意外改动。
(function disableCtrlWheelZoom(){
    function blockZoomWheel(e){
        if(e.ctrlKey || e.metaKey){ e.preventDefault(); }
    }
    function blockKeyZoom(e){
        if((e.ctrlKey||e.metaKey) && ['+','=','-','0'].includes(e.key)){ e.preventDefault(); }
    }
    window.addEventListener('wheel', blockZoomWheel, {passive:false});
    window.addEventListener('keydown', blockKeyZoom, {passive:false});
    ['gesturestart','gesturechange','gestureend'].forEach(ev=>{
        window.addEventListener(ev, e=>{ e.preventDefault(); }, {passive:false});
    });
    console.log('[ZoomGuard] 已禁用 Ctrl/⌘ + 滚轮 和 +-0 快捷缩放');
    // 再次应用锁定
    if(!document.body.classList.contains('locked-zoom-90')) document.body.classList.add('locked-zoom-90');
})();

// ===== 布局切换工具：5x2 与 4x3 (通过 body class) =====
window.setFixedLayout=function(mode){
    document.body.classList.remove('force-layout-5x2','force-layout-4x3');
    if(mode==='5x2') document.body.classList.add('force-layout-5x2');
    else if(mode==='4x3') document.body.classList.add('force-layout-4x3');
    // 触发一次高度重算
    try{ window.forceAutoFit && window.forceAutoFit(); }catch(_){ }
};
// 默认开启 5x2 (若屏幕宽度足够且有 >=10 个卡片)
window.addEventListener('DOMContentLoaded',()=>{
    const cards=document.querySelectorAll('.dashboard-grid .huarong-piece');
    if(cards.length>=10){ document.body.classList.add('force-layout-5x2'); }
});

// 运行模式徽章已移除，保留空壳避免旧引用报错
window.__RUNTIME_BADGE_REMOVED__=true;
// 工具提示初始化
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(event) {
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = event.target.getAttribute('data-tooltip');
    
    tooltip.style.cssText = `
        position: absolute;
        background: rgba(22, 33, 62, 0.95);
        color: #ffffff;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 0.9rem;
        font-weight: 400;
        white-space: nowrap;
        z-index: 1000;
        pointer-events: none;
        border: 1px solid rgba(168, 218, 220, 0.3);
        backdrop-filter: blur(10px);
    `;
    
    document.body.appendChild(tooltip);
    
    const updatePosition = (e) => {
        tooltip.style.left = (e.clientX + 10) + 'px';
        tooltip.style.top = (e.clientY - tooltip.offsetHeight - 10) + 'px';
    };
    
    updatePosition(event);
    event.target.addEventListener('mousemove', updatePosition);
    event.target.tooltip = tooltip;
}

function hideTooltip(event) {
    if (event.target.tooltip) {
        document.body.removeChild(event.target.tooltip);
        delete event.target.tooltip;
    }
}

// 性能监控
function trackPerformance() {
    if ('performance' in window) {
        const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
        console.log(`页面加载时间: ${loadTime}ms`);
        
        // 如果有分析工具，可以在这里发送性能数据
    }
}

// 错误处理
window.addEventListener('error', (event) => {
    console.error('页面错误:', event.error);
    // 这里可以添加错误报告逻辑
});

// 移动设备适配
if ('ontouchstart' in window) {
    // 为触摸设备添加特殊处理
    document.body.classList.add('touch-device');
    
    // 防止双击缩放
    document.addEventListener('touchstart', (event) => {
        if (event.touches.length > 1) {
            event.preventDefault();
        }
    });
    
    // 触摸设备上的面板交互优化
    const panels = document.querySelectorAll('.panel');
    panels.forEach(panel => {
        panel.addEventListener('touchstart', () => {
            panel.style.transform = 'scale(0.98)';
        });
        
        panel.addEventListener('touchend', () => {
            panel.style.transform = 'scale(1)';
        });
    });
}

// ===== 保留功能完整的地球控制（避免被后面回退代码覆盖） =====
// ---- 地球就绪队列 ----
window.__globeReadyCallbacks = window.__globeReadyCallbacks || [];
function onGlobeReady(cb){
    if(window.globe3D){ cb(window.globe3D); } else { window.__globeReadyCallbacks.push(cb); }
}
// globe.js 创建后在 window.globe3D 赋值后追加: window.__globeReadyCallbacks?.forEach(fn=>{try{fn(window.globe3D)}catch(e){console.warn(e)}}); window.__globeReadyCallbacks=[];

// Legacy globe functions replaced with no-ops
function toggleAnimation() { return false; }
function resetView() { return false; }



// 页面卸载时的清理
window.addEventListener('beforeunload', () => { trackPerformance(); });

// ===== 视口宽高比监测，动态打标以优化不同比例屏幕卡片布局 =====
(function viewportAspectWatcher(){
    function apply(){
        const r=window.innerWidth/(window.innerHeight||1);
        document.body.classList.remove('ratio-ultrawide','ratio-wide','ratio-std','ratio-tall');
        if(r>=2){ document.body.classList.add('ratio-ultrawide'); }
        else if(r>=1.45){ document.body.classList.add('ratio-wide'); }
        else if(r<=0.85){ document.body.classList.add('ratio-tall'); }
        else { document.body.classList.add('ratio-std'); }
    }
    window.addEventListener('resize',()=>{ requestAnimationFrame(apply); });
    apply();
})();

// 数据模拟功能
async function runRubbishSimulation() {
    console.log('🚀 开始运行海洋垃圾产量模拟...');
    
    // 添加视觉反馈
    const button = document.querySelector('button[onclick="runRubbishSimulation()"]');
    if (button) {
        button.style.background = 'linear-gradient(135deg, #f59e0b, #d97706)';
        button.innerHTML = '⏳ 运行中...';
        button.disabled = true;
    }
    
    const statusElement = document.getElementById('simulation-status');
    const statusText = statusElement?.querySelector('.status-text');
    
    try {
        // 更新状态为运行中
        if (statusText) {
            statusText.textContent = '正在运行海洋垃圾产量模拟...';
            statusText.className = 'status-text status-running';
        }
        
        // 模拟执行时间
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 生成模拟的海洋垃圾数据
        const rubbishData = generateRubbishSimulationData();
        console.log('📊 海洋垃圾数据已生成:', rubbishData);
        
        if (statusText) {
            statusText.textContent = '海洋垃圾产量模拟完成！';
            statusText.className = 'status-text status-success';
        }
        
        // 更新图表数据（不显示额外结果卡片）
        console.log('🔄 开始更新图表数据...');
        await updateChartWithSimulationData('rubbish', rubbishData);
        
        // 使用全局清理函数清除所有弹窗
        window.clearAllPopups();
        
        // 延迟清理多次，确保彻底清除
        setTimeout(() => window.clearAllPopups(), 100);
        setTimeout(() => window.clearAllPopups(), 500);
        setTimeout(() => window.clearAllPopups(), 1500);
        setTimeout(() => window.clearAllPopups(), 3000);
        
        // 5秒后恢复原状态
        setTimeout(() => {
            if (statusText) {
                statusText.textContent = '准备就绪';
                statusText.className = 'status-text';
            }
            
            // 恢复按钮状态
            if (button) {
                button.style.background = '';
                button.innerHTML = '🏭 海洋垃圾产量模拟';
                button.disabled = false;
            }
        }, 5000);
        
    } catch (error) {
        console.error('❌ 海洋垃圾模拟失败:', error);
        statusText.textContent = '模拟执行失败，请检查控制台';
        statusText.className = 'status-text status-error';
        
        // 3秒后恢复原状态
        setTimeout(() => {
            statusText.textContent = '准备就绪';
            statusText.className = 'status-text';
        }, 3000);
    }
}

async function runOceanCurrentSimulation() {
    console.log('🌊 开始运行海洋环流数据模拟...');
    
    // 添加视觉反馈
    const button = document.querySelector('button[onclick="runOceanCurrentSimulation()"]');
    if (button) {
        button.style.background = 'linear-gradient(135deg, #06b6d4, #0891b2)';
        button.innerHTML = '⏳ 运行中...';
        button.disabled = true;
    }
    
    const statusElement = document.getElementById('simulation-status');
    const statusText = statusElement?.querySelector('.status-text');
    
    try {
        // 更新状态为运行中
        if (statusText) {
            statusText.textContent = '正在运行海洋环流数据模拟...';
            statusText.className = 'status-text status-running';
        }
        
        // 模拟执行时间
        await new Promise(resolve => setTimeout(resolve, 2500));
        
        // 生成模拟的海洋环流数据
        const oceanData = generateOceanCurrentSimulationData();
        console.log('🌊 海洋环流数据已生成:', oceanData);
        
        if (statusText) {
            statusText.textContent = '海洋环流数据模拟完成！';
            statusText.className = 'status-text status-success';
        }
        
        // 更新图表数据（不显示额外结果卡片）
        console.log('🔄 开始更新图表数据...');
        await updateChartWithSimulationData('ocean_current', oceanData);
        
        // 使用全局清理函数
        window.clearAllPopups();
        
        // 延迟清理多次，确保彻底清除
        setTimeout(() => window.clearAllPopups(), 100);
        setTimeout(() => window.clearAllPopups(), 500);
        setTimeout(() => window.clearAllPopups(), 1500);
        setTimeout(() => window.clearAllPopups(), 3000);
        
        // 5秒后恢复原状态
        setTimeout(() => {
            if (statusText) {
                statusText.textContent = '准备就绪';
                statusText.className = 'status-text';
            }
            
            // 恢复按钮状态
            if (button) {
                button.style.background = '';
                button.innerHTML = '🌊 海洋环流数据模拟';
                button.disabled = false;
            }
        }, 5000);
        
    } catch (error) {
        console.error('❌ 海洋环流模拟失败:', error);
        if (statusText) {
            statusText.textContent = '模拟执行失败，请检查控制台';
        }
        statusText.className = 'status-text status-error';
        
        // 3秒后恢复原状态
        setTimeout(() => {
            statusText.textContent = '准备就绪';
            statusText.className = 'status-text';
        }, 3000);
    }
}

// (已移除的模拟数据生成函数位置占位)

// 更新图表数据的辅助函数
async function updateChartWithSimulationData(simulationType, data) {
    console.log(`📈 准备更新 ${simulationType} 图表...`);
    console.log('🔍 window.chartManager 状态:', window.chartManager);
    console.log('🔍 数据内容:', data);
    
    // 强制初始化图表管理器（如果尚未初始化）
    if (!window.chartManager) {
        console.log('🔧 强制初始化图表管理器...');
        try {
            if (typeof ChartManager !== 'undefined') {
                window.chartManager = new ChartManager();
                // 等待初始化完成
                await window.chartManager.createCharts();
                console.log('✅ 图表管理器强制初始化完成');
            } else {
                console.error('❌ ChartManager类未找到');
                return; // 如果没有ChartManager，直接返回
            }
        } catch (error) {
            console.error('❌ 强制初始化图表管理器失败:', error);
            return; // 如果初始化失败，直接返回
        }
    }
    
    if (window.chartManager) {
        try {
            console.log('🎯 开始更新图表数据...');
            
            if (simulationType === 'rubbish') {
                console.log('📊 创建海洋垃圾数据图表...');
                console.log('🔍 调用 chartManager.createRubbishChart');
                await window.chartManager.createRubbishChart(data);
                console.log('✅ 海洋垃圾图表创建完成');
            } else if (simulationType === 'ocean_current') {
                console.log('🌊 创建海洋环流数据图表...');
                console.log('🔍 调用 chartManager.createOceanCurrentChart');
                await window.chartManager.createOceanCurrentChart(data);
                console.log('✅ 海洋环流图表创建完成');
            }
            
            console.log(`✅ ${simulationType} 图表数据已成功更新`);
            
            // 强制重新渲染图表
            setTimeout(() => {
                console.log('🔄 强制重新渲染所有图表...');
                if (window.Chart) {
                    Object.values(Chart.instances).forEach(chart => {
                        if (chart && chart.update) {
                            chart.update();
                        }
                    });
                }
            }, 100);
            
        } catch (error) {
            console.error(`❌ 更新 ${simulationType} 图表失败:`, error);
            console.error('错误详情:', error.stack);
            console.error('chartManager方法列表:', Object.getOwnPropertyNames(window.chartManager));
        }
    } else {
        console.error('❌ chartManager 仍未初始化');
        console.log('🔍 可用的全局对象:', Object.keys(window).filter(key => key.toLowerCase().includes('chart')));
        
        // 等待一段时间后重试
        setTimeout(async () => {
            if (window.chartManager) {
                console.log('🔄 延迟重试创建图表...');
                await updateChartWithSimulationData(simulationType, data);
            } else {
                console.error('❌ 图表管理器延迟重试仍失败');
            }
        }, 1000);
    }
}

// 测试函数 - 用于验证模拟图表功能
function testSimulationCharts() {
    console.log('🧪 开始测试模拟图表功能...');
    
    // 检查按钮是否存在
    const button1 = document.querySelector('button[onclick="runRubbishSimulation()"]');
    const button2 = document.querySelector('button[onclick="runOceanCurrentSimulation()"]');
    console.log('🔘 垃圾模拟按钮:', button1);
    console.log('🔘 环流模拟按钮:', button2);
    
    // 检查状态显示区域
    const statusElement = document.getElementById('simulation-status');
    console.log('📊 状态显示区域:', statusElement);
    
    // 检查图表管理器
    console.log('🎨 图表管理器:', window.chartManager);
    
    // 直接运行一次垃圾模拟测试
    if (window.chartManager) {
        console.log('🚀 直接测试垃圾图表创建...');
        const testData = generateRubbishSimulationData();
        window.chartManager.createRubbishChart(testData);
    }
}

// (Globe removed) 保留对 setGlobeSize 的引用为稳定的 no-op
window.setGlobeSize = window.setGlobeSize || (()=>{});
// 统一运行所有模拟
async function runAllSimulations() {
    console.log('🚀 开始运行全部数据模拟...');
    const statusElement = document.getElementById('simulation-status');
    const statusText = statusElement.querySelector('.status-text');
    
    try {
        // 更新状态为运行中
        statusText.textContent = '正在运行全部数据模拟...';
        statusText.className = 'status-text status-running';
        
        // 先运行垃圾模拟
        console.log('📊 步骤1: 运行垃圾产量模拟...');
        const rubbishData = generateRubbishSimulationData();
        await updateChartWithSimulationData('rubbish', rubbishData);
        
        // 等待一下再运行洋流模拟
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 运行洋流模拟
        console.log('🌊 步骤2: 运行海洋环流模拟...');
        const oceanData = generateOceanCurrentSimulationData();
        await updateChartWithSimulationData('ocean_current', oceanData);
        
        statusText.textContent = '全部数据模拟完成！';
        statusText.className = 'status-text status-success';
        
        // 5秒后恢复原状态
        setTimeout(() => {
            statusText.textContent = '准备就绪';
            statusText.className = 'status-text';
        }, 5000);
        
    } catch (error) {
        console.error('❌ 数据模拟失败:', error);
        statusText.textContent = '模拟执行失败，请检查控制台';
        statusText.className = 'status-text status-error';
        
        // 3秒后恢复原状态
        setTimeout(() => {
            statusText.textContent = '准备就绪';
            statusText.className = 'status-text';
        }, 3000);
    }
}

// 统一的旋转控制函数（去重保留）
function toggleRotation() { return false; }
function resetGlobe() { /* no-op (globe removed) */ }
function setGlobeSize(size) { /* no-op */ }

// ---- 统一按钮绑定：防止 inline onclick 失效时仍可响应 ----
function bindGlobeButtons() { /* removed with globe */ }
document.addEventListener('DOMContentLoaded', bindGlobeButtons);

// ---- ChartManager 回退 ----
if(!window.ChartManager){
    console.warn('未找到 ChartManager，创建回退管理器');
    window.ChartManager = class {
        constructor(){ this.instances={}; this.initBaseCharts(); }
        initBaseCharts(){
            const baseConfigs = {
                'source': {el:'source-chart', type:'doughnut', data:{labels:['A','B','C'], datasets:[{data:[30,40,30], backgroundColor:['#4dabf7','#1dd3b0','#ffaf40']}]}},
                'trend': {el:'trend-chart', type:'line', data:{labels:['2021','2022','2023','2024','2025'], datasets:[{label:'塑料量', data:[10,20,28,36,40], borderColor:'#4dabf7', tension:.3}]}}
            };
            Object.values(baseConfigs).forEach(cfg=>{ const c=document.getElementById(cfg.el); if(c && window.Chart){this.instances[cfg.el]=new Chart(c,{type:cfg.type,data:cfg.data,options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}}}});} });
        }
        createRubbishChart(simData){
            const yearly = document.getElementById('rubbish-yearly-chart');
            if(yearly && window.Chart){
                this.instances['rubbish-yearly-chart']?.destroy();
                this.instances['rubbish-yearly-chart']= new Chart(yearly,{type:'bar',data:{labels:simData.yearly_totals.labels, datasets:[{label:'年度垃圾量(吨)', data:simData.yearly_totals.values, backgroundColor:'#4dabf7'}]},options:{responsive:true,maintainAspectRatio:false,scales:{y:{ticks:{color:'#fff'},beginAtZero:true},x:{ticks:{color:'#fff'}}}}});
            }
            const city = document.getElementById('rubbish-city-chart');
            if(city && window.Chart){
                this.instances['rubbish-city-chart']?.destroy();
                this.instances['rubbish-city-chart']= new Chart(city,{type:'radar',data:{labels:simData.city_totals.labels,datasets:[{label:'城市垃圾量', data:simData.city_totals.values, backgroundColor:'rgba(77,171,247,0.3)', borderColor:'#4dabf7'}]},options:{plugins:{legend:{display:false}},scales:{r:{grid:{color:'rgba(255,255,255,0.15)'},angleLines:{color:'rgba(255,255,255,0.15)'},pointLabels:{color:'#fff'},ticks:{display:false}}}}});
            }
        }
        createOceanCurrentChart(oData){
            const river = document.getElementById('ocean-river-chart');
            if(river && window.Chart){
                const list = oData.rivers.top_rivers;
                this.instances['ocean-river-chart']?.destroy();
                this.instances['ocean-river-chart']= new Chart(river,{type:'bar',data:{labels:list.map(r=>r.river),datasets:[{label:'排放(吨/年)', data:list.map(r=>r.plastic_tons_per_year), backgroundColor:'#1dd3b0'}]},options:{responsive:true,maintainAspectRatio:false,scales:{y:{ticks:{color:'#fff'},beginAtZero:true},x:{ticks:{color:'#fff'}}}}});
            }
            const overview = document.getElementById('ocean-overview-chart');
            if(overview && window.Chart){
                this.instances['ocean-overview-chart']?.destroy();
                this.instances['ocean-overview-chart']= new Chart(overview,{type:'line',data:{labels:['Ⅰ','Ⅱ','Ⅲ','Ⅳ','Ⅴ'],datasets:[{label:'环流强度指数', data:[10,14,18,16,13], borderColor:'#1dd3b0', fill:false}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{ticks:{color:'#fff'}},x:{ticks:{color:'#fff'}}}}});
            }
        }
        animateChart(){/* 可扩展动画 */}
        handleResize(){Object.values(this.instances).forEach(ch=>ch.resize());}
        renderChart(){/* 密度图等留空 */}
    }
}
// 若仍未实例化，主动实例化
if(!window.chartManager){ try{ window.chartManager = new ChartManager(); }catch(e){ console.warn('图表回退初始化失败', e);} }

window.toggleAnimation = toggleAnimation; // now no-op
window.resetView = resetView; // now no-op
window.runRubbishSimulation = runRubbishSimulation;
window.runOceanCurrentSimulation = runOceanCurrentSimulation;
window.runAllSimulations = runAllSimulations;
window.testSimulationCharts = testSimulationCharts;
// 生态影响统计图表切换
function toggleEcoChart(element) {
    if (element.classList.contains('clicked')) {
        element.classList.remove('clicked');
        console.log('生态影响统计图表已隐藏');
    } else {
        element.classList.add('clicked');
        console.log('生态影响统计图表已显示');
        
        // 如果图表管理器存在，触发图表渲染
        if (window.chartManager && window.chartManager.renderChart) {
            setTimeout(() => {
                window.chartManager.renderChart('density');
            }, 300);
        }
    }
}

window.toggleRotation = toggleRotation;
window.resetGlobe = resetGlobe; // no-op

// 响应式布局处理
function handleResponsiveLayout() {
    const container = document.querySelector('.huarong-puzzle-container');
    const pieces = document.querySelectorAll('.huarong-piece');
    if (!container) return;
    
    // 获取容器尺寸
    const containerWidth = window.innerWidth;
    const containerHeight = window.innerHeight;
    
    console.log(`🔧 响应式布局调整: ${containerWidth}x${containerHeight}`);
    
    // 更新所有组件的自适应
    pieces.forEach(piece => {
        // 强制重新计算布局
        piece.style.transform = piece.style.transform;
        
        // 确保canvas图表重新适应
        const canvas = piece.querySelector('canvas');
        if (canvas && window.Chart) {
            const chartInstance = window.Chart.getChart(canvas);
            if (chartInstance) {
                setTimeout(() => {
                    chartInstance.resize();
                }, 100);
            }
        }
    });
    
    // (globe removed) skip globe sizing
    
    // 触发图表管理器重新布局
    if (window.chartManager && window.chartManager.handleResize) {
        window.chartManager.handleResize();
    }
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// 监听窗口大小变化
window.addEventListener('resize', throttle(handleResponsiveLayout, 250));

// 页面加载完成后初始化响应式布局（保留原复杂模拟函数，移除重复简化版）

// 删除重复简化版 toggleRotation/resetGlobe（已合并到上方）

window.addEventListener('load', () => {
    setTimeout(handleResponsiveLayout, 500);
});

// 导出响应式布局函数供外部调用
window.handleResponsiveLayout = handleResponsiveLayout;
window.toggleEcoChart = toggleEcoChart;
window.runRubbishSimulation = runRubbishSimulation;
window.runOceanCurrentSimulation = runOceanCurrentSimulation;

// ================== 视口缩放等级 -> 固定列数映射 ==================
// 需求映射 (推断自用户描述):
//  - 缩放 ≤ 90%: 4 列
//  - 90% < 缩放 < 125%: 3 列
//  - 125% ≤ 缩放 < 145%: 2 列
//  - ≥ 145%: 1 列
// 说明: 浏览器无原生 CSS Zoom 媒体查询; 采用 devicePixelRatio 近似。
// 若系统显示缩放 / 高 DPI 影响，可在下面函数中调整计算方式。
(function setupZoomColumns(){
    const CLS = ['zoom-lte90','zoom-gt90-lt125','zoom-gte125-lt145','zoom-gte145'];
    function detectZoom(){
        // 方案1: 直接使用 devicePixelRatio (最简单)
        // 方案2: outerWidth/innerWidth 备选; 若 DPR 异常可替换
        let z = (window.devicePixelRatio||1)*100;
        // 部分浏览器在极端缩放 rounding 差异, 做一次四舍五入
        z = Math.round(z);
        return z;
    }
    let lastBucket=null; let rafId=null;
    function apply(){
        const z = detectZoom();
        let bucket;
        if(z <= 90) bucket='zoom-lte90';
        else if(z < 125) bucket='zoom-gt90-lt125';
        else if(z < 145) bucket='zoom-gte125-lt145';
        else bucket='zoom-gte145';
        if(bucket!==lastBucket){
            lastBucket=bucket;
            document.body.classList.remove(...CLS);
            document.body.classList.add(bucket);
            // 列数变化后重新计算高度
            try{ window.forceAutoFit && window.forceAutoFit(); }catch(_){ }
            // 自适应降级：若最小宽度仍 < 240px 则再降 1 档，直到安全或只剩 1 列
            setTimeout(()=>{
                try{
                    const grid=document.querySelector('.dashboard-grid.glass-card.dynamic-auto');
                    if(!grid) return;
                    let safetyLoops=0;
                    while(safetyLoops<3){
                        const widths=[...grid.querySelectorAll('.huarong-piece')].map(p=>p.getBoundingClientRect().width).filter(w=>w>0);
                        if(!widths.length) break;
                        const min=Math.min(...widths);
                        if(min >= 240 || document.body.classList.contains('zoom-gte145')) break;
                        // 降级 bucket
                        if(document.body.classList.contains('zoom-lte90')){ document.body.classList.remove('zoom-lte90'); document.body.classList.add('zoom-gt90-lt125'); }
                        else if(document.body.classList.contains('zoom-gt90-lt125')){ document.body.classList.remove('zoom-gt90-lt125'); document.body.classList.add('zoom-gte125-lt145'); }
                        else if(document.body.classList.contains('zoom-gte125-lt145')){ document.body.classList.remove('zoom-gte125-lt145'); document.body.classList.add('zoom-gte145'); }
                        safetyLoops++;
                        window.forceAutoFit && window.forceAutoFit();
                    }
                    // 针对 >125% 的场景，进一步用网格宽度计算最大可放列数 (向下取整)
                    const gridW = grid.getBoundingClientRect().width;
                    const minCard = 260; const gap = parseFloat(getComputedStyle(grid).gap)||28;
                    // 计算理论最大列 (gridW + gap) / (minCard + gap)
                    let maxCols = Math.max(1, Math.floor((gridW + gap)/(minCard + gap)));
                    // 如果当前 bucket 期望列数 > maxCols，则强制使用动态列变量
                    const bucketDesired = document.body.classList.contains('zoom-lte90')?4: document.body.classList.contains('zoom-gt90-lt125')?3: document.body.classList.contains('zoom-gte125-lt145')?2:1;
                    if(bucketDesired > maxCols){
                        grid.classList.add('use-dyn-cols');
                        grid.style.setProperty('--dyn-cols', maxCols);
                    } else {
                        grid.classList.remove('use-dyn-cols');
                        grid.style.removeProperty('--dyn-cols');
                    }
                    // 再次统一高度
                    window.forceAutoFit && window.forceAutoFit();
                }catch(e){ }
            },80);
        }
    }
    function schedule(){ cancelAnimationFrame(rafId); rafId=requestAnimationFrame(apply); }
    window.addEventListener('resize', schedule, {passive:true});
    window.addEventListener('orientationchange', ()=>setTimeout(apply,120), {passive:true});
    document.addEventListener('DOMContentLoaded', ()=>{ apply(); setTimeout(apply,400); setTimeout(apply,1200); });
    window.debugZoomBucket=()=>({zoom:detectZoom(),bucket:lastBucket});
})();

// === 贴图切换桥接函数 ===

// 保留一次注册，避免多次覆盖
// (Globe removed) registerGlobeControlsOnce block stripped

    // ===== 地球控件强化绑定（二次保障） =====
    // (Globe removed) reinforceGlobeControls block stripped

    // === 追加：确保暂停后可以恢复旋转 ===
    // (Globe removed) override callback block stripped

// ===== 统一按钮事件委托，确保所有按钮可点击响应 =====
document.addEventListener('click', (e) => {
    const target = e.target.closest('button, .panel');
    if (!target) return;
    if (target.classList.contains('panel')) {
        animatePanel(target, e);
    }
});

// ================== 卡片放大预览功能 ==================
// 需求: 每个卡片点击可放大到屏幕 90% (非全屏)，带流畅动画；点击空白或关闭按钮退出。
// 实现策略:
// 1. 初次点击时记录卡片原始位置信息(getBoundingClientRect)和滚动偏移。
// 2. 通过克隆节点（或直接提升原节点并用占位符）实现过渡：这里选择“占位符 + 原节点绝对定位”方式，保留内部状态/图表引用。
// 3. 使用 transform/width/height 过渡到目标中心区域 (90vw x 90vh, 居中)。
// 4. 关闭时反向动画回到原位置，再还原文档流。
// 5. 避免同时多开；窗口 resize 时若处于放大态自动关闭，保持简单。
;(function enablePanelEnlarge(){
    const selector = '.huarong-piece';
    let active = null; // 当前放大卡片引用
    let placeholder = null; // 占位符
    let overlay = null;
    let closing = false;

    function createOverlay(){
        overlay = document.createElement('div');
        overlay.className='panel-enlarge-overlay';
        document.body.appendChild(overlay);
        requestAnimationFrame(()=>overlay.classList.add('visible'));
        overlay.addEventListener('click', ()=>closeActive());
    }
    let openedAt = 0;
    function openPanel(el){
        if(active || closing) return;
        active = el;
        const rect = el.getBoundingClientRect();
        console.log('[Enlarge] open panel rect=', rect);
        // 暂停溢出监控，避免放大过程产生误报 / Pause overflow detector to avoid false alarms
        try { window.__ENLARGING__ = true; window.overflowDetector?.stopMonitoring(); } catch(e){}
        // 保存原始内联样式，便于还原
        el.__origStyle = el.getAttribute('style') || '';
        // 创建占位符保持原网格布局不塌陷
        placeholder = document.createElement('div');
        placeholder.className='panel-placeholder';
        placeholder.style.width = rect.width + 'px';
        placeholder.style.height = rect.height + 'px';
        el.parentNode.insertBefore(placeholder, el);
        // 先创建遮罩（保证遮罩层级在卡片下）
        if(!overlay) createOverlay();
        // 把原节点提升到 body 直接子级，避免祖先 transform 影响 fixed/层级
        document.body.appendChild(el);
        Object.assign(el.style,{
            position:'fixed',
            left:rect.left + 'px',
            top:rect.top + 'px',
            width:rect.width + 'px',
            height:rect.height + 'px',
            margin:'0',
            zIndex:'150',
            maxWidth:'none',
            maxHeight:'none',
            overflow:'hidden',
            transformOrigin:'center center'
        });
        el.classList.add('panel-enlarging');
    // 初始缩放 & 透明度（开启动画）/ initial scale & opacity for entering animation
    // 初始缩放统一：不再对 piece-6 做水平偏移，保持原位置放大
    el.style.transform='scale(.94)';
    el.style.opacity='0.4';
    el.style.willChange='left,top,width,height,transform,opacity';
        // 关闭按钮
        const closeBtn = document.createElement('button');
        closeBtn.className='panel-close-btn';
        closeBtn.setAttribute('aria-label','关闭');
        closeBtn.innerHTML='×';
    closeBtn.addEventListener('click', (ev)=>{ ev.stopPropagation(); ev.preventDefault(); closeActive(); });
    closeBtn.style.zIndex='300';
        el.appendChild(closeBtn);
        // 防止内部点击（如 canvas / 控件）意外触发冒泡再次进入 openPanel 或触发文档委托逻辑
        // 使用单例模式绑定，避免重复添加；仅在放大状态下阻止冒泡，确保关闭后能再次触发打开逻辑
        if(!el.__stopPropHandler){
            el.__stopPropHandler = (innerEv)=>{
                if(el.classList.contains('panel-enlarging')){
                    innerEv.stopPropagation();
                }
            };
            el.addEventListener('click', el.__stopPropHandler, {capture:true});
        }
        // 观察尺寸变化（Chart.js 重绘或内容动态插入）保持卡片不“跳位置”
        try {
            const ro = new ResizeObserver(()=>{
                if(!el.classList.contains('panel-enlarging')){ ro.disconnect(); return; }
                // 限制内部内容超出时自动加滚动
                if(el.scrollHeight > el.clientHeight + 12){ el.style.overflowY='auto'; }
            });
            ro.observe(el);
            el.__enlargeRO = ro;
        } catch {}
        // 强制重排
        void el.offsetWidth;
        document.body.classList.add('panel-enlarge-active');
    // 目标尺寸（放大后的最终宽高）
    const targetW = Math.min(window.innerWidth*0.9, 1400);
    const targetH = Math.min(window.innerHeight*0.9, window.innerHeight - 40);
    
    // 直接计算屏幕中心位置 (Directly calculate screen center)
    const centerL = Math.max((window.innerWidth - targetW)/2, 12);
    const centerT = Math.max((window.innerHeight - targetH)/2, 16);

    // 保存数据用于关闭/resize
    el.__origRect = {left:rect.left, top:rect.top, width:rect.width, height:rect.height};
    el.__centerRect = {left:centerL, top:centerT, width:targetW, height:targetH};
    
    // 加入 transform / opacity 让关闭更顺滑 (包括缩放与淡出) / include transform+opacity for smoother close
        // 统一动画曲线：使用 cubic-bezier(0.25, 0.8, 0.25, 1)
        const UNIFIED_EASE = 'cubic-bezier(0.25, 0.8, 0.25, 1)';
        el.style.transition = `left .5s ${UNIFIED_EASE}, top .5s ${UNIFIED_EASE}, width .5s ${UNIFIED_EASE}, height .5s ${UNIFIED_EASE}, transform .5s ${UNIFIED_EASE}, opacity .4s ease`;
        openedAt = performance.now();
        requestAnimationFrame(()=>{ // 下一帧执行放大动画
            // 直接放大到屏幕中间 (Directly expand to screen center)
            el.style.left = centerL + 'px';
            el.style.top = centerT + 'px';
            el.style.width = targetW + 'px';
            el.style.height = targetH + 'px';
            el.style.overflowY='auto';
            el.style.overflowX='hidden';
            el.style.transform='scale(1)';
            el.style.opacity='1';
            // 弹性放大：使用关键帧动画进一步增加视觉反馈 / elastic keyframe
            el.style.animation = `panelPop .6s ${UNIFIED_EASE}`;
            // 动画后提升阴影层级视觉 (延迟执行) / elevate shadow after pop
            setTimeout(()=>{ if(el.classList.contains('panel-enlarging')) el.classList.add('panel-elevated'); }, 380);
        });
        
        // 动画结束后再注入扩展内容，减少布局抖动 / Inject extra content after animation settles
        setTimeout(()=>{ 
           try{ window.chartManager?.handleResize(); }catch(_){ }
           try{ injectExtraContentForPanel(el); }catch(e){ console.warn('扩展内容注入失败', e); }
        },540);
    }
    function closeActive(){
        if(!active || closing) return; closing=true;
        const rect = placeholder.getBoundingClientRect(); // 原位置目标
        console.log('[Enlarge] close -> target rect', rect);
        const el = active;
        const extra = el.querySelector('.panel-extra-wrapper');
        // 阶段1：内容淡出（保持尺寸不动）/ phase1: fade content only
        if(extra){ extra.style.transition='opacity .18s ease'; extra.style.opacity='0'; }
        el.classList.add('panel-closing-prep');
        // 移除弹性提升样式 / remove elevated style
        el.classList.remove('panel-elevated');
        document.body.classList.remove('panel-enlarge-active');
        // 阶段2：延迟后执行缩回 & 容器几何动画 / phase2 after short delay
        setTimeout(()=>{
            // 加入最终关闭 class / add closing class
            el.classList.add('panel-closing');
            
            // 确保关闭动画曲线一致 (Ensure consistent closing animation curve)
            const UNIFIED_EASE = 'cubic-bezier(0.25, 0.8, 0.25, 1)';
            el.style.transition = `left .5s ${UNIFIED_EASE}, top .5s ${UNIFIED_EASE}, width .5s ${UNIFIED_EASE}, height .5s ${UNIFIED_EASE}, transform .5s ${UNIFIED_EASE}, opacity .4s ease`;

            // 缩回原尺寸（平移回原位置）
            el.style.left = rect.left + 'px';
            el.style.top = rect.top + 'px';
            el.style.width = rect.width + 'px';
            el.style.height = rect.height + 'px';
            el.style.transform='scale(.9)';
            el.style.opacity='0';
            let finalized=false;
            function finalize(){
                if(finalized) return; finalized=true;
                if(el.__origStyle!==undefined){
                    el.setAttribute('style', el.__origStyle);
                    delete el.__origStyle;
                } else { el.removeAttribute('style'); }
                if(el.__enlargeRO){ try{ el.__enlargeRO.disconnect(); }catch(_){} delete el.__enlargeRO; }
                el.classList.remove('panel-enlarging','panel-closing','panel-closing-prep');
                const closeBtn = el.querySelector('.panel-close-btn'); closeBtn && closeBtn.remove();
                if(extra && extra.parentNode) extra.parentNode.removeChild(extra);
                placeholder && placeholder.parentNode && placeholder.parentNode.insertBefore(el, placeholder);
                placeholder && placeholder.remove();
                placeholder=null; active=null; closing=false;
                if(overlay){
                    overlay.classList.remove('visible');
                    overlay.classList.add('fading');
                    setTimeout(()=>{ overlay && overlay.remove(); overlay=null; }, 340);
                }
                try{ window.chartManager?.handleResize(); }catch(_){ }
                setTimeout(()=>{ try{ window.__ENLARGING__=false; window.overflowDetector?.startMonitoring(); }catch(e){} }, 240);
            }
            el.addEventListener('transitionend', (ev)=>{ if(['height','width','left','top'].includes(ev.propertyName)) finalize(); }, {once:true});
            setTimeout(finalize, 700); // fallback
        }, 160); // 先让内容淡出再缩回
    }
    // 事件绑定：区分已有特殊点击（如 piece-3 toggleEcoChart）避免冲突 -> 先允许默认逻辑执行，再放大
    document.addEventListener('click', (e)=>{
        const card = e.target.closest(selector);
        if(!card) return;
        // 已放大点击忽略（让 closeBtn/overlay 处理）
        if(active===card) return; // 避免重复触发
        // 若点击的是内部交互控件（select/checkbox/button/a）则不放大
        if(e.target.closest('button,select,input,label,a,.panel-close-btn')) return;
        // piece-3 的 toggleEcoChart 已绑定；放大不影响其内部逻辑
        openPanel(card);
    });
    window.addEventListener('keydown', (e)=>{ if(e.key==='Escape') closeActive(); });
    // 兜底：捕获阶段监听关闭按钮点击（防止某些冒泡阻断）
    document.addEventListener('click',(ev)=>{
        if(ev.target && ev.target.classList && ev.target.classList.contains('panel-close-btn')){
            ev.stopPropagation(); ev.preventDefault(); closeActive();
        }
    }, true);
    // 调整：窗口 resize 时不直接关闭，而是重新定位（避免用户触发 OS 窗口阴影变化导致立即收回）
    window.addEventListener('resize', ()=>{
        if(!active) return;
        const now = performance.now();
        // 放大不足 300ms 内的 resize 忽略，防止动画阶段抖动
        if(now - openedAt < 300) return;
        const el = active;
        const targetW = Math.min(window.innerWidth*0.9, 1400);
        const targetH = Math.min(window.innerHeight*0.9, window.innerHeight - 40);
        const centerL = Math.max((window.innerWidth - targetW)/2, 12);
        const centerT = Math.max((window.innerHeight - targetH)/2, 16);
        el.__centerRect = {left:centerL, top:centerT, width:targetW, height:targetH};
        el.style.left = centerL + 'px';
        el.style.top = centerT + 'px';
        el.style.width = targetW + 'px';
        el.style.height = targetH + 'px';
    });
    // 暴露全局关闭（可供其它脚本调用）
    window.closeEnlargedPanel = closeActive;
})();

// 防止链接按钮被覆盖层阻挡（如果存在意外层）
// 关键概念按钮工作正常，若未来出现层问题可取消注释：
// document.querySelectorAll('.concept-link').forEach(a=>a.style.pointerEvents='auto');

// 结束：主交互脚本已加载
// <-- 文件结束 (移除多余的包裹大括号) -->

// ================= Streamlit 自动探测与跳转增强 =================
// 目的: 统一端口探测 (8501-8510)、按钮状态动态更新、提供失败提示与再次检测入口
// ================= 漂流演示按钮初始化 =================
// 确保按钮显示正确的文本，不依赖Streamlit
;(function initDriftDemoButton(){
    function resetDemoBtn(){
        const btn = document.querySelector('.demo-btn[onclick*="navigateToDemo"]');
        if(!btn) return;
        
        // 重置按钮为原始状态
        btn.innerHTML = '🌊 详细漂流演示<span class="btn-arrow">→</span>';
        btn.removeAttribute('data-state');
        btn.classList.remove('streamlit-loading');
        btn.style.background = '';
        btn.disabled = false;
        
        console.log('✅ 漂流演示按钮已重置为正确文本');
    }

    // 页面就绪后立即重置按钮文本
    if(document.readyState === 'loading'){
        document.addEventListener('DOMContentLoaded', resetDemoBtn);
    } else {
        resetDemoBtn();
    }
    
    // 延迟再次确保按钮文本正确（防止其他脚本覆盖）
    setTimeout(resetDemoBtn, 100);
    setTimeout(resetDemoBtn, 500);

    // 清理：已移除不再需要的Streamlit相关样式
})();

// ===== 初始尺寸同步保障 =====
// 若初始地球默认逻辑已是 medium，但按钮可能被其它早期脚本标记在 small；
// 这里添加一次性的安全同步：在 DOMContentLoaded 与 globe ready 后都尝试一次。
// (Globe removed) ensureInitialMediumSize block stripped

// ================== Portrait Mode Detection (纵向模式检测) ==================
// 目的：在宽高比 < 1 时统一卡片尺寸（配合 styles.css 中的 portrait-mode 覆盖）
// 可通过给 <body> 添加 class="no-portrait-auto" 禁用该自动切换。
;(function setupPortraitMode(){
    if(window.__DASHBOARD_GRID__){ return; }
    let last=null; let ticking=false;
    let attempts=0; const MAX_ATTEMPTS=8;
    function evaluate(){
        ticking=false;
        if(!document.body){
            if(attempts++ < MAX_ATTEMPTS) return setTimeout(evaluate,80);
            return;
        }
        if(document.body.classList.contains('no-portrait-auto')) return;
        const isPortrait = window.innerHeight > window.innerWidth; // 简单判断
        if(isPortrait!==last){
            document.body.classList.toggle('portrait-mode', isPortrait);
            last=isPortrait;
            if(isPortrait){
                if(!document.body.classList.contains('unify-cards')){
                    document.body.classList.add('unify-cards');
                    console.log('[Portrait] 进入纵向 -> 强制 unify-cards (flex 模式)');
                }
                // 清除旧的区域定位或绝对定位尺寸，防止挤压
                document.querySelectorAll('.panel-grid-8 .huarong-piece').forEach(el=>{
                    el.style.gridArea='';
                    el.style.left='';
                    el.style.top='';
                    el.style.width='';
                    el.style.height='';
                    if(el.style.position==='absolute') el.style.position='';
                });
                // 检测列是否过窄，必要时启用 flex 回退
                setTimeout(()=>{
                    try{
                        const container=document.querySelector('.panel-grid-8');
                        if(!container) return;
                        const pieces=[...container.querySelectorAll('.huarong-piece')];
                        const tooNarrow = pieces.some(p=>p.getBoundingClientRect().width < 140);
                        // 额外判定：如果第一块宽度 < 容器宽度 * 0.25 说明仍被旧 grid-area 影响
                        const first=pieces[0];
                        let ratioOk=true;
                        if(first){
                           const cw=container.getBoundingClientRect().width;
                           const fw=first.getBoundingClientRect().width;
                           ratioOk = fw >= cw*0.25;
                        }
                        if(tooNarrow){
                           document.body.classList.add('portrait-flex-fallback');
                           console.log('[Portrait] 启用 flex 回退模式 (列过窄)');
                        } else if(!ratioOk){
                            document.body.classList.add('portrait-flex-fallback');
                            console.log('[Portrait] 启用 flex 回退模式 (首块比例异常)');
                        } else {
                           document.body.classList.remove('portrait-flex-fallback');
                        }
                    }catch(e){console.warn('Portrait fallback detect failed',e);}
                },90);
            } else {
                document.body.classList.remove('portrait-flex-fallback');
            }
            // 触发一次 resize 让 Chart.js / Globe 重算
            setTimeout(()=>window.dispatchEvent(new Event('resize')),60);
        }
        // 即使未触发状态变化也进行比例自检（防止最初判断失误）
        if(isPortrait){
            setTimeout(()=>{
               try{
                 const container=document.querySelector('.panel-grid-8');
                 if(!container) return;
                 const first=container.querySelector('.huarong-piece');
                 if(first){
                    const cw=container.getBoundingClientRect().width;
                    const fw=first.getBoundingClientRect().width;
                    if(fw < cw*0.25){
                       document.body.classList.add('portrait-flex-fallback');
                       console.log('[Portrait] 后置检查触发 flex 回退');
                    }
                 }
               }catch(e){}
            },220);
        }
    }
    function onResize(){
        if(!ticking){
            ticking=true;
            requestAnimationFrame(evaluate);
        }
    }
    window.addEventListener('resize', onResize, {passive:true});
    window.addEventListener('orientationchange', ()=>{ setTimeout(evaluate,50); }, {passive:true});
    // 多次延迟尝试，防止早期执行未正确判断
    const kickoffTimes=[0,120,400,900];
    kickoffTimes.forEach(t=>setTimeout(()=>evaluate(),t));
    // 提供手动触发工具
    window.__forcePortraitMode = function(force){
        if(typeof force==='boolean'){
            last=!force; // 让 evaluate 感知变化
            if(force){ window.innerWidth = 500; } // 仅用于模拟时；真实环境下无效（浏览器不允许直接改）
        }
        evaluate();
    };
    window.forceUnifiedCards = () => { document.body.classList.add('portrait-mode','portrait-flex-fallback'); console.log('[Portrait] 手动强制统一卡片布局'); };
})();

    // ========= 高缩放/网格压缩自动回退监视 =========
    ;(function setupGridCompressionFallback(){
        if(window.__DASHBOARD_GRID__){ return; }
        // 基于“单列理论宽度”而非逐块测量，避免某块被动画/隐藏影响
        const MIN_COL_WIDTH = 200; // 若 12 列平均宽度 < 200 即触发回退
        const EXIT_COL_WIDTH = 230; // 恢复到正常布局阈值
        let compressedState = false;
        let ro=null; let lastLogTs=0;

        window.debugGridCompression = function(){
            const container=document.querySelector('.huarong-puzzle-container.panel-grid-8');
            if(!container) return {compressedState, msg:'no container'};
            const cw=container.getBoundingClientRect().width;
            return {compressedState, colWidth:(cw/12).toFixed(1), cw};
        };

        function applyState(next){
            if(next === compressedState) return;
            compressedState = next;
            const container=document.querySelector('.huarong-puzzle-container.panel-grid-8');
            const pieces=[...document.querySelectorAll('.huarong-puzzle-container.panel-grid-8 .huarong-piece')];
            if(next){
                document.body.classList.add('grid-fallback');
                if(document.body.classList.contains('unify-cards')){
                    document.body.classList.remove('unify-cards');
                    console.info('[GridFallback] 移除 unify-cards 以避免冲突');
                }
                // 清理每块 gridArea 以使用流式回退
                pieces.forEach(p=>{ p.style.gridArea='auto'; });
                console.info('[GridFallback] 激活');
                try{ window.overflowDetector?.stopMonitoring(); }catch(e){}
            } else {
                document.body.classList.remove('grid-fallback');
                pieces.forEach(p=>{ if(p.style){ p.style.gridArea=''; } });
                console.info('[GridFallback] 解除');
                try{ window.overflowDetector?.startMonitoring(); }catch(e){}
            }
        }

        function scan(){
            const container=document.querySelector('.huarong-puzzle-container.panel-grid-8');
            if(!container) return;
            const cw=container.getBoundingClientRect().width;
            if(cw<=0) return;
            const colW = cw/12;
            const now=Date.now();
            if(now-lastLogTs>2500){ console.log('[GridFallback][scan] colWidth='+colW.toFixed(1)+' state='+(compressedState?'ON':'OFF')); lastLogTs=now; }
            if(!compressedState && colW < MIN_COL_WIDTH){ applyState(true); return; }
            if(compressedState && colW > EXIT_COL_WIDTH){ applyState(false); }
        }

        function initObservers(){
            const container=document.querySelector('.huarong-puzzle-container.panel-grid-8');
            if(!container) return;
            if(ro) return; // 已初始化
        ro=new ResizeObserver(()=> scan());
            ro.observe(container);
            pieceROs=[...container.querySelectorAll('.huarong-piece')].map(p=>{ const r=new ResizeObserver(()=>scan()); r.observe(p); return r;});
            scan();
        }

        document.addEventListener('DOMContentLoaded', ()=>{
            initObservers();
            // 多次兜底：防止早期样式尚未应用
            [120,400,900].forEach(t=> setTimeout(scan, t));
        });
        window.addEventListener('load', ()=> setTimeout(scan, 300));
        // 新增：监听窗口 resize（浏览器缩放会触发），再兜底一次
        window.addEventListener('resize', ()=> setTimeout(scan, 80), {passive:true});
        // 周期性兜底（防止极端情况下 ResizeObserver 被某些浏览器禁用）
        setInterval(()=>{ if(!compressedState) scan(); }, 5000);
        window.forceGridFallback = (on)=>{ applyState(!!on); if(on){ setTimeout(()=>scan(),120); } };
        // 强制移除 unify + 重新扫描
        window.forceDisableUnify = ()=>{ document.body.classList.remove('unify-cards'); console.log('[GridFallback] 已移除 unify-cards, 重新扫描'); scan(); };
        // 汇总调试状态
        window.layoutDebug = ()=>({
            gridFallback: compressedState,
            hasUnify: document.body.classList.contains('unify-cards'),
            colWidth: (function(){ const container=document.querySelector('.huarong-puzzle-container.panel-grid-8'); if(!container) return null; return (container.getBoundingClientRect().width/12).toFixed(1);} )(),
            thresholds:{MIN_COL_WIDTH, EXIT_COL_WIDTH}
        });
        console.log('[GridFallback] 监控脚本版本 v2 ready');
    })();

    // 安全清理：若不存在放大中的卡片却遗留 panel-enlarge-active，则移除（避免阻塞其它逻辑）
    setInterval(()=>{
        if(document.body.classList.contains('panel-enlarge-active')){
            if(!document.querySelector('.huarong-piece.panel-enlarging')){
                document.body.classList.remove('panel-enlarge-active');
            }
        }
    }, 2500);

    // =============== 全局列挤压监视 ===============
    ;(function setupGlobalCardCompressionWatch(){
        if(window.__DASHBOARD_GRID__){ return; }
        const MIN_ACCEPTABLE = 150; // px
        function scan(){
             const container=document.querySelector('.panel-grid-8');
             if(!container) return;
             try {
                 const cw = container.getBoundingClientRect().width;
                 // 新增：小屏（容器宽度 < 760px）直接启用统一 flex 布局，绕过复杂 grid-area，防止“小块挤进大块”现象
                 if(cw && cw < 760){
                     if(!document.body.classList.contains('unify-cards')){
                         document.body.classList.add('unify-cards');
                         console.log('[Unify] 小屏宽度触发统一布局 width='+cw.toFixed(1));
                         setTimeout(()=>window.dispatchEvent(new Event('resize')),40);
                     }
                     return; // 已强制统一，后续宽度差判定无需执行
                 } else if(cw && cw > 820 && document.body.classList.contains('unify-cards')) {
                     // 宽度恢复，允许回退（仅当不是由列压缩逻辑继续需要时）
                     // 先暂时移除，稍后依靠宽度差逻辑决定是否再加
                     document.body.classList.remove('unify-cards');
                     console.log('[Unify] 小屏恢复宽度，尝试回退统一布局 width='+cw.toFixed(1));
                 }
             } catch(e){}
             const pieces=[...container.querySelectorAll('.huarong-piece')];
             if(!pieces.length) return;
             const widths=pieces.map(p=>p.getBoundingClientRect().width).filter(w=>w>0);
             if(!widths.length) return;
             const min=Math.min(...widths);
             const avg=widths.reduce((a,b)=>a+b,0)/widths.length;
             // 若当前 unify-cards 且列宽已安全（> MIN_ACCEPTABLE*1.05），自动退出
             if(document.body.classList.contains('unify-cards') && min >= MIN_ACCEPTABLE*1.05){
                 document.body.classList.remove('unify-cards');
                 console.log('[Unify] 自动解除统一布局: minWidth='+min.toFixed(1));
             }
             if(min < MIN_ACCEPTABLE && avg > min*2){
                 if(!document.body.classList.contains('unify-cards')){
                     document.body.classList.add('unify-cards');
                     console.log(`[Unify] 触发统一卡片布局 min=${min.toFixed(1)} avg=${avg.toFixed(1)}`);
                     setTimeout(()=>window.dispatchEvent(new Event('resize')),40);
                 }
             } else if(min >= MIN_ACCEPTABLE*1.1 && document.body.classList.contains('unify-cards')){
                 document.body.classList.remove('unify-cards');
                 console.log('[Unify] 取消统一卡片布局');
             }
        }
        let resizeTimer=null; function schedule(){ clearTimeout(resizeTimer); resizeTimer=setTimeout(scan,140); }
        window.addEventListener('resize', schedule, {passive:true});
        document.addEventListener('DOMContentLoaded', ()=>{ setTimeout(scan,120); setTimeout(scan,500); });
        window.scanCardCompression = scan; // 手动触发
        window.forceSmallScreenLayout = ()=>{ document.body.classList.add('unify-cards'); console.log('[Unify] 手动强制小屏统一布局'); setTimeout(()=>window.dispatchEvent(new Event('resize')),30); };
        window.clearCompressionClasses = ()=>{ ['unify-cards','portrait-flex-fallback'].forEach(c=>document.body.classList.remove(c)); console.log('[Unify] 已清理压缩类'); };
    })();
// ================== 扩展放大内容注入 ==================
// 依据不同 piece-X 注入主题扩展内容（统计卡片 / 数据来源 / 说明文字）
// 设计原则：
// 1. 首次放大后延迟注入，避免初始动画卡顿
// 2. 关闭时移除，保持 DOM 干净
// 3. 仅使用纯前端合成数据，不请求网络
// 4. 样式依赖 main.html 中已存在的 .panel-extra-wrapper 等 class

function injectExtraContentForPanel(panel){
    if(!panel || panel.querySelector('.panel-extra-wrapper')) return; // 已存在不重复
    const pieceClass = [...panel.classList].find(c=>/^piece-\d+$/.test(c));
    if(!pieceClass) return;
    const wrapper = document.createElement('div');
    wrapper.className='panel-extra-wrapper';
    wrapper.style.opacity='0';
    // 轻微延迟渐显
    setTimeout(()=>{ wrapper.style.opacity='1'; },40);
    let content='';
    const builders = {
        'piece-1': buildPollutionOverviewExtra,
        'piece-2': buildSourceAttributionExtra,
        'piece-3': buildEcoImpactExtra,
        'piece-4': buildTrendInsightExtra,
        'piece-5': buildSimulationInsightExtra,
        'piece-6': buildCityDistributionExtra,
        'piece-7': buildRiverDischargeExtra,
        'piece-8': buildGyreOverviewExtra,
        'piece-9': buildBioLossExtra,
        'piece-10': buildWaterQualityExtra
    };
    try{
        content = (builders[pieceClass] ? builders[pieceClass]() : '<div class="panel-extra-section"><h3>扩展内容</h3><p>暂无额外信息。</p></div>');
    }catch(e){ content = '<div class="panel-extra-section"><h3>扩展内容</h3><p>构建失败: '+ (e.message||e) +'</p></div>'; }
    wrapper.innerHTML = content + buildCommonFooter();
    panel.appendChild(wrapper);
    // 尝试初始化扩展图表（如 eco detail）
    setTimeout(()=>{ try{ initExtraCharts(wrapper); }catch(e){ console.warn('extra charts init fail',e); } }, 60);
}

// ====== 各主题构建函数（返回 HTML 字符串） ======
function buildStatBox(label,value,unit='',trend=0){
   const trendCls = trend>0?'up': (trend<0?'down':'flat');
   const trendIcon = trend>0?'▲': (trend<0?'▼':'━');
   return `<div class="panel-stat-box ${trendCls}">
      <div class="label">${label}</div>
      <div class="val">${value}<span class="unit">${unit}</span></div>
      <div class="trend">${trendIcon} ${Math.abs(trend)}%</div>
   </div>`;
}
function section(title, body){
   return `<div class="panel-extra-section"><h3>${title}</h3>${body}</div>`;
}
function buildPollutionOverviewExtra(){
    const stats = [
        buildStatBox('全球塑料量','176','Mt',+3),
        buildStatBox('海面漂浮','2.1','Mt',+1),
        buildStatBox('海床沉积','94','Mt',+4),
        buildStatBox('微塑料比例','11.6','%',+2)
    ].join('');
    const body = `<div class="panel-stat-grid">${stats}</div>
    <p>该模块聚焦全球海洋塑料污染总体负荷的多仓位分布（表层 / 水柱 / 沉积）。数值为合成示例，用于交互演示。</p>`;
    return section('污染概览扩展', body);
}
function buildSourceAttributionExtra(){
    const body = `<ul class="mini-list">
      <li>河流输入占比 <strong>44%</strong></li>
      <li>沿海城市点源 <strong>27%</strong></li>
      <li>渔业与航运 <strong>18%</strong></li>
      <li>远洋扩散再循环 <strong>11%</strong></li>
    </ul>
    <p>来源解析强调陆源主导 + 海上次级释放的组合模式，可为政策聚焦提供优先序。</p>`;
    return section('来源结构洞察', body);
}
function buildEcoImpactExtra(){
        const body = `<p>生态影响维度涵盖 <strong>摄食</strong>、<strong>缠绕</strong>、<strong>栖息地改变</strong> 与 <strong>化学吸附</strong>。放大后可视为“快速研判面板”。</p>
        <div class="mini-badges">
            <span>海鸟受影响 ↑</span><span>珊瑚礁风险 中</span><span>浮游生物链路 待验证</span>
        </div>
        <div class="extra-chart-block">
                <canvas id="eco-impact-detail-chart" height="140"></canvas>
                <p class="chart-note">示例：不同生态压力因子相对强度 (合成数据)</p>
        </div>`;
        return section('生态影响说明', body);
}
function buildTrendInsightExtra(){
    const body = `<p>历史趋势基于合成年序列，演示<strong>增速放缓但绝对量仍上升</strong>的情形。可扩展叠加政策情景对比。</p>`;
    return section('趋势解读', body);
}
function buildSimulationInsightExtra(){
    const body = `<p>模拟模块在纯前端模式下使用随机种子 + 分布权重伪造时序，保持交互体验，同时避免后端依赖。</p>`;
    return section('模拟机制', body);
}
function buildCityDistributionExtra(){
    const body = `<p>城市分布图的扩展内容可包含“高贡献城市 Top5”以及针对性减排策略占位。</p>`;
    return section('城市分布扩展', body);
}
function buildRiverDischargeExtra(){
    const body = `<p>河流排放强调长尾：前若干条河流贡献显著，其余呈幂律衰减。示例用于说明集中治理优先级。</p>`;
    return section('河流排放解析', body);
}
function buildGyreOverviewExtra(){
    const body = `<p>环流数据概览聚焦五大洋垃圾带形成的滞留机制（地转平衡 + Ekman 汇聚）。</p>`;
    return section('环流结构解读', body);
}
function buildBioLossExtra(){
    const body = `<p>沿海城市生物减少图展示模拟的指数式衰减趋势。可在未来接入真实观测或遥感指标。</p>`;
    return section('生物多样性减少说明', body);
}
function buildWaterQualityExtra(){
    const body = `<p>水质指标（溶解氧 / 浊度 / 营养盐）当前为模拟数据，用于展示面板交互形态。</p>`;
    return section('水质影响说明', body);
}
function buildCommonFooter(){
    return `<div class="panel-extra-footer">数据均为演示用合成值 · 不代表真实观测 | Synthetic demo values</div>`;
}

// ====== 扩展图表初始化 ======
function initExtraCharts(scope){
    if(!scope) scope=document;
    const ecoCanvas = scope.querySelector('#eco-impact-detail-chart');
    if(ecoCanvas && !ecoCanvas.__inited){
        ecoCanvas.__inited=true;
        function spawn(){
            if(typeof Chart==='undefined'){ return setTimeout(spawn, 260); }
            try{
                const ctx=ecoCanvas.getContext('2d');
                const dataKeys=['摄食','缠绕','化学','栖息','迁移'];
                const vals=[72,54,43,38,27];
                new Chart(ctx,{type:'radar',data:{
                    labels:dataKeys,
                    datasets:[{label:'相对强度',data:vals,fill:true,backgroundColor:'rgba(80,180,255,0.18)',borderColor:'#4dbafd',pointBackgroundColor:'#a8e4ff',borderWidth:2}]
                },options:{responsive:true,plugins:{legend:{labels:{color:'#d8f3fd'}}},scales:{r:{angleLines:{color:'rgba(255,255,255,0.15)'},grid:{color:'rgba(255,255,255,0.12)'},pointLabels:{color:'#cce8f8',font:{size:12}},suggestedMin:0,suggestedMax:100,ticks:{display:false}}}}});
            }catch(e){ console.warn('eco detail chart fail',e); }
        }
        spawn();
    }
}
window.initExtraCharts = initExtraCharts;

// 对外暴露便于调试
window.injectExtraContentForPanel = injectExtraContentForPanel;
// 注入附加样式（若未存在） / inject supporting styles for close animation if absent
;(function ensureEnlargeAnimStyles(){
    if(document.getElementById('enlarge-extra-anim-style')) return;
    const st=document.createElement('style');
    st.id='enlarge-extra-anim-style';
    st.textContent=`
            @keyframes panelPop{0%{transform:scale(.94);opacity:.4}55%{transform:scale(1.01);}100%{transform:scale(1);opacity:1}}
            .panel-enlarging.panel-elevated{box-shadow:0 18px 42px -8px rgba(0,0,0,.55),0 0 0 1px rgba(255,255,255,0.08) inset;}
            .panel-enlarging{box-shadow:0 12px 32px -10px rgba(0,0,0,.45),0 0 0 1px rgba(255,255,255,0.05) inset;transition:box-shadow .5s cubic-bezier(0.25, 0.8, 0.25, 1);}
            .panel-enlarging.panel-closing-prep{filter:saturate(.9);}
            .panel-enlarging.panel-closing{opacity:.0;transform:scale(.9);} 
            body.panel-enlarge-active{overflow-x:hidden;} 
            .panel-enlarge-overlay.fading{opacity:0 !important;}
            .panel-extra-wrapper{transition:opacity .28s ease;}
    `;
    document.head.appendChild(st);
})();

// ===== 强制多列兜底: 宽度>1000 且第一行只有 1 个卡片时添加 body.force-multi-cols =====
document.addEventListener('DOMContentLoaded', ()=>{
    setTimeout(()=>{
        try{
            const grid=document.querySelector('.dashboard-grid.glass-card.dynamic-auto');
            if(!grid) return;
            const pieces=[...grid.querySelectorAll('.huarong-piece')];
            if(pieces.length<2) return; // 只有1个没意义
            const top=pieces[0].getBoundingClientRect().top;
            let firstRow=0; pieces.forEach(p=>{ if(Math.abs(p.getBoundingClientRect().top-top)<2) firstRow++;});
            if(window.innerWidth>1000 && firstRow===1){
                document.body.classList.add('force-multi-cols');
                console.log('[force-multi-cols] applied');
            }
        }catch(e){ console.warn('force-multi-cols fail',e); }
    },600);
});

// ================= 长期预测 (至2050) 组合柱+线 (改为前端轻量 MLP 深度学习预测) =================
;(function initLongForecast(){
    function waitChart(cb){ if(window.Chart) return cb(); document.addEventListener('chart-ready',cb,{once:true}); }
    waitChart(()=>{
        const cvs=document.getElementById('long-forecast-chart'); if(!cvs) return;
    // 基础：尝试复用 time series (若可用)；否则构造示例数据
        async function build(){
            let years=[], values=[];
            try{
                if(window.dataService?.getPlasticWasteTimeSeries){
                    const r=await window.dataService.getPlasticWasteTimeSeries({forceRefresh:false});
                        if(r?.data?.years && r?.data?.values){ years=r.data.years.slice(); values=r.data.values.slice(); }
                }
            }catch(e){ console.warn('[LongForecast] 获取历史失败, 使用示例',e); }
            if(!years.length){
                // 构造 2000-2024 递增序列 (示例)
                years = Array.from({length:25},(_,i)=>2000+i);
                let base=10; for(let i=0;i<years.length;i++){ base+= Math.random()*0.6 + 0.8; values.push(+base.toFixed(2)); }
            }
                        // ====== 深度学习：轻量 MLP (1 hidden layer) 拟合时间序列并外推 ======
                        // 数据标准化 (year 与 value 分开缩放)
                        const xs=years; const ys=values; const n=xs.length;
                        const xMin=Math.min(...xs), xMax=Math.max(...xs);
                        const yMin=Math.min(...ys), yMax=Math.max(...ys);
                        function normX(x){ return (x - xMin)/(xMax - xMin || 1); }
                        function denormY(y){ return y * (yMax - yMin || 1) + yMin; }
                        function normY(y){ return (y - yMin)/(yMax - yMin || 1); }
                        const X = xs.map(normX);
                        const Y = ys.map(normY);
                        // 模型结构: 输入1 -> 隐藏 H(8) ReLU -> 输出1 (线性)
                        const H=8; let W1=new Array(H).fill(0).map(()=> (Math.random()*2-1)*0.4 ); let B1=new Array(H).fill(0); let W2=new Array(H).fill(0).map(()=> (Math.random()*2-1)*0.4 ); let B2=0;
                        const lr=0.04; const epochs=Math.min(1500, 400 + n*40); // 动态迭代
                        function forward(x){ // x scalar
                            const z1=W1.map((w,i)=> x*w + B1[i]);
                            const a1=z1.map(v=> v>0?v:0); // ReLU
                            const yhat=a1.reduce((s,v,i)=> s+ v*W2[i], B2);
                            return {z1,a1,yhat};
                        }
                        function train(){
                            for(let ep=0; ep<epochs; ep++){
                                let dW1=new Array(H).fill(0), dB1=new Array(H).fill(0), dW2=new Array(H).fill(0), dB2=0, loss=0;
                                for(let i=0;i<n;i++){
                                    const x=X[i], target=Y[i];
                                    const {z1,a1,yhat}=forward(x);
                                    const err=yhat - target; loss+= err*err;
                                    // 输出层梯度
                                    for(let h=0; h<H; h++){ dW2[h]+= err * a1[h]; }
                                    dB2+=err;
                                    // 反向到隐藏
                                    for(let h=0; h<H; h++){
                                        const gradHidden = err * W2[h] * (z1[h]>0?1:0); // ReLU导数
                                        dW1[h]+= gradHidden * x;
                                        dB1[h]+= gradHidden;
                                    }
                                }
                                const scale = 1/n; loss*=scale;
                                for(let h=0; h<H; h++){
                                    W2[h]-= lr * dW2[h]*scale;
                                    W1[h]-= lr * dW1[h]*scale;
                                    B1[h]-= lr * dB1[h]*scale;
                                }
                                B2-= lr * dB2*scale;
                                if(ep%400===0) console.log('[MLP] epoch',ep,'loss',loss.toFixed(5));
                            }
                        }
                        train();
                        function predictYear(year){ const x=normX(year); const {yhat}=forward(x); return denormY(yhat); }
                        // 拟合曲线 (对全部标签生成平滑线)
                        const lastHistYear=years[years.length-1];
                        const futureYears=[]; const futureVals=[]; for(let y=lastHistYear+1;y<=2050;y++){ futureYears.push(y); futureVals.push(+predictYear(y).toFixed(2)); }
                        const fitLineYears=[...years, ...futureYears];
                        const fitLine = fitLineYears.map(y=> +predictYear(y).toFixed(2));
                        // 简易决定系数近似 (用训练集拟合值计算 R^2)
                        const yMean = ys.reduce((a,b)=>a+b,0)/ys.length;
                        const ssTot = ys.reduce((s,v)=> s+(v-yMean)**2,0);
                        const ssRes = ys.reduce((s,v,i)=> { const pv = fitLine[i]; return s+(v-pv)**2; },0);
                        const r2 = ssTot? 1-ssRes/ssTot : 0;
                        // 阈值：动态 = 最近真实值 *1.35
                        const threshold = +(values[values.length-1]*1.35).toFixed(2);
                        const warningDiv=document.getElementById('forecast-warning');
                        let exceedYear=null; for(let i=0;i<futureYears.length;i++){ if(futureVals[i] > threshold){ exceedYear=futureYears[i]; break; } }
                        if(exceedYear){ warningDiv.classList.add('active'); warningDiv.querySelector('.fw-year').textContent=exceedYear; warningDiv.querySelector('.fw-th').textContent=threshold; } else { warningDiv.classList.remove('active'); }
                        // 构图
                        const ctx=cvs.getContext('2d');
                        const gradientHist = ctx.createLinearGradient(0,0,0,cvs.height); gradientHist.addColorStop(0,'rgba(77,171,247,0.55)'); gradientHist.addColorStop(1,'rgba(77,171,247,0.05)');
                        const gradientFuture = ctx.createLinearGradient(0,0,0,cvs.height); gradientFuture.addColorStop(0,'rgba(34,197,194,0.65)'); gradientFuture.addColorStop(1,'rgba(34,197,194,0.10)');
                        const lineColor='rgba(255,230,109,1)';
                        const labels=[...years, ...futureYears];
                        const histBarData=years.map((y,i)=> values[i]);
                        const futureBarData=futureYears.map((y,i)=> futureVals[i]);
                        new Chart(cvs,{
                type:'bar',
                data:{
                    labels: labels.map(String),
                    datasets:[
                                                { type:'bar', label:'历史 (百万吨)', data:[...histBarData, ...new Array(futureYears.length).fill(null)], backgroundColor:gradientHist, borderColor:'rgba(77,171,247,1)', borderWidth:1.5, borderRadius:5, maxBarThickness:32 },
                                                { type:'bar', label:'预测 (百万吨, MLP)', data:[...new Array(years.length).fill(null), ...futureBarData], backgroundColor:gradientFuture, borderColor:'rgba(34,197,194,0.9)', borderWidth:1.2, borderRadius:5, maxBarThickness:32 },
                                                { type:'line', label:'MLP 拟合曲线', data:fitLine, borderColor:lineColor, backgroundColor:'rgba(255,230,109,0.12)', fill:false, tension:.25, borderWidth:2.4, pointRadius:0, yAxisID:'y' },
                                                { type:'line', label:'阈值', data: labels.map(()=>threshold), borderColor:'rgba(255,107,107,0.9)', borderWidth:1.8, borderDash:[6,4], pointRadius:0, fill:false, yAxisID:'y' }
                    ]
                },
                options:{
                    responsive:true, maintainAspectRatio:false,
                    interaction:{mode:'index', intersect:false},
                    plugins:{
                        legend:{labels:{color:'#cfefff', boxHeight:10,boxWidth:22}},
                        tooltip:{callbacks:{
                            label:(ctx)=> ctx.dataset.label+': '+ctx.parsed.y+' Mt'
                        }}
                    },
                    scales:{
                        x:{ticks:{color:'#bde5f5', maxRotation:0, autoSkip:true}, grid:{display:false}},
                        y:{ticks:{color:'#bde5f5'}, grid:{color:'rgba(189,229,245,0.12)'}, title:{display:true,text:'百万吨 (Mismanaged Plastic)',color:'#bde5f5',font:{size:12}}}
                    }
                }
            });
                        // 更新模型信息 & R² 近似
                        const eq=document.getElementById('forecast-reg-eq'); const r2El=document.getElementById('forecast-r2'); const thInfo=document.getElementById('forecast-threshold-info');
                        if(eq) eq.textContent = `模型: MLP(1x${H}) 迭代 ${epochs}`;
                        if(r2El) r2El.textContent = '拟合R²: '+r2.toFixed(3);
                        if(thInfo) thInfo.textContent = '阈值: '+threshold+' Mt (末年×1.35)';
        }
        build();
    });
})();

// ====== 新布局附加逻辑：仅问候语（登录功能已移除） ======
(function initGreeting(){
    function updateGreeting(){
        const h=new Date().getHours();
        let txt='欢迎';
        if(h>=5 && h<11) txt='早上好';
        else if(h>=11 && h<14) txt='中午好';
        else if(h>=14 && h<18) txt='下午好';
        else if(h>=18 && h<23) txt='晚上好';
        else txt='早点休息';
        const el=document.getElementById('greet-text');
        const timeEl=document.getElementById('current-time');
        if(el) {
            const base=txt;
            if(timeEl){
                el.childNodes.forEach(n=>{ if(n.nodeType===3){ n.textContent=base; }});
            } else {
                el.textContent=base;
            }
        }
        if(timeEl){
            const now=new Date();
            const hh=String(now.getHours()).padStart(2,'0');
            const mm=String(now.getMinutes()).padStart(2,'0');
            timeEl.textContent=`${hh}:${mm}`;
        }
    }
    updateGreeting();
    setInterval(updateGreeting, 60*1000);
})();

// ===== 3D 卡片倾斜交互效果（随鼠标位置） =====
(function initCardTilt(){
    try {
        const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        const finePointer = window.matchMedia('(pointer:fine)').matches;
        if(reduceMotion || !finePointer){ console.log('[CardTilt] 环境不支持或用户偏好禁用，跳过初始化'); return; }
        const grid = document.querySelector('.dashboard-grid');
        if(!grid){ console.warn('[CardTilt] 未找到 .dashboard-grid'); return; }
        grid.classList.add('tilt-active');
        const cards = grid.querySelectorAll('.huarong-piece.panel');
        const MAX_TILT = 18; // 最大倾斜角度 (增强版)
        const SCALE_DOWN = 0.97; // 按下微缩
        let enabled = true;
        cards.forEach(card=>{
            card.classList.add('tilt-card');
            // 注入 glare 层
            const glare = document.createElement('div');
            glare.className='card-glare';
            card.appendChild(glare);
            // 注入波纹层容器
            const rippleWrap=document.createElement('div');
            rippleWrap.className='card-ripple-stack';
            for(let i=0;i<3;i++){ const span=document.createElement('span'); span.className='ripple'; rippleWrap.appendChild(span); }
            card.appendChild(rippleWrap);
                        // 标记深度视差元素：按重要程度分配 depth (px)
                        const depthEls=[
                            ...card.querySelectorAll('.panel-title'),
                            ...card.querySelectorAll('.main-value'),
                            ...card.querySelectorAll('.large-stats-grid, .ocean-pollution-card, .yearly-controls'),
                            ...card.querySelectorAll('canvas'),
                            ...card.querySelectorAll('.panel-info, .yearly-kpis, #rubbish-forecast-table')
                        ];
                        depthEls.forEach((el,idx)=>{
                            const d = (idx===0?50: idx<3?40: idx<6?30: idx<12?22:16); // 递减深度
                            el.classList.add('depth-layer');
                            el.dataset.depth = d;
                        });
                        card.__depthEls = depthEls;
        });
        function applyTilt(card, e){
            if(!enabled) return;
            if(card.classList.contains('panel-enlarging')) return; // 放大预览时禁用
            const rect = card.getBoundingClientRect();
            const xPct = (e.clientX - rect.left) / rect.width; // 0..1
            const yPct = (e.clientY - rect.top) / rect.height; // 0..1
            const tiltX = (yPct - 0.5) * MAX_TILT; // rotateX
            const tiltY = (xPct - 0.5) * -MAX_TILT; // rotateY
            const shadowX = (xPct - 0.5) * 36; // 阴影偏移
            const shadowY = (yPct - 0.5) * 28;
            const intensity = 0.35 + Math.abs(xPct-0.5)*0.35 + Math.abs(yPct-0.5)*0.35; // 0.35~1.05
            const glare = card.querySelector('.card-glare');
            const ripples = card.querySelectorAll('.card-ripple-stack .ripple');
            if(card.__tiltRaf) cancelAnimationFrame(card.__tiltRaf);
            card.__tiltRaf = requestAnimationFrame(()=>{
                card.style.transform = `rotateX(${tiltX}deg) rotateY(${tiltY}deg)`;
                // 动态阴影：方向与鼠标相反，偏移可见
                card.style.boxShadow = `${-shadowX}px ${-shadowY}px 36px -12px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.10)`;
                if(glare){
                    const gx = xPct*100; const gy = yPct*100;
                    glare.style.transform = `translateZ(1px) scale(1.15)`;
                    glare.style.background = `radial-gradient(circle at ${gx}% ${gy}%, rgba(255,255,255,${0.55*intensity}), rgba(255,255,255,0.08) 42%, rgba(255,255,255,0) 72%)`;
                    glare.parentElement.classList.add('glare-active');
                }
                // 边缘高光 (CSS 变量)
                const rimAngle = (Math.atan2(tiltX, tiltY) * 180 / Math.PI + 360) % 360; // 根据倾斜方向旋转
                card.style.setProperty('--rim-angle', rimAngle+'deg');
                card.style.setProperty('--rim-opacity', (0.4 + 0.4*intensity).toFixed(3));
                // 波纹层动画：不同缩放与透明度
                if(ripples.length){
                    ripples.forEach((r,i)=>{
                        const baseScale = 0.35 + i*0.28 + intensity*0.15; // 递增扩散
                        r.style.transform = `translate(${(gx-50)/2}%, ${(gy-50)/2}%) scale(${baseScale})`;
                        r.style.opacity = (0.18 - i*0.04 + 0.25*intensity).toFixed(3);
                    });
                }
                // 深度视差：元素随鼠标反向轻移动 + translateZ
                if(card.__depthEls){
                  card.__depthEls.forEach(el=>{
                    const d = +el.dataset.depth || 0;
                    const dx = (xPct - 0.5) * -d * 0.4; // 水平位移缩放系数 0.4
                    const dy = (yPct - 0.5) * -d * 0.4; // 垂直位移
                    const dz = d * 0.6; // 视觉纵深
                    el.style.transform = `translate3d(${dx}px, ${dy}px, ${dz}px)`;
                  });
                }
            });
        }
        function resetTilt(card){
            if(card.__tiltRaf) cancelAnimationFrame(card.__tiltRaf);
            card.style.transform = '';
            card.style.boxShadow='';
            const glare = card.querySelector('.card-glare');
            if(glare){ glare.parentElement.classList.remove('glare-active'); }
            card.style.removeProperty('--rim-angle');
            card.style.removeProperty('--rim-opacity');
            if(card.__depthEls){ card.__depthEls.forEach(el=>{ el.style.transform=''; }); }
        }
        cards.forEach(card=>{
            card.addEventListener('mousemove', e=>applyTilt(card,e));
            card.addEventListener('mouseleave', ()=>resetTilt(card));
            card.addEventListener('mousedown', ()=>{ if(!enabled) return; card.style.transform += ' scale('+SCALE_DOWN+')'; });
            card.addEventListener('mouseup', ()=>resetTilt(card));
        });
        // 调试与动态控制 API
        window.disableCardTilt = function(){ enabled=false; cards.forEach(c=>{ c.style.transform=''; c.style.boxShadow=''; c.classList.remove('glare-active'); }); console.log('[CardTilt] 已禁用'); };
        window.enableCardTilt = function(){ enabled=true; console.log('[CardTilt] 已启用'); };
        console.log('[CardTilt] 初始化完成(含动态阴影+glare)，卡片数:', cards.length);
    } catch(e){ console.warn('[CardTilt] 初始化失败', e); }
})();