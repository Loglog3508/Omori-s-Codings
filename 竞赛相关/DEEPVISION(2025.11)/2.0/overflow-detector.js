// 8组件溢出检测器 - 专门检测piece-7和piece-8的溢出问题
class ComponentOverflowDetector {
    constructor() {
        this.overflowThreshold = 10; // 10px容忍度
        this.checkInterval = 4000; // 放宽检测间隔，减少刷屏
        this.isMonitoring = false;
        this.disabled = false; // 全局禁用开关
        this._lastCriticalHash = ''; // 避免 piece-7/8 同一状态刷屏
        this._lastOverflowSignature='';
    this.scrolling=false;
    this._scrollTimer=null;
    this._lastScrollEnd=0; // 最近一次滚动结束时间戳，用于滚动后缓冲
    this.postScrollCooldown=420; // 滚动结束后 420ms 内不判定 bottom 溢出
    }
    
    startMonitoring() {
        if (this.isMonitoring) return;
    if (this.disabled || window.__DISABLE_OVERFLOW__) { console.log('🔧 溢出监控已禁用 (disabled flag)'); return; }
    if (document.body.classList.contains('grid-fallback') || document.body.classList.contains('unify-cards')) { console.log('🔧 跳过溢出监控: fallback/unify 模式中'); return; }
        
        console.log('🔍 开始监控组件溢出...');
        this.isMonitoring = true;
        // 监听滚动：滚动进行中不检测，避免视图内/可滚动区域被误判为 bottom 溢出
        const scrollHost = document.querySelector('.widgets-scroll') || window;
        scrollHost.addEventListener('scroll', ()=>{
            this.scrolling=true;
            clearTimeout(this._scrollTimer);
            this._scrollTimer=setTimeout(()=>{ this.scrolling=false; this._lastScrollEnd=Date.now(); }, 260); // 停止滚动 260ms 后恢复检测并记录时间
        }, {passive:true});
        
        this.checkAllComponents();
        this.monitoringInterval = setInterval(() => {
            this.checkAllComponents();
        }, this.checkInterval);
    }
    
    stopMonitoring() {
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.isMonitoring = false;
            console.log('⏹️ 停止监控组件溢出');
        }
    }
    
    checkAllComponents() {
        // 若处于全局放大或网格回退模式，直接跳过检测，避免误报
        if(document.body.classList.contains('panel-enlarge-active') || document.body.classList.contains('grid-fallback')){
            return [];
        }
        if(this.scrolling){ return []; }
        // 使用实际拼图容器作为边界，若不存在则退回 body
    const container = document.querySelector('.dashboard-grid') || document.querySelector('.huarong-puzzle-container.panel-grid-8') || document.querySelector('.container') || document.body;
        const containerRect = container.getBoundingClientRect();
        
        const components = [
            { selector: '.piece-1', name: '海洋污染' },
            { selector: '.piece-2', name: '塑料污染来源统计' },
            { selector: '.piece-3', name: '生态影响统计' },
            { selector: '.piece-4', name: '历史趋势' },
            { selector: '.piece-5', name: '年度误管理趋势' },
            { selector: '.piece-6', name: '主要国家误管理占比' },
            { selector: '.piece-7', name: '洋流速度分布' },
            { selector: '.piece-8', name: '洋流指标概览' },
            { selector: '.piece-9', name: '沿海城市生物减少' },
            { selector: '.piece-10', name: '沿海城市水质影响' }
        ];
        
        let overflowResults = [];
        
        components.forEach(comp => {
            const element = document.querySelector(comp.selector);
            if (element) {
                const result = this.checkComponentOverflow(element, containerRect, comp.name);
                if (result.hasOverflow) {
                    overflowResults.push(result);
                }
            }
        });
        
        // 特别检查piece-7和piece-8
        this.checkCriticalComponents();
        
        if (overflowResults.length > 0) {
            // 构造签名避免重复同一状态刷屏
            const signature = overflowResults.map(r=>r.componentName+':'+Object.keys(r.overflows).filter(d=>r.overflows[d]).join('.')).sort().join('|');
            if(signature !== this._lastOverflowSignature){
                this._lastOverflowSignature = signature;
                this.reportOverflow(overflowResults);
            }
        }
        
        return overflowResults;
    }
    
    checkComponentOverflow(element, containerRect, componentName) {
        const rect = element.getBoundingClientRect();
        // 判定滚动宿主，用于 bottom 修正
        const scrollHost = document.querySelector('.widgets-scroll');
        let right = rect.right > (containerRect.right + this.overflowThreshold);
    let bottom = rect.bottom > (containerRect.bottom + this.overflowThreshold);
        let left = rect.left < (containerRect.left - this.overflowThreshold);
        let top = rect.top < (containerRect.top - this.overflowThreshold);
        // bottom 溢出修正：若仍在 scrollHeight 范围内，不算溢出
        if(bottom && scrollHost){
            const hostRect = scrollHost.getBoundingClientRect();
            // 容器最大逻辑底部 (考虑 scrollHeight + hostRect.top)
            const logicalMaxBottom = hostRect.top + scrollHost.scrollHeight;
            // 条件1：元素实际 bottom 没超过逻辑最大底部
            const withinLogical = rect.bottom <= logicalMaxBottom + this.overflowThreshold;
            // 条件2：当前仍在滚动中或滚动刚结束的缓冲期内
            const inCooldown = this.scrolling || (Date.now() - this._lastScrollEnd < this.postScrollCooldown);
            if(withinLogical || inCooldown){ bottom=false; }
        }
        const overflows = { right, bottom, left, top };
        
        const hasOverflow = Object.values(overflows).some(overflow => overflow);
        // 额外规则：若仅有 bottom 溢出且该元素在容器底部 240px 以内，且容器具备滚动能力，则判定为“即将抵底”而非溢出
        try {
            const scrollHost = document.querySelector('.widgets-scroll');
            if(hasOverflow && overflows.bottom && !overflows.top && scrollHost){
                const hostRect = scrollHost.getBoundingClientRect();
                const distanceToBottom = (hostRect.top + scrollHost.scrollHeight) - rect.bottom;
                if(distanceToBottom > -this.overflowThreshold && distanceToBottom < 240){
                    overflows.bottom=false; // 取消 bottom 标记
                }
            }
        }catch{}
        const finalHasOverflow = Object.values(overflows).some(v=>v);
        
        return {
            componentName: componentName,
            element: element,
            hasOverflow: finalHasOverflow,
            overflows: overflows,
            rect: {
                width: rect.width,
                height: rect.height,
                left: rect.left - containerRect.left,
                top: rect.top - containerRect.top,
                right: rect.right - containerRect.left,
                bottom: rect.bottom - containerRect.top
            },
            containerSize: {
                width: containerRect.width,
                height: containerRect.height
            }
        };
    }
    
    checkCriticalComponents() {
        const piece7 = document.querySelector('.piece-7');
        const piece8 = document.querySelector('.piece-8');
        // 构造当前关键信息哈希，若未变化则节流日志
        let hashParts=[];
        if(piece7){ const r7=piece7.getBoundingClientRect(); hashParts.push('7:'+Math.round(r7.width)+'x'+Math.round(r7.height)); }
        if(piece8){ const r8=piece8.getBoundingClientRect(); hashParts.push('8:'+Math.round(r8.width)+'x'+Math.round(r8.height)); }
        const hash=hashParts.join('|');
        const sameHash = (hash && hash===this._lastCriticalHash);
        this._lastCriticalHash = hash || this._lastCriticalHash;
        if(sameHash){ return; } // 状态未变化，不再刷屏

        if (piece7) {
            const status7 = this.analyzeCriticalComponent(piece7, 'piece-7 (河流排放)');
            if (status7.hasIssue) {
                console.warn('🚨 piece-7 问题:', status7);
            }
        }
        
        if (piece8) {
            const status8 = this.analyzeCriticalComponent(piece8, 'piece-8 (环流数据概览)');
            if (status8.hasIssue) {
                console.warn('🚨 piece-8 问题:', status8);
            }
        }
    }
    
    analyzeCriticalComponent(element, name) {
        const rect = element.getBoundingClientRect();
        const container = document.querySelector('.huarong-puzzle-container.panel-grid-8') || document.querySelector('.container') || document.body;
        const containerRect = container.getBoundingClientRect();
        
        const issues = [];
        
        // 检查溢出
        if (rect.right > containerRect.right) {
            issues.push(`右侧溢出 ${Math.round(rect.right - containerRect.right)}px`);
        }
        if (rect.bottom > containerRect.bottom) {
            issues.push(`底部溢出 ${Math.round(rect.bottom - containerRect.bottom)}px`);
        }
        if (rect.left < containerRect.left) {
            issues.push(`左侧溢出 ${Math.round(containerRect.left - rect.left)}px`);
        }
        if (rect.top < containerRect.top) {
            issues.push(`顶部溢出 ${Math.round(containerRect.top - rect.top)}px`);
        }
        
        // 检查尺寸
        if (rect.width < 100) {
            issues.push(`宽度过小 ${Math.round(rect.width)}px`);
        }
        if (rect.height < 50) {
            issues.push(`高度过小 ${Math.round(rect.height)}px`);
        }
        
        return {
            name: name,
            hasIssue: issues.length > 0,
            issues: issues,
            dimensions: {
                width: Math.round(rect.width),
                height: Math.round(rect.height),
                left: Math.round(rect.left - containerRect.left),
                top: Math.round(rect.top - containerRect.top)
            }
        };
    }
    
    reportOverflow(overflowResults) {
    console.groupCollapsed('🚨 检测到组件溢出 ('+overflowResults.length+')');
        
        overflowResults.forEach(result => {
            console.warn(`${result.componentName}:`, {
                '溢出方向': Object.keys(result.overflows).filter(dir => result.overflows[dir]),
                '组件尺寸': `${Math.round(result.rect.width)}×${Math.round(result.rect.height)}px`,
                '组件位置': `(${Math.round(result.rect.left)}, ${Math.round(result.rect.top)})`,
                '容器尺寸': `${Math.round(result.containerSize.width)}×${Math.round(result.containerSize.height)}px`
            });
        });
        
        console.groupEnd();
        
    // 仅在首次或变化时显示一次视觉警告
    this.showOverflowWarning(overflowResults);
    }
    
    showOverflowWarning(overflowResults) {
        // 移除之前的警告
        const existingWarning = document.querySelector('.overflow-warning');
        if (existingWarning) {
            existingWarning.remove();
        }
        
        // 创建新的警告提示
        const warning = document.createElement('div');
        warning.className = 'overflow-warning';
        warning.style.cssText = `
            position: fixed;
            top: 20px;
            // 只在控制台输出，不再页面显示弹窗
            // 如需恢复页面警告，将下方注释去掉即可
            console.warn('组件溢出警告', overflowResults);
        }
    
    // 获取详细报告
    getDetailedReport() {
        const results = this.checkAllComponents();
        
        return {
            timestamp: new Date().toISOString(),
            overflowCount: results.length,
            overflows: results,
            screenInfo: {
                width: window.innerWidth,
                height: window.innerHeight,
                ratio: window.innerWidth / window.innerHeight,
                isLandscape: window.innerWidth > window.innerHeight
            }
        };
    }
}

// 全局实例
window.overflowDetector = new ComponentOverflowDetector();
// 提供全局开关便于调试
window.disableOverflowDetector = ()=>{ window.overflowDetector.disabled=true; window.overflowDetector.stopMonitoring(); console.log('[OverflowDetector] 已禁用'); };
window.enableOverflowDetector = ()=>{ window.overflowDetector.disabled=false; window.overflowDetector.startMonitoring(); console.log('[OverflowDetector] 已启用'); };

// 自动启动检测
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 组件溢出检测器已加载');
    
    // 等待布局初始化完成
    setTimeout(() => {
        window.overflowDetector.startMonitoring();
    }, 2000);
});

// 窗口大小变化时重新检测
window.addEventListener('resize', () => {
    setTimeout(() => {
        window.overflowDetector.checkNow();
    }, 300);
});

// 导出检测函数供外部调用
window.checkComponentOverflow = () => window.overflowDetector.checkNow();
window.getOverflowReport = () => window.overflowDetector.getDetailedReport();

console.log('✅ 组件溢出检测器脚本已加载完成');
// 兜底：再次暴露开关（防止因打包缓存覆盖）
if(!window.disableOverflowDetector){ window.disableOverflowDetector = ()=>{ window.overflowDetector.disabled=true; window.overflowDetector.stopMonitoring(); console.log('[OverflowDetector] 全局禁用'); }; }
if(!window.enableOverflowDetector){ window.enableOverflowDetector = ()=>{ window.overflowDetector.disabled=false; window.overflowDetector.startMonitoring(); console.log('[OverflowDetector] 全局启用'); }; }
window.__OVERFLOW_DETECTOR_VERSION__ = '2.0';