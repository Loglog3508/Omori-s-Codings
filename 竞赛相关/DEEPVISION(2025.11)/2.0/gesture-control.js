(function() {
    // 确保 video 元素存在，如果不存在则创建（虽然 HTML 中会添加，但为了健壮性）
    let videoElement = document.querySelector('.input_video');
    if (!videoElement) {
        videoElement = document.createElement('video');
        videoElement.className = 'input_video';
        videoElement.style.display = 'none';
        document.body.appendChild(videoElement);
    }

    // 简单的状态指示器
    const indicator = document.createElement('div');
    indicator.style.position = 'fixed';
    indicator.style.bottom = '20px';
    indicator.style.left = '20px';
    indicator.style.padding = '10px 16px';
    indicator.style.background = 'rgba(0, 20, 40, 0.6)';
    indicator.style.color = '#78c6f7';
    indicator.style.border = '1px solid rgba(120, 198, 247, 0.3)';
    indicator.style.borderRadius = '20px';
    indicator.style.zIndex = '9999';
    indicator.style.display = 'none'; 
    indicator.style.fontSize = '13px';
    indicator.style.backdropFilter = 'blur(8px)';
    indicator.style.pointerEvents = 'none';
    indicator.innerHTML = '<span style="display:inline-block;width:8px;height:8px;background:#78c6f7;border-radius:50%;margin-right:8px;animation:pulse 1.5s infinite"></span>手势初始化中...';
    
    // 添加 pulse 动画
    const style = document.createElement('style');
    style.innerHTML = `@keyframes pulse { 0% { opacity: 0.4; transform: scale(0.8); } 50% { opacity: 1; transform: scale(1.2); } 100% { opacity: 0.4; transform: scale(0.8); } }`;
    document.head.appendChild(style);
    document.body.appendChild(indicator);

    let isHandDetected = false;
    let isFist = false;
    let fistStartX = 0;
    let fistStartY = 0;
    
    // 平滑处理变量
    let smoothedX = null;
    let smoothedY = null;
    const SMOOTH_FACTOR = 0.12; // 平滑系数 (越小越平滑，抗抖动强)

    function onResults(results) {
        // 全局手势模式控制
        // window.GESTURE_MODE: '3D' (默认) | '2D' | 'OFF'
        if (window.GESTURE_MODE === 'OFF') {
            indicator.style.display = 'none';
            return;
        }

        // 发送原始数据供 3D 场景使用 (仅在 3D 模式下)
        if (window.GESTURE_MODE === '3D' || window.GESTURE_MODE === undefined) {
            if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
                window.dispatchEvent(new CustomEvent('gesture-raw', { detail: results.multiHandLandmarks[0] }));
            } else {
                window.dispatchEvent(new CustomEvent('gesture-raw', { detail: null }));
            }
        }

        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            indicator.style.display = 'flex';
            indicator.style.alignItems = 'center';
            
            if (!isHandDetected) {
                isHandDetected = true;
                // 触发手掌检测事件（变慢）
                window.dispatchEvent(new CustomEvent('gesture-palm', { detail: { slow: true } }));
                
                if (window.GESTURE_MODE === '3D') {
                    indicator.innerHTML = '<span style="display:inline-block;width:8px;height:8px;background:#78c6f7;border-radius:50%;margin-right:8px;"></span>✋ 握拳以启动 3D 场景';
                } else {
                    indicator.innerHTML = '<span style="display:inline-block;width:8px;height:8px;background:#78c6f7;border-radius:50%;margin-right:8px;"></span>检测到手掌 - 移动变慢';
                }
            }

            const landmarks = results.multiHandLandmarks[0];
            
            // 检测握拳
            const wrist = landmarks[0];
            const indexTip = landmarks[8];
            const middleTip = landmarks[12];
            const ringTip = landmarks[16];
            const pinkyTip = landmarks[20];
            const middleMcp = landmarks[9]; // 中指根部

            function dist(p1, p2) {
                return Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));
            }

            // 简单的握拳阈值：指尖到手腕的距离 < 指关节到手腕的距离 * 阈值
            // 这里的阈值需要调试，1.0 比较严格，1.2 比较宽松
            // 另外可以检查指尖是否低于 MCP (对于手掌向上的情况)
            // 这里使用相对距离比较法
            const isFistNow = (
                dist(indexTip, wrist) < dist(landmarks[5], wrist) * 0.9 && 
                dist(middleTip, wrist) < dist(landmarks[9], wrist) * 0.9 &&
                dist(ringTip, wrist) < dist(landmarks[13], wrist) * 0.9 &&
                dist(pinkyTip, wrist) < dist(landmarks[17], wrist) * 0.9
            );

            // 坐标转换：MediaPipe x 是 [0, 1]，且镜像。
            const rawX = (1 - middleMcp.x) * window.innerWidth;
            const rawY = middleMcp.y * window.innerHeight;

            // 指数平滑处理
            if (smoothedX === null) {
                smoothedX = rawX;
                smoothedY = rawY;
            } else {
                smoothedX = smoothedX * (1 - SMOOTH_FACTOR) + rawX * SMOOTH_FACTOR;
                smoothedY = smoothedY * (1 - SMOOTH_FACTOR) + rawY * SMOOTH_FACTOR;
            }
            
            const currentX = smoothedX;
            const currentY = smoothedY;

            // 如果处于 3D 模式，不触发 2D 拖拽逻辑
            if (window.is3DMode) {
                // 即使在 3D 模式下，我们也可以更新指示器状态，或者干脆隐藏
                // 这里选择让指示器显示 "3D 交互中"
                if (isFistNow) {
                     indicator.innerHTML = '<span style="display:inline-block;width:8px;height:8px;background:#F5D061;border-radius:50%;margin-right:8px;"></span>3D 模式交互中';
                     indicator.style.borderColor = 'rgba(245, 208, 97, 0.5)';
                     indicator.style.color = '#F5D061';
                }
                // 确保重置 2D 拖拽状态
                if (isFist) {
                    isFist = false;
                    window.dispatchEvent(new CustomEvent('gesture-drag-end'));
                }
            } else {
                // 仅在明确为 2D 模式时启用平面拖拽
                if (window.GESTURE_MODE === '2D') {
                    // 原有的 2D 拖拽逻辑
                    if (isFistNow) {
                        if (!isFist) {
                            // 刚开始握拳 -> 开始拖拽
                            isFist = true;
                            fistStartX = currentX;
                            fistStartY = currentY;
                            window.dispatchEvent(new CustomEvent('gesture-drag-start', { detail: { x: 0, y: 0 } }));
                            indicator.innerHTML = '<span style="display:inline-block;width:8px;height:8px;background:#ffe29f;border-radius:50%;margin-right:8px;"></span>✊ 握拳 - 拖拽中';
                            indicator.style.borderColor = 'rgba(255, 226, 159, 0.5)';
                            indicator.style.color = '#ffe29f';
                        } else {
                            // 保持握拳 -> 移动
                            const dx = currentX - fistStartX;
                            const dy = currentY - fistStartY;
                            const sensitivity = 1.8; // 灵敏度
                            window.dispatchEvent(new CustomEvent('gesture-drag-move', { detail: { x: dx * sensitivity, y: dy * sensitivity } }));
                        }
                    } else {
                        if (isFist) {
                            // 松开拳头 -> 结束拖拽
                            isFist = false;
                            window.dispatchEvent(new CustomEvent('gesture-drag-end'));
                            indicator.innerHTML = '<span style="display:inline-block;width:8px;height:8px;background:#78c6f7;border-radius:50%;margin-right:8px;"></span>✋ 检测到手掌 - 移动变慢';
                            indicator.style.borderColor = 'rgba(120, 198, 247, 0.3)';
                            indicator.style.color = '#78c6f7';
                        }
                    }
                } else if (window.GESTURE_MODE === '3D') {
                    // 3D 模式下但未激活场景时，显示提示
                    if (isFistNow) {
                        indicator.innerHTML = '<span style="display:inline-block;width:8px;height:8px;background:#F5D061;border-radius:50%;margin-right:8px;"></span>✊ 正在进入 3D 模式...';
                        indicator.style.borderColor = 'rgba(245, 208, 97, 0.5)';
                        indicator.style.color = '#F5D061';
                        
                        // 强制触发 3D 启动
                        window.dispatchEvent(new CustomEvent('gesture-start-3d'));
                    } else {
                        indicator.innerHTML = '<span style="display:inline-block;width:8px;height:8px;background:#78c6f7;border-radius:50%;margin-right:8px;"></span>✋ 握拳以启动 3D 场景';
                        indicator.style.borderColor = 'rgba(120, 198, 247, 0.3)';
                        indicator.style.color = '#78c6f7';
                    }
                }
            }

        } else {
            if (isHandDetected) {
                isHandDetected = false;
                isFist = false;
                smoothedX = null; // 重置平滑
                smoothedY = null;
                // 手消失 -> 恢复正常速度
                window.dispatchEvent(new CustomEvent('gesture-palm', { detail: { slow: false } }));
                window.dispatchEvent(new CustomEvent('gesture-drag-end'));
                indicator.style.display = 'none';
            }
        }
    }

    // 延迟加载 MediaPipe 以避免阻塞页面
    // 改为按需启动，不再自动执行
    window.GestureControl = {
        camera: null,
        hands: null,
        isActive: false,
        
        init: function() {
            if (typeof Hands === 'undefined') {
                console.warn('MediaPipe Hands not loaded');
                indicator.innerText = '手势组件加载失败';
                indicator.style.display = 'block';
                return false;
            }

            if (this.hands) return true;

            this.hands = new Hands({locateFile: (file) => {
                return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
            }});
            
            this.hands.setOptions({
                maxNumHands: 1,
                modelComplexity: 1,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5
            });
            
            this.hands.onResults(onResults);
            return true;
        },

        start: function() {
            if (this.isActive) return;
            
            if (!this.init()) {
                // 如果未加载完成，稍后重试
                setTimeout(() => this.start(), 500);
                return;
            }

            if (!this.camera && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                this.camera = new Camera(videoElement, {
                    onFrame: async () => {
                        if (this.hands) await this.hands.send({image: videoElement});
                    },
                    width: 640,
                    height: 480
                });
            }

            if (this.camera) {
                this.camera.start()
                    .then(() => {
                        this.isActive = true;
                        console.log('[GestureControl] Camera started');
                    })
                    .catch(err => {
                        console.error('[GestureControl] Camera start failed', err);
                        indicator.innerText = '摄像头启动失败';
                        indicator.style.display = 'block';
                    });
            } else {
                console.error("不支持摄像头");
                indicator.innerText = '不支持摄像头';
                indicator.style.display = 'block';
            }
        },

        stop: function() {
            if (!this.isActive) return;
            
            // 尝试停止摄像头流
            if (videoElement.srcObject) {
                const tracks = videoElement.srcObject.getTracks();
                tracks.forEach(track => track.stop());
                videoElement.srcObject = null;
            }
            
            // 如果 Camera 实例有 stop 方法（取决于版本），调用它
            if (this.camera && typeof this.camera.stop === 'function') {
                this.camera.stop();
            }

            this.isActive = false;
            indicator.style.display = 'none';
            console.log('[GestureControl] Camera stopped');
        }
    };
})();
