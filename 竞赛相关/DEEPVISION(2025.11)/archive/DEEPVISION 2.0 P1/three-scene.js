
// 封装 Three.js 场景逻辑
const ThreeScene = (function() {
    let container, scene, camera, renderer, composer;
    let group, objects = [];
    let bgMesh; // 背景网格
    let bloomPass; // 提升到模块作用域
    let isActive = false;
    let animationId;
    let idleTimer = null;
    let getDomElementsCallback = null; // 新增：获取 DOM 元素的回调
    const IDLE_TIMEOUT = 15000; // 15秒

    // 配置
    const CONFIG = {
        colors: {
            gold: 0xF5D061, 
            green: 0x1A5C45, 
            blue: 0x00BFFF,  
            dark: 0x010b19   
        },
        particleCount: 80,
        sphereRadius: 18, // 增大半径以减少重叠
        scatterRange: 40,
        cameraZ: 55 // 调整相机距离以适应更大的球体
    };

    const STATE = {
        mode: 'SPHERE',
        targetRotationX: 0,
        targetRotationY: 0,
        isHandDetected: false,
        activePhotoIndex: -1
    };

    // 初始化
    function init(domContainer, images, getDomElements) {
        container = domContainer;
        getDomElementsCallback = getDomElements;
        
        // Scene
        scene = new THREE.Scene();
        // 恢复默认背景设置，我们将使用视频平面作为背景
        scene.background = new THREE.Color(0x000000);

        // Camera
        camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.z = CONFIG.cameraZ;

        // Video Background
        const video = document.createElement('video');
        video.src = 'background.mp4';
        video.loop = true;
        video.muted = true;
        video.playsInline = true;
        video.crossOrigin = 'anonymous';
        video.play().catch(e => console.warn("Video autoplay blocked:", e));

        const videoTexture = new THREE.VideoTexture(video);
        videoTexture.minFilter = THREE.LinearFilter;
        videoTexture.magFilter = THREE.LinearFilter;
        videoTexture.format = THREE.RGBFormat;
        videoTexture.encoding = THREE.sRGBEncoding;

        const bgGeo = new THREE.PlaneGeometry(2, 2);
        const bgMat = new THREE.MeshBasicMaterial({ 
            map: videoTexture, 
            depthTest: false, // 不参与深度测试，始终在最远
            depthWrite: false,
            color: 0x666666 // 降低亮度至约 40% (配合 Bloom 阈值)
        });
        bgMesh = new THREE.Mesh(bgGeo, bgMat);
        // 将背景放置在相机后方足够远的位置
        scene.add(bgMesh);

        // Renderer
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false }); // 关闭 alpha
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.toneMapping = THREE.ReinhardToneMapping;
        renderer.toneMappingExposure = 1.2; // 稍微增加曝光度
        renderer.outputEncoding = THREE.sRGBEncoding; // 确保正确的颜色输出
        // renderer.setClearColor(0x000000, 0); // 不需要透明了
        renderer.domElement.style.position = 'absolute';
        renderer.domElement.style.top = '0';
        renderer.domElement.style.left = '0';
        renderer.domElement.style.zIndex = '90'; // 降低层级，确保侧边栏(z-index:100)可见
        renderer.domElement.style.opacity = '0'; // 初始隐藏
        renderer.domElement.style.transition = 'opacity 1s ease';
        renderer.domElement.style.pointerEvents = 'none'; // 初始不阻挡交互
        container.appendChild(renderer.domElement);

        // Lights
        const ambientLight = new THREE.AmbientLight(0x404040, 1.5);
        scene.add(ambientLight);
        const pointLight = new THREE.PointLight(CONFIG.colors.gold, 2, 100);
        pointLight.position.set(15, 15, 15);
        scene.add(pointLight);
        const blueLight = new THREE.PointLight(CONFIG.colors.blue, 2, 100);
        blueLight.position.set(-15, -15, 15);
        scene.add(blueLight);
        const topLight = new THREE.DirectionalLight(0xffffff, 0.5);
        topLight.position.set(0, 20, 0);
        scene.add(topLight);

        // Post-processing
        const renderScene = new THREE.RenderPass(scene, camera);
        // 不需要透明清除
        // renderScene.clearColor = new THREE.Color(0, 0, 0);
        // renderScene.clearAlpha = 0;
        
        bloomPass = new THREE.UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 1.5, 0.4, 0.85);
        bloomPass.threshold = 0.9; // 提高阈值，仅让高亮粒子发光，照片不发光
        bloomPass.strength = 1.2; 
        bloomPass.radius = 0.5;
        
        // 恢复默认 RenderTarget
        composer = new THREE.EffectComposer(renderer);
        composer.addPass(renderScene);
        composer.addPass(bloomPass);

        // Objects
        group = new THREE.Group();
        scene.add(group);
        createObjects(images);

        // Initial resize to set background size
        onResize();

        // Resize
        window.addEventListener('resize', onResize);

        // Gesture Listener
        window.addEventListener('gesture-raw', handleGesture);
        
        // 监听强制启动事件 (来自 gesture-control.js)
        window.addEventListener('gesture-start-3d', () => {
            if (!isActive) start();
        });
    }

    function start() {
        isActive = true;
        renderer.domElement.style.opacity = '1';
        renderer.domElement.style.pointerEvents = 'auto';
        
        // 尝试播放背景视频 (如果之前被阻止)
        if(bgMesh && bgMesh.material.map && bgMesh.material.map.image) {
            bgMesh.material.map.image.play().catch(()=>{});
        }
        
        animate();
    }

    function createObjects(images) {
        // 增强材质发光效果
        const goldMat = new THREE.MeshStandardMaterial({ 
            color: CONFIG.colors.gold, 
            metalness: 0.9, 
            roughness: 0.1, 
            emissive: 0xF5D061, 
            emissiveIntensity: 2.0 
        });
        const greenMat = new THREE.MeshStandardMaterial({ 
            color: CONFIG.colors.green, 
            metalness: 0.4, 
            roughness: 0.7, 
            flatShading: true,
            emissive: 0x1A5C45,
            emissiveIntensity: 1.5
        });
        const glassMat = new THREE.MeshPhysicalMaterial({ 
            color: 0xe0fbfc, 
            metalness: 0.1, 
            roughness: 0.05, 
            transmission: 0.9, 
            transparent: true, 
            thickness: 0.5,
            emissive: 0xe0fbfc,
            emissiveIntensity: 1.0
        });

        const sphereGeo = new THREE.SphereGeometry(0.5, 16, 16);
        const boxGeo = new THREE.BoxGeometry(0.8, 0.8, 0.8);
        const bottleGeo = new THREE.CylinderGeometry(0.3, 0.3, 1.2, 12);

        // Geometry Particles
        for (let i = 0; i < CONFIG.particleCount; i++) {
            let mesh;
            const rand = Math.random();
            if (rand < 0.4) mesh = new THREE.Mesh(sphereGeo, goldMat);
            else if (rand < 0.7) mesh = new THREE.Mesh(boxGeo, greenMat);
            else mesh = new THREE.Mesh(bottleGeo, glassMat);

            const scale = 0.5 + Math.random() * 0.8;
            mesh.scale.set(scale, scale, scale);

            const phi = Math.acos(-1 + (2 * i) / CONFIG.particleCount);
            const theta = Math.sqrt(CONFIG.particleCount * Math.PI) * phi;
            
            // 增加径向随机性，使粒子分布在不同半径上，增加立体感
            // 原来是 CONFIG.sphereRadius * (0.8 + Math.random() * 0.4)
            // 现在范围扩大到 0.6 ~ 1.4 倍半径
            const r = CONFIG.sphereRadius * (0.6 + Math.random() * 0.8);
            
            const sX = r * Math.cos(theta) * Math.sin(phi);
            const sY = r * Math.sin(theta) * Math.sin(phi);
            const sZ = r * Math.cos(phi);

            const scX = (Math.random() - 0.5) * CONFIG.scatterRange;
            const scY = (Math.random() - 0.5) * CONFIG.scatterRange;
            const scZ = (Math.random() - 0.5) * CONFIG.scatterRange * 0.5;

            mesh.position.set(sX, sY, sZ);
            mesh.lookAt(0, 0, 0);
            // 随机自转
            mesh.rotation.set(Math.random()*Math.PI, Math.random()*Math.PI, Math.random()*Math.PI);
            
            group.add(mesh);
            objects.push({ mesh, spherePos: new THREE.Vector3(sX, sY, sZ), scatterPos: new THREE.Vector3(scX, scY, scZ), sphereRot: mesh.rotation.clone(), scatterRot: new THREE.Euler(Math.random()*Math.PI, Math.random()*Math.PI, 0), isPhoto: false });
        }

        // Photos
        // 使用自定义加载器以兼容 file:// 协议
        const loadTexture = (url, onSuccess, onError) => {
            const img = new Image();
            // 尝试不设置 crossOrigin，这对于本地文件通常更有效
            // img.crossOrigin = "Anonymous"; 
            img.onload = () => {
                const texture = new THREE.Texture(img);
                // 修复：非 2 的幂次方 (NPOT) 图片处理
                texture.minFilter = THREE.LinearFilter;
                texture.magFilter = THREE.LinearFilter;
                texture.generateMipmaps = false; 
                
                // 修复：颜色空间和格式
                texture.encoding = THREE.sRGBEncoding;
                texture.format = THREE.RGBFormat; // 强制 RGB，避免透明度问题
                
                texture.needsUpdate = true;
                onSuccess(texture);
            };
            img.onerror = (err) => {
                console.warn("Image load failed:", url, err);
                if (onError) onError(err);
            };
            img.src = url;
        };

        // const EXTENDED_IMAGES = [...images, ...images]; // Double up -> Removed to reduce clutter
        const EXTENDED_IMAGES = images;
        
        // Placeholder generator
        function createPlaceholder(index) {
            const canvas = document.createElement('canvas');
            canvas.width = 256; canvas.height = 192;
            const ctx = canvas.getContext('2d');
            // 使用更亮的颜色以便调试
            ctx.fillStyle = `hsl(${index * 20}, 70%, 40%)`;
            ctx.fillRect(0,0,256,192);
            ctx.fillStyle = 'white';
            ctx.font = '30px Arial';
            ctx.fillText('Loading...', 50, 100);
            return new THREE.CanvasTexture(canvas);
        }

        EXTENDED_IMAGES.forEach((url, i) => {
            const h = 6; const w = 8; // 再次增大尺寸 (原 4.5, 6)
            const geo = new THREE.PlaneGeometry(w, h);
            // 确保颜色为纯白，避免叠加变暗
            const mat = new THREE.MeshBasicMaterial({ 
                map: createPlaceholder(i), 
                side: THREE.DoubleSide, 
                transparent: false, // 加载完成后关闭透明，避免排序问题
                color: 0xdddddd, // 稍微降低亮度，避免过曝
                toneMapped: false // 关键修复：关闭色调映射，保持图片原始亮度
            });
            const mesh = new THREE.Mesh(geo, mat);

            const phi = Math.acos(-1 + (2 * i) / EXTENDED_IMAGES.length);
            const theta = Math.sqrt(EXTENDED_IMAGES.length * Math.PI * 4) * phi;
            
            // 修改：让照片分布在球体内部和表面
            // 30% 的概率在内部 (0.4~0.8倍半径)，70% 的概率在表面附近 (0.9~1.1倍半径)
            let r;
            if (Math.random() < 0.3) {
                r = CONFIG.sphereRadius * (0.4 + Math.random() * 0.4);
            } else {
                r = CONFIG.sphereRadius * (0.9 + Math.random() * 0.2);
            }
            
            const sX = r * Math.cos(theta) * Math.sin(phi);
            const sY = r * Math.sin(theta) * Math.sin(phi);
            const sZ = r * Math.cos(phi);

            const scX = (Math.random() - 0.5) * CONFIG.scatterRange * 1.4;
            const scY = (Math.random() - 0.5) * CONFIG.scatterRange * 1.4;
            const scZ = (Math.random() - 0.5) * CONFIG.scatterRange * 1.0;

            mesh.position.set(sX, sY, sZ);
            mesh.lookAt(new THREE.Vector3(sX, sY, sZ).multiplyScalar(2));

            group.add(mesh);
            const currentObj = { 
                mesh, 
                spherePos: new THREE.Vector3(sX, sY, sZ), 
                scatterPos: new THREE.Vector3(scX, scY, scZ), 
                sphereRot: mesh.rotation.clone(), 
                scatterRot: new THREE.Euler(0,0,0), 
                isPhoto: true, 
                originalScale: new THREE.Vector3(1,1,1),
                wallPos: new THREE.Vector3(0,0,0), // 新增：记录墙面位置
                wallScale: new THREE.Vector3(1,1,1) // 新增：记录墙面缩放
            };
            objects.push(currentObj);

            loadTexture(url, (tex) => {
                mat.map = tex; 
                mat.opacity = 1.0; 
                mat.needsUpdate = true;
                const aspect = tex.image.width / tex.image.height;
                
                // 统一大小逻辑：长边对齐
                let sx, sy;
                if (aspect >= 1) {
                    sx = 1;
                    sy = (w / h) / aspect;
                } else {
                    sx = (h / w) * aspect;
                    sy = 1;
                }
                
                mesh.scale.set(sx, sy, 1);
                // 更新原始比例，以便在动画中恢复
                currentObj.originalScale.set(sx, sy, 1);
            });
        });
    }

    function onResize() {
        if(!camera || !renderer) return;
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
        if(composer) composer.setSize(window.innerWidth, window.innerHeight);
        
        // 更新背景平面尺寸以覆盖视野
        if (bgMesh) {
            const dist = camera.position.z - bgMesh.position.z; // 55 - (-100) = 155
            const vFOV = THREE.Math.degToRad(camera.fov); // 60度
            const height = 2 * Math.tan(vFOV / 2) * dist;
            const width = height * camera.aspect;
            bgMesh.scale.set(width / 2, height / 2, 1); // PlaneGeometry 是 2x2，所以除以 2
        }
    }

    function animate() {
        if (!isActive) return;
        animationId = requestAnimationFrame(animate);
        TWEEN.update();

        // Auto rotate or Hand rotate
        if (STATE.mode === 'SPHERE' && !STATE.isHandDetected) {
            group.rotation.y += 0.002;
            group.rotation.x += 0.001;
        } else if (STATE.mode === 'SCATTER') {
            group.rotation.y += (STATE.targetRotationY - group.rotation.y) * 0.05;
            group.rotation.x += (STATE.targetRotationX - group.rotation.x) * 0.05;
        }

        // Floating
        const time = Date.now() * 0.001;
        objects.forEach((obj, i) => {
            if (STATE.mode === 'SCATTER' && obj !== objects[STATE.activePhotoIndex]) {
                obj.mesh.position.y += Math.sin(time + i) * 0.02;
            }
            // 球态下非图片粒子的随机移动
            if (STATE.mode === 'SPHERE' && !obj.isPhoto) {
                obj.mesh.position.x += Math.sin(time * 0.5 + i) * 0.005;
                obj.mesh.position.y += Math.cos(time * 0.3 + i) * 0.005;
                obj.mesh.position.z += Math.sin(time * 0.7 + i) * 0.005;
            }
        });

        composer.render();
    }

    function transformTo(mode, targetIndex = -1) {
        if (STATE.mode === mode && mode !== 'DETAIL') return;
        STATE.mode = mode;
        STATE.activePhotoIndex = targetIndex;
        const duration = 1500;
        const easing = TWEEN.Easing.Quadratic.InOut;

        // 动态调整 Bloom 强度：球体模式发光，展开/详情模式不发光
        if (bloomPass) {
            const targetStrength = (mode === 'SPHERE') ? 1.5 : 0;
            new TWEEN.Tween(bloomPass).to({ strength: targetStrength }, duration).easing(easing).start();
        }

        objects.forEach((obj, idx) => {
            let targetPos, targetRot, targetScale;
            if (mode === 'SPHERE') {
                targetPos = obj.spherePos; targetRot = obj.sphereRot; targetScale = obj.isPhoto ? obj.originalScale : obj.mesh.scale;
                if(obj.isPhoto) new TWEEN.Tween(obj.mesh.material).to({opacity: 1.0}, duration).start();
            } else if (mode === 'SCATTER') {
                targetPos = obj.scatterPos; targetRot = obj.scatterRot; targetScale = obj.isPhoto ? obj.originalScale : obj.mesh.scale;
                if(obj.isPhoto) new TWEEN.Tween(obj.mesh.material).to({opacity: 1.0}, duration).start();
            } else if (mode === 'DETAIL') {
                if (idx === targetIndex) {
                    // 调整选中后的缩放比例和位置，避免遮挡右侧侧边栏
                    targetPos = new THREE.Vector3(-6, 0, 30); targetRot = new THREE.Euler(0, 0, 0); targetScale = new THREE.Vector3(4, 4, 4);
                    new TWEEN.Tween(obj.mesh.material).to({opacity: 1}, duration).start();
                } else {
                    // 减小推远距离 (1.5 -> 1.2)，使背景图片看起来更大
                    targetPos = obj.scatterPos.clone().multiplyScalar(1.2); targetRot = obj.scatterRot; targetScale = obj.isPhoto ? obj.originalScale : obj.mesh.scale;
                    if(obj.isPhoto) new TWEEN.Tween(obj.mesh.material).to({opacity: 0.1}, duration).start();
                }
            } else if (mode === 'WALL') { // 新增：返回墙面模式
                if (obj.isPhoto) {
                    targetPos = obj.wallPos; targetRot = new THREE.Euler(0,0,0); targetScale = obj.wallScale;
                    new TWEEN.Tween(obj.mesh.material).to({opacity: 1.0}, duration).start();
                } else {
                    // 隐藏非照片粒子
                    targetPos = new THREE.Vector3(0,0,0); targetRot = new THREE.Euler(0,0,0); targetScale = new THREE.Vector3(0.1,0.1,0.1);
                    new TWEEN.Tween(obj.mesh.material).to({opacity: 0}, duration).start();
                }
            }
            new TWEEN.Tween(obj.mesh.position).to({x:targetPos.x, y:targetPos.y, z:targetPos.z}, duration).easing(easing).start();
            new TWEEN.Tween(obj.mesh.rotation).to({x:targetRot.x, y:targetRot.y, z:targetRot.z}, duration).easing(easing).start();
            if (obj.isPhoto) new TWEEN.Tween(obj.mesh.scale).to({x:targetScale.x, y:targetScale.y, z:targetScale.z}, duration).easing(easing).start();
        });

        if (mode === 'DETAIL' || mode === 'WALL') {
            new TWEEN.Tween(group.rotation).to({x:0, y:0}, duration).easing(easing).start();
            STATE.targetRotationX = 0; STATE.targetRotationY = 0;
        }
    }

    // 辅助函数：屏幕坐标转世界坐标
    function getWorldPosFromScreen(x, y, zDepth) {
        const vec = new THREE.Vector3();
        const pos = new THREE.Vector3();
        vec.set((x / window.innerWidth) * 2 - 1, -(y / window.innerHeight) * 2 + 1, 0.5);
        vec.unproject(camera);
        vec.sub(camera.position).normalize();
        const distance = (zDepth - camera.position.z) / vec.z;
        pos.copy(camera.position).add(vec.multiplyScalar(distance));
        return pos;
    }

    // 同步 3D 对象到 DOM 位置
    function syncObjectsToDom(domElements, applyImmediately = true) {
        if (!domElements || domElements.length === 0) return;
        
        const photoObjects = objects.filter(o => o.isPhoto);
        const visibleItems = Array.from(domElements).filter(el => {
            const rect = el.getBoundingClientRect();
            return rect.bottom > 0 && rect.top < window.innerHeight;
        });

        // 计算可见区域的缩放比例
        const vFOV = THREE.Math.degToRad(60);
        const visibleHeight = 2 * Math.tan(vFOV / 2) * CONFIG.cameraZ;
        const scaleFactor = visibleHeight / window.innerHeight;

        photoObjects.forEach((obj, i) => {
            if (i < visibleItems.length) {
                const el = visibleItems[i];
                const rect = el.getBoundingClientRect();
                const cx = rect.left + rect.width / 2;
                const cy = rect.top + rect.height / 2;
                
                // 设置为 Z=0 平面
                const worldPos = getWorldPosFromScreen(cx, cy, 0);
                
                // 记录墙面位置供返回使用
                obj.wallPos.copy(worldPos);
                
                // 计算缩放
                const targetWidth = rect.width * scaleFactor;
                const targetHeight = rect.height * scaleFactor;
                // PlaneGeometry 是 8x6 (之前已修改)
                obj.wallScale.set(targetWidth / 8, targetHeight / 6, 1);
                
                if (applyImmediately) {
                    // 立即应用位置和缩放 (作为动画起点)
                    obj.mesh.position.copy(worldPos);
                    obj.mesh.rotation.set(0, 0, 0);
                    obj.mesh.scale.copy(obj.wallScale);
                    obj.mesh.material.opacity = 1;
                }
            } else {
                if (applyImmediately) {
                    // 多余的对象先隐藏在屏幕外
                    obj.mesh.position.set(0, -100, 0);
                    obj.mesh.material.opacity = 0;
                }
            }
        });
        
        if (applyImmediately) {
            // 隐藏几何粒子
            objects.filter(o => !o.isPhoto).forEach(obj => {
                 obj.mesh.position.set(0, 0, 0);
                 obj.mesh.material.opacity = 0;
            });
        }
    }

    function resetIdleTimer() {
        if (idleTimer) clearTimeout(idleTimer);
        idleTimer = setTimeout(() => {
            console.log("Idle timeout, reverting to 2D");
            stop();
        }, IDLE_TIMEOUT);
    }

    function handleGesture(e) {
        const landmarks = e.detail;
        
        // 如果不处于活动状态，检测握拳以启动
        if (!isActive) {
            if (landmarks && isFistGesture(landmarks)) {
                start();
            }
            return;
        }

        // 如果处于活动状态，重置计时器并处理交互
        resetIdleTimer();

        if (landmarks) {
            STATE.isHandDetected = true;
            const wrist = landmarks[0];
            const indexTip = landmarks[8];
            const thumbTip = landmarks[4];
            const middleMcp = landmarks[9];

            const dist = (p1, p2) => Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));
            
            const isFist = (
                dist(indexTip, wrist) < dist(landmarks[5], wrist) * 0.9 && 
                dist(landmarks[12], wrist) < dist(landmarks[9], wrist) * 0.9
            );
            
            const isOpen = (
                dist(indexTip, wrist) > dist(landmarks[5], wrist) * 1.2 && 
                dist(landmarks[12], wrist) > dist(landmarks[9], wrist) * 1.2
            );

            const isPinch = dist(thumbTip, indexTip) < 0.05 && !isFist;

            if (isFist) {
                transformTo('SPHERE');
            } else if (isPinch) {
                if (STATE.mode !== 'DETAIL') {
                    const photoIndices = objects.map((o, i) => o.isPhoto ? i : -1).filter(i => i !== -1);
                    const randIdx = photoIndices[Math.floor(Math.random() * photoIndices.length)];
                    transformTo('DETAIL', randIdx);
                }
            } else if (isOpen) {
                if (STATE.mode === 'SPHERE' || STATE.mode === 'DETAIL') transformTo('SCATTER');
                if (STATE.mode === 'SCATTER') {
                    STATE.targetRotationY = (middleMcp.x - 0.5) * Math.PI * 2;
                    STATE.targetRotationX = (middleMcp.y - 0.5) * Math.PI;
                }
            }
        } else {
            STATE.isHandDetected = false;
        }
    }

    function isFistGesture(landmarks) {
        const wrist = landmarks[0];
        const dist = (p1, p2) => Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));
        // 放宽判定阈值 0.9 -> 1.1，更容易触发
        return (
            dist(landmarks[8], wrist) < dist(landmarks[5], wrist) * 1.1 && 
            dist(landmarks[12], wrist) < dist(landmarks[9], wrist) * 1.1 &&
            dist(landmarks[16], wrist) < dist(landmarks[13], wrist) * 1.1 &&
            dist(landmarks[20], wrist) < dist(landmarks[17], wrist) * 1.1
        );
    }

    function start() {
        if (isActive) return;
        try {
            console.log("Starting 3D Mode");
            isActive = true;
            window.is3DMode = true; // 全局标志位，通知其他脚本暂停
            
            // 1. 同步位置
            if (getDomElementsCallback) {
                const els = getDomElementsCallback();
                syncObjectsToDom(els, true);
            }
            
            // 2. 瞬间切换显示状态 (无过渡，实现无缝衔接)
            renderer.domElement.style.transition = 'none';
            renderer.domElement.style.opacity = '1';
            renderer.domElement.style.pointerEvents = 'auto';
            
            const wall = document.querySelector('.photo-wall');
            if(wall) {
                wall.style.transition = 'none';
                wall.style.opacity = '0';
            }
            
            // 播放背景视频
            const bgVideo = document.getElementById('bg-video');
            if(bgVideo) bgVideo.style.display = 'block';

            animate();
            resetIdleTimer();
            
            // 3. 开始变换动画
            STATE.mode = 'WALL'; 
            // 稍微延迟以确保渲染循环已启动且第一帧已绘制
            setTimeout(() => transformTo('SPHERE'), 50);
        } catch (e) {
            console.error("Error starting 3D mode:", e);
            isActive = false;
            window.is3DMode = false;
        }
    }

    function stop() {
        if (!isActive) return;
        console.log("Stopping 3D Mode");
        
        // 1. 重新同步位置，但不立即应用，只更新目标 wallPos
        if (getDomElementsCallback) {
            const els = getDomElementsCallback();
            syncObjectsToDom(els, false);
        }

        // 先变换回墙面
        transformTo('WALL');
        
        // 动画结束后隐藏 Canvas
        setTimeout(() => {
            isActive = false;
            window.is3DMode = false; // 恢复 2D 交互
            cancelAnimationFrame(animationId);
            
            // 瞬间切换回 2D 墙
            renderer.domElement.style.opacity = '0';
            renderer.domElement.style.pointerEvents = 'none';

            const wall = document.querySelector('.photo-wall');
            if(wall) {
                wall.style.opacity = '1';
                // 恢复过渡效果 (如果需要)
                setTimeout(() => { wall.style.transition = 'opacity 1s ease'; }, 50);
            }
        }, 1500); // 等待动画完成
    }

    return { init, stop };
})();
