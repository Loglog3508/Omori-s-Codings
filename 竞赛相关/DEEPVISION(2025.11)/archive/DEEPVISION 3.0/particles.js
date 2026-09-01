// 全屏星空噪声流粒子（无中心圈、均匀分布、轻微闪烁）
class ParticleSystem {
    constructor() {
        this.canvas = document.getElementById('particle-canvas');
        this.ctx = this.canvas.getContext('2d');
    this.particles = [];      // 近景层
    this.farParticles = [];   // 远景层
        this.noiseZ = 0; // 噪声第三维动画
        this.settings = {
            density: 8000,        // 近景层密度
            farLayerFactor: 3.2,  // 远景层密度倍率(越大粒子越少 = density*factor)
            flickerAmp: 0.28,     // 轻微闪烁
            moveSpeedMin: 0.015,  // 粒子最小基础速度（像素/帧）
            moveSpeedMax: 0.05,   // 粒子最大基础速度（保持很慢）
            angleJitter: 0.015,   // 每帧角度随机偏移幅度
            driftBias: 0.0005,    // 全局微偏移（>0 让星空缓慢向一个方向漂）
            sizeMin: 0.6,
            sizeMax: 1.8,
            farSizeMin: 0.4,
            farSizeMax: 1.1,
            palette: [ '#ffffff', '#d9f1ff', '#b7e3ff', '#a8d7ff', '#d0f7ff' ],
            paletteFar: [ '#9fb9d8', '#b5d8f0', '#aecfea' ],
            colorJitter: 0.08,
            uniformMode: true,        // 仍然用均匀初始化
            uniformJitter: 0.35       // 抖动
        };
        this._init();
    }

    _init() {
        this._resize();
        this._createParticles();
        this._bind();
        this._loop();
    }

    _resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    _createParticles() {
        const { uniformMode, uniformJitter } = this.settings;
        const area = this.canvas.width * this.canvas.height;
        const nearCount = Math.floor(area / this.settings.density);
        const farCount = Math.floor(area / (this.settings.density * this.settings.farLayerFactor));
        this.particles.length = 0;
        this.farParticles.length = 0;
        // 均匀网格生成函数
        const buildLayer = (count, jitter, makeParticle) => {
            const cols = Math.ceil(Math.sqrt(count * (this.canvas.width / this.canvas.height)));
            const rows = Math.ceil(count / cols);
            const cellW = this.canvas.width / cols;
            const cellH = this.canvas.height / rows;
            let created = 0;
            for (let r = 0; r < rows && created < count; r++) {
                for (let c = 0; c < cols && created < count; c++) {
                    const jitterX = (Math.random() - 0.5) * 2 * jitter;
                    const jitterY = (Math.random() - 0.5) * 2 * jitter;
                    const x = (c + 0.5 + jitterX) * cellW;
                    const y = (r + 0.5 + jitterY) * cellH;
                    makeParticle(x,y);
                    created++;
                }
            }
        };
        if(uniformMode){
            buildLayer(nearCount, uniformJitter, (x,y)=> this.particles.push(this._baseParticle(x,y,false)) );
            buildLayer(farCount, uniformJitter, (x,y)=> this.farParticles.push(this._baseParticle(x,y,true)) );
        } else {
            for(let i=0;i<nearCount;i++) this.particles.push(this._randParticle());
            for(let i=0;i<farCount;i++) this.farParticles.push(this._randParticle());
        }
    }

    _randParticle() {
        return this._baseParticle(Math.random() * this.canvas.width, Math.random() * this.canvas.height);
    }

    _baseParticle(x, y, isFar) {
        const s = this.settings;
        const size = isFar
            ? Math.random()*(s.farSizeMax - s.farSizeMin)+s.farSizeMin
            : Math.random()*(s.sizeMax - s.sizeMin)+s.sizeMin;
        const palette = isFar ? s.paletteFar : s.palette;
        const color = palette[ Math.floor(Math.random()*palette.length) ];
        return {
            x, y,
            baseOpacity: (isFar? (Math.random()*0.35+0.08):(Math.random()*0.5+0.25)),
            size,
            phase: Math.random()*Math.PI*2,
            angle: Math.random()*Math.PI*2,
            speed: (Math.random()*(s.moveSpeedMax - s.moveSpeedMin)+s.moveSpeedMin) * (isFar?0.55:1),
            color,
            isFar,
            hueShift: (Math.random()-0.5)*s.colorJitter
        };
    }

    _bind() {
        window.addEventListener('resize', () => {
            this._resize();
            this._createParticles();
        });
    }

    // 简易 Perlin-like 噪声（基于栅格插值）
    _noise(x, y, z) {
        const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
        const xf = x - xi, yf = y - yi, zf = z - zi;
        const r = (n) => {
            const t = Math.sin(n * 127.1 + n * 311.7) * 43758.5453;
            return t - Math.floor(t);
        };
        function lerp(a,b,t){return a + (b-a)*t;}
        const c000 = r(xi*57 + yi*131 + zi*37);
        const c100 = r((xi+1)*57 + yi*131 + zi*37);
        const c010 = r(xi*57 + (yi+1)*131 + zi*37);
        const c110 = r((xi+1)*57 + (yi+1)*131 + zi*37);
        const c001 = r(xi*57 + yi*131 + (zi+1)*37);
        const c101 = r((xi+1)*57 + yi*131 + (zi+1)*37);
        const c011 = r(xi*57 + (yi+1)*131 + (zi+1)*37);
        const c111 = r((xi+1)*57 + (yi+1)*131 + (zi+1)*37);
        const x00 = lerp(c000, c100, xf);
        const x10 = lerp(c010, c110, xf);
        const x01 = lerp(c001, c101, xf);
        const x11 = lerp(c011, c111, xf);
        const y0 = lerp(x00, x10, yf);
        const y1 = lerp(x01, x11, yf);
        return lerp(y0, y1, zf);
    }

    _update() {
        const { flickerAmp, angleJitter, driftBias } = this.settings;
        this.noiseZ += 0.002; // 时间推进（用于闪烁节奏）
        const w = this.canvas.width, h = this.canvas.height;

        const updateOne = (p)=>{
            // 随机缓慢方向游走：角度轻微抖动
            p.angle += (Math.random()-0.5) * angleJitter;
            // 小的全局偏移 bias 让整体有极慢漂移
            p.x += Math.cos(p.angle) * p.speed + driftBias;
            p.y += Math.sin(p.angle) * p.speed + driftBias*0.2;
            // wrap
            if (p.x < 0) p.x += w; else if (p.x > w) p.x -= w;
            if (p.y < 0) p.y += h; else if (p.y > h) p.y -= h;
            // 闪烁
            p.phase += 0.02;
            p.opacity = p.baseOpacity + Math.sin(p.phase) * flickerAmp * p.baseOpacity * 0.4;
            if (p.opacity < 0) p.opacity = 0;
        };
        for(const p of this.farParticles) updateOne(p);
        for (const p of this.particles) updateOne(p);
    }

    _draw() {
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        ctx.save();
        const drawLayer = (arr)=>{
            for (const p of arr) {
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                // 解析颜色并应用轻微色调/透明度
                const col = p.color;
                // 颜色已是浅色 HEX，直接转为 rgba
                const r = parseInt(col.slice(1,3),16);
                const g = parseInt(col.slice(3,5),16);
                const b = parseInt(col.slice(5,7),16);
                ctx.fillStyle = `rgba(${r},${g},${b},${p.opacity})`;
                ctx.fill();
            }
        };
        drawLayer(this.farParticles);  // 远景先画
        drawLayer(this.particles);     // 近景后画
        ctx.restore();
    }

    _loop() {
        this._update();
        this._draw();
        requestAnimationFrame(() => this._loop());
    }
}

window.addEventListener('load', () => {
    window.__particleSystemInstance = new ParticleSystem();
});