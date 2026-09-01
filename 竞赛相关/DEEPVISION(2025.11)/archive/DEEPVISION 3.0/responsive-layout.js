// 自适应华容道布局系统
// 已切换为 CSS Grid 严格等距布局，暂时禁用旧的绝对定位华容道算法以防止覆盖事件区域
// 如需重新启用，将 DISABLE_RESPONSIVE_HUARONG 设为 false
const DISABLE_RESPONSIVE_HUARONG = true;

class ResponsiveHuarongLayout {
    constructor() {
        this.container = null;
        this.pieces = [];
        this.aspectRatio = 16 / 9; // 容器纵横比
        
        // 基于华容道容器的精确空间利用配置
        this.percentConfig = {
            // 外边距：华容道容器到边界的距离（精确控制）
            outerMargin: 0.002,        // 0.2% 最小外边距，防止溢出
            // 水平间隙：组件之间的水平距离
            horizontalGap: 0.003,      // 0.3% 紧凑水平间隙
            // 垂直间隙：组件之间的垂直距离  
            verticalGap: 0.003,        // 0.3% 紧凑垂直间隙
            // 最小间距限制（像素）- 保证最基本可用性
            minMargin: 1,              // 最小边距1px，防止溢出
            minGap: 1,                 // 最小间隙1px，节省空间
            // 安全系数 - 预留一定空间防止溢出
            safetyFactor: 0.98         // 使用98%空间，预留2%安全空间
        };
        
        console.log('ResponsiveHuarongLayout: 初始化开始');
        this.init();
    }
    
    init() {
        // 等待DOM加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.setupLayout();
            });
        } else {
            this.setupLayout();
        }
    }
    
    setupLayout() {
        this.container = document.querySelector('.huarong-puzzle-container');
        this.pieces = document.querySelectorAll('.huarong-piece');
        
        console.log('找到容器:', this.container);
        console.log('找到组件数量:', this.pieces.length);
        
        if (!this.container || this.pieces.length === 0) {
            console.warn('华容道容器或组件未找到');
            return;
        }
        
        // 初始化布局
        if (DISABLE_RESPONSIVE_HUARONG) {
            console.log('🛑 已禁用旧华容道绝对定位算法，依赖 CSS Grid 布局');
            return;
        }
        this.calculateAndApplyLayout();
        
        // 监听窗口大小变化
        this.setupResizeObserver();
        
        console.log('✅ 自适应华容道布局初始化完成');
    }
    
    // 根据华容道容器宽度计算最佳高度（严格控制4行布局）
    calculateOptimalHeight(width) {
        // 8个组件4行布局需要足够垂直空间，防止溢出
        const idealRatio = 4 / 4.5; // 调整到4.5，给底部更多空间
        const baseHeight = width / idealRatio;
        
        // 根据屏幕方向和尺寸调整
        const screenHeight = window.innerHeight;
        const screenWidth = window.innerWidth;
        const isLandscape = screenWidth > screenHeight;
        
        let calculatedHeight;
        
        if (isLandscape) {
            // 横屏模式：保守的垂直空间使用，防止溢出
            const landscapeRatio = Math.min(0.85, Math.max(0.75, screenHeight / screenWidth));
            calculatedHeight = Math.max(
                baseHeight,
                screenHeight * landscapeRatio
            );
        } else {
            // 竖屏模式：适中的垂直空间使用
            calculatedHeight = Math.min(
                baseHeight,
                screenHeight * 0.85  // 降低到85%，更保守
            );
        }
        
        // 确保最小高度但不过度膨胀
        const minHeight = Math.max(350, width * 0.4); // 降低最小高度比例
        const maxHeight = Math.min(screenHeight * 0.9, width * 1.2); // 增加最大高度限制
        calculatedHeight = Math.min(Math.max(calculatedHeight, minHeight), maxHeight);
        
        console.log(`📐 屏幕: ${screenWidth}×${screenHeight}, 容器: ${width}×${calculatedHeight.toFixed(0)}, 模式: ${isLandscape ? '横屏' : '竖屏'}`);
        
        return calculatedHeight;
    }
    
    calculateAndApplyLayout() {
    if (DISABLE_RESPONSIVE_HUARONG) return; // 防御：禁用后不执行
    // 首先获取华容道容器的实际尺寸（由CSS规则自动计算）
        const containerRect = this.container.getBoundingClientRect();
        const availableWidth = containerRect.width || this.container.offsetWidth;
        
        // 如果容器宽度为0，使用父容器宽度
        const finalWidth = availableWidth > 0 ? availableWidth : 
                          Math.min(window.innerWidth * 0.9, 1400);
        
        console.log(`🎯 华容道容器实际宽度: ${finalWidth}px`);
        
        // 根据华容道容器实际宽度计算最佳高度
        const availableHeight = this.calculateOptimalHeight(finalWidth);
        
        // 基于华容道容器尺寸计算间距（更精准的空间利用）
        const spacing = {
            // 外边距（华容道容器边缘到组件）
            outerMargin: Math.max(
                this.percentConfig.minMargin,
                finalWidth * this.percentConfig.outerMargin
            ),
            // 水平间隙（组件之间）
            horizontalGap: Math.max(
                this.percentConfig.minGap,
                finalWidth * this.percentConfig.horizontalGap
            ),
            // 垂直间隙（组件之间）
            verticalGap: Math.max(
                this.percentConfig.minGap,
                availableHeight * this.percentConfig.verticalGap
            )
        };

        // 高效空间利用的华容道布局结构（包含8个组件）
        const screenRatio = finalWidth / availableHeight;
        
        // 高效4行布局 - 基于华容道容器的安全空间利用率
        let layoutStructure = {
            effectiveCols: 3,      // 保持3列结构
            effectiveRows: 4.0,    // 精确的4行，更紧凑
            horizontalGaps: 2,     // 2个水平间隙
            verticalGaps: 3,       // 3个垂直间隙（4行需要3个间隙）
            // 基于华容道容器的安全空间利用率
            spaceUtilization: 0.86, // 降到86%，预留空间防止溢出
            componentPadding: 0.002, // 最小化组件内边距
            safetyMargin: 0.98     // 应用98%安全系数
        };
        
        // 根据华容道容器的屏幕比例精准优化
        if (screenRatio > 2.2) {
            // 超宽屏华容道容器：极致利用率
            layoutStructure.spaceUtilization = 0.94;
            layoutStructure.effectiveRows = 3.7;
            layoutStructure.componentPadding = 0.002;
        } else if (screenRatio > 1.8) {
            // 宽屏华容道容器：高效利用率
            layoutStructure.spaceUtilization = 0.92;
            layoutStructure.effectiveRows = 3.8;
        } else if (screenRatio < 1.2) {
            // 窄屏华容道容器：平衡利用率和可用性
            layoutStructure.spaceUtilization = 0.87;
            layoutStructure.effectiveRows = 4.2;
        }

        console.log(`🎯 华容道容器比例: ${screenRatio.toFixed(2)}, 空间利用率: ${(layoutStructure.spaceUtilization*100).toFixed(1)}%`);
        
        // 高效空间利用算法：优先最大化组件空间
        const totalMarginWidth = spacing.outerMargin * 2;
        const totalGapWidth = spacing.horizontalGap * layoutStructure.horizontalGaps;
        const totalMarginHeight = spacing.outerMargin * 2;
        const totalGapHeight = spacing.verticalGap * layoutStructure.verticalGaps;
        
        // 计算实际可用空间
        const rawContentWidth = finalWidth - totalMarginWidth - totalGapWidth;
        const rawContentHeight = availableHeight - totalMarginHeight - totalGapHeight;
        
        // 应用空间利用率优化
        const contentWidth = rawContentWidth * layoutStructure.spaceUtilization;
        const contentHeight = rawContentHeight * layoutStructure.spaceUtilization;
        
        // 计算优化的基础单元大小（应用安全系数）
        const safeContentWidth = contentWidth * (layoutStructure.safetyMargin || this.percentConfig.safetyFactor);
        const safeContentHeight = contentHeight * (layoutStructure.safetyMargin || this.percentConfig.safetyFactor);
        
        const baseUnitWidth = safeContentWidth / layoutStructure.effectiveCols;
        const baseUnitHeight = safeContentHeight / layoutStructure.effectiveRows;
        
        // 均匀分配间距 - 确保四边边距一致
        const savedWidth = rawContentWidth - contentWidth;
        const savedHeight = rawContentHeight - contentHeight;
        
        // 简化的布局算法 - 防止重叠和压线
        const safeMargin = Math.max(12, Math.min(finalWidth, availableHeight) * 0.015); // 1.5%边距，避免压线
        const safeHorizontalGap = Math.max(8, finalWidth * 0.012); // 1.2%水平间距
        const safeVerticalGap = Math.max(8, availableHeight * 0.012); // 1.2%垂直间距
        
        // 计算可用空间
        const usableWidth = finalWidth - (safeMargin * 2) - (safeHorizontalGap * 2); // 3列需要2个间隙
        const usableHeight = availableHeight - (safeMargin * 2) - (safeVerticalGap * 3); // 4行需要3个间隙
        
        // 计算基础单元大小
        const unitWidth = usableWidth / 3; // 3列
        const unitHeight = usableHeight / 4; // 4行
        
        // 统一的间距配置
        const optimizedSpacing = {
            outerMargin: safeMargin,
            horizontalGap: safeHorizontalGap,
            verticalGap: safeVerticalGap
        };
        
        console.log(`🎯 统一边距: ${safeMargin.toFixed(1)}px (四边一致)`);
        console.log(`📐 单元大小: ${unitWidth.toFixed(1)}x${unitHeight.toFixed(1)}px`);
        console.log(`📏 间距: H=${safeHorizontalGap.toFixed(1)}px, V=${safeVerticalGap.toFixed(1)}px`);
        
        // 简化的布局计算
        const rowHeight = unitHeight;
        const colWidth = unitWidth;
        
        // 计算行位置
        const row1Top = optimizedSpacing.outerMargin;
        const row2Top = row1Top + rowHeight + optimizedSpacing.verticalGap;
        const row3Top = row2Top + rowHeight + optimizedSpacing.verticalGap;
        const row4Top = row3Top + rowHeight + optimizedSpacing.verticalGap;
        
        // 计算列位置
        const col1Left = optimizedSpacing.outerMargin;
        const col2Left = col1Left + colWidth + optimizedSpacing.horizontalGap;
        const col3Left = col2Left + colWidth + optimizedSpacing.horizontalGap;
        
        const layouts = [
            // piece-1: 左上角
            { 
                selector: '.piece-1',
                layout: { 
                    width: colWidth,
                    height: rowHeight,
                    left: col1Left,
                    top: row1Top
                }
            },
            // piece-2: 顶部中间（跨两列）
            { 
                selector: '.piece-2',
                layout: { 
                    width: colWidth * 2 + optimizedSpacing.horizontalGap,
                    height: rowHeight,
                    left: col2Left,
                    top: row1Top
                }
            },
            // piece-3: 右侧大块（从第二行开始，跨两行）
            { 
                selector: '.piece-3',
                layout: { 
                    width: colWidth,
                    height: rowHeight * 2 + optimizedSpacing.verticalGap,
                    left: col3Left,
                    top: row2Top
                }
            },
            // piece-4: 第二行左侧
            { 
                selector: '.piece-4',
                layout: { 
                    width: colWidth,
                    height: rowHeight,
                    left: col1Left,
                    top: row2Top
                }
            },
            // piece-5: 第二行中间
            { 
                selector: '.piece-5',
                layout: { 
                    width: colWidth,
                    height: rowHeight,
                    left: col2Left,
                    top: row2Top
                }
            },
            // piece-6: 第三行（跨前两列）
            { 
                selector: '.piece-6',
                layout: { 
                    width: colWidth * 2 + optimizedSpacing.horizontalGap,
                    height: rowHeight,
                    left: col1Left,
                    top: row3Top
                }
            },
            // piece-7: 河流排放 - 第四行左侧（使用统一行高）
            { 
                selector: '.piece-7',
                layout: { 
                    width: colWidth,
                    height: rowHeight, // 使用标准行高，与其他行保持一致
                    left: col1Left,
                    top: row4Top
                }
            },
            // piece-8: 环流数据概览 - 第四行中间，横跨两列（使用统一行高）
            { 
                selector: '.piece-8',
                layout: { 
                    width: colWidth * 2 + optimizedSpacing.horizontalGap,
                    height: rowHeight, // 使用标准行高，与其他行保持一致
                    left: col2Left,
                    top: row4Top
                }
            }
        ];
        
        // 应用布局 - 直接使用计算好的位置和大小
        layouts.forEach(layoutItem => {
            const element = document.querySelector(layoutItem.selector);
            if (!element) return;
            
            const { width, height, left, top } = layoutItem.layout;
            
            // 应用位置和大小，确保完全填充
            element.style.cssText += `
                left: ${Math.round(left)}px !important;
                top: ${Math.round(top)}px !important;
                width: ${Math.round(width)}px !important;
                height: ${Math.round(height)}px !important;
                position: absolute;
                transition: all 0.3s ease;
                box-sizing: border-box;
            `;
            
            console.log(`📦 ${layoutItem.selector}: ${Math.round(width)}×${Math.round(height)} at (${Math.round(left)}, ${Math.round(top)})`);
            
            // 严格的边界检查和实时修复
            const bottomPos = top + height;
            const rightPos = left + width;
            const isVerticalOverflow = bottomPos > availableHeight;
            const isHorizontalOverflow = rightPos > finalWidth;
            
            // 如果溢出，立即修复
            if (isVerticalOverflow || isHorizontalOverflow) {
                let correctedWidth = width;
                let correctedHeight = height;
                let correctedTop = top;
                let correctedLeft = left;
                
                if (isHorizontalOverflow) {
                    correctedWidth = finalWidth - left - optimizedSpacing.outerMargin;
                    console.warn(`� 修复 ${layoutItem.selector} 水平溢出: ${width} → ${correctedWidth}px`);
                }
                
                if (isVerticalOverflow) {
                    correctedHeight = availableHeight - top - optimizedSpacing.outerMargin;
                    console.warn(`🔧 修复 ${layoutItem.selector} 垂直溢出: ${height} → ${correctedHeight}px`);
                }
                
                // 应用修正后的尺寸
                element.style.cssText += `
                    width: ${Math.max(50, Math.round(correctedWidth))}px !important;
                    height: ${Math.max(40, Math.round(correctedHeight))}px !important;
                `;
                
                console.log(`🔧 ${layoutItem.selector} 已修复: ${Math.round(correctedWidth)}×${Math.round(correctedHeight)}`);
            }
            
            // 特别检查第四行组件
            if (layoutItem.selector === '.piece-7' || layoutItem.selector === '.piece-8') {
                console.log(`� ${layoutItem.selector}: ${Math.round(width)}×${Math.round(height)} at (${Math.round(left)}, ${Math.round(top)})`);
                console.log(`   底边界: ${Math.round(bottomPos)}px / ${availableHeight}px ${isVerticalOverflow ? '❌' : '✅'}`);
            }
        });
        
        // 更新容器高度 - 动态调整以适应屏幕比例
        this.container.style.height = `${availableHeight}px`;
        
        // 同时更新父容器的高度以确保完整显示
        const parentContainer = this.container.parentElement;
        if (parentContainer && parentContainer.style) {
            parentContainer.style.minHeight = `${availableHeight}px`;
        }
        
        console.log(`📐 华容道容器: ${finalWidth}×${availableHeight} (比例: ${(finalWidth/availableHeight).toFixed(2)})`);
        console.log(`🎯 空间利用率: ${(layoutStructure.spaceUtilization*100).toFixed(1)}%`);
        console.log(`📊 统一外边距: ${optimizedSpacing.outerMargin.toFixed(1)}px (基础: ${spacing.outerMargin.toFixed(1)}px)`);
        console.log(`📊 水平间隙: ${optimizedSpacing.horizontalGap.toFixed(1)}px (基础: ${spacing.horizontalGap.toFixed(1)}px)`);
        console.log(`📊 垂直间隙: ${optimizedSpacing.verticalGap.toFixed(1)}px (基础: ${spacing.verticalGap.toFixed(1)}px)`);
        console.log(`📊 间距比例: H/V = ${(optimizedSpacing.horizontalGap/optimizedSpacing.verticalGap).toFixed(2)}`);
        console.log(`📊 基础单元: ${baseUnitWidth.toFixed(1)}×${baseUnitHeight.toFixed(1)}px`);
        console.log(`📊 内容区域: ${contentWidth.toFixed(1)}×${contentHeight.toFixed(1)}px (利用率: ${((contentWidth*contentHeight)/(finalWidth*availableHeight)*100).toFixed(1)}%)`);
        console.log(`📊 布局结构: ${layoutStructure.effectiveCols}列×${layoutStructure.effectiveRows}行`);
        
        // 验证高效布局完整性
        this.validateLayout(finalWidth, availableHeight, optimizedSpacing, layouts);
        
        // 自动修复溢出问题
        this.fixOverflowIssues(layouts, finalWidth, availableHeight);
    }
    
    // 验证布局完整性 - 检查是否完全填充华容道容器
    validateLayout(containerWidth, availableHeight, spacing, layouts) {
        let maxRight = 0;
        let maxBottom = 0;
        
        layouts.forEach(layoutItem => {
            const element = document.querySelector(layoutItem.selector);
            if (element) {
                const { width, height, left, top } = layoutItem.layout;
                maxRight = Math.max(maxRight, left + width);
                maxBottom = Math.max(maxBottom, top + height);
            }
        });
        
        const expectedRight = containerWidth - spacing.outerMargin;
        const expectedBottom = availableHeight - spacing.outerMargin;
        
        const fillRatio = {
            horizontal: (maxRight / expectedRight * 100).toFixed(1),
            vertical: (maxBottom / expectedBottom * 100).toFixed(1)
        };
        
        console.log(`🎯 容器填充率: 水平 ${fillRatio.horizontal}%, 垂直 ${fillRatio.vertical}%`);
        
        return fillRatio;
    }
    
    setupResizeObserver() {
        // 使用ResizeObserver监听容器大小变化
        if (window.ResizeObserver) {
            const resizeObserver = new ResizeObserver(entries => {
                // 防抖处理
                clearTimeout(this.resizeTimer);
                this.resizeTimer = setTimeout(() => {
                    this.calculateAndApplyLayout();
                }, 150);
            });
            
            resizeObserver.observe(document.body);
        } else {
            // 后备方案：监听window resize
            window.addEventListener('resize', () => {
                clearTimeout(this.resizeTimer);
                this.resizeTimer = setTimeout(() => {
                    this.calculateAndApplyLayout();
                }, 150);
            });
        }
    }
    
    // 手动触发重新布局
    refresh() {
        this.calculateAndApplyLayout();
    }
    
    // 动态调整百分比配置
    updateSpacingConfig(config) {
        Object.assign(this.percentConfig, config);
        this.refresh();
        console.log('📝 间距配置已更新:', this.percentConfig);
    }
    
    // 获取当前间距配置
    getSpacingConfig() {
        return { ...this.percentConfig };
    }
    
    // 自动修复溢出问题 - 增强版
    fixOverflowIssues(layouts, containerWidth, containerHeight) {
        console.log('🔧 严格检查并修复溢出问题...');
        
        // 留更多安全边距
        const safeMargin = 10;
        const effectiveWidth = containerWidth - safeMargin;
        const effectiveHeight = containerHeight - safeMargin;
        
        layouts.forEach(layoutItem => {
            const { selector, layout } = layoutItem;
            let { width, height, left, top } = layout;
            
            // 检查溢出情况
            const rightEdge = left + width;
            const bottomEdge = top + height;
            
            let needsFixing = false;
            let newWidth = width;
            let newHeight = height;
            let newLeft = left;
            let newTop = top;
            
            // 严格的右侧边界检查
            if (rightEdge > effectiveWidth) {
                newWidth = Math.max(80, effectiveWidth - left);
                needsFixing = true;
                console.warn(`� 严格修复${selector}右侧溢出: ${Math.round(rightEdge - effectiveWidth)}px`);
            }
            
            // 严格的底部边界检查
            if (bottomEdge > effectiveHeight) {
                newHeight = Math.max(50, effectiveHeight - top);
                needsFixing = true;
                console.warn(`� 严格修复${selector}底部溢出: ${Math.round(bottomEdge - effectiveHeight)}px`);
            }
            
            // 左侧边界检查
            if (left < 5) {
                newLeft = 5;
                needsFixing = true;
                console.warn(`🚨 修复${selector}左侧溢出`);
            }
            
            // 顶部边界检查
            if (top < 5) {
                newTop = 5;
                needsFixing = true;
                console.warn(`🚨 修复${selector}顶部溢出`);
            }
            
            // 确保最小可用尺寸
            if (newWidth < 80) {
                newWidth = 80;
                newLeft = Math.max(5, Math.min(newLeft, effectiveWidth - 80));
                needsFixing = true;
            }
            if (newHeight < 50) {
                newHeight = 50;
                newTop = Math.max(5, Math.min(newTop, effectiveHeight - 50));
                needsFixing = true;
            }
            
            // 应用修复
            if (needsFixing) {
                const element = document.querySelector(selector);
                if (element) {
                    element.style.cssText += `
                        width: ${Math.round(newWidth)}px !important;
                        height: ${Math.round(newHeight)}px !important;
                        left: ${Math.round(newLeft)}px !important;
                        top: ${Math.round(newTop)}px !important;
                        max-width: ${Math.round(newWidth)}px !important;
                        max-height: ${Math.round(newHeight)}px !important;
                        overflow: hidden !important;
                        box-sizing: border-box !important;
                    `;
                    
                    console.log(`✅ 严格修复${selector}: ${Math.round(newWidth)}×${Math.round(newHeight)} at (${Math.round(newLeft)}, ${Math.round(newTop)})`);
                }
            }
        });
        
        // 验证修复效果
        setTimeout(() => this.validateFixResults(containerWidth, containerHeight), 100);
    }
    
    // 验证修复结果
    validateFixResults(containerWidth, containerHeight) {
        console.log('🔍 验证修复结果...');
        
        const criticalPieces = ['.piece-7', '.piece-8'];
        criticalPieces.forEach(selector => {
            const element = document.querySelector(selector);
            if (element) {
                const rect = element.getBoundingClientRect();
                const containerRect = this.container.getBoundingClientRect();
                
                const rightOverflow = rect.right > containerRect.right;
                const bottomOverflow = rect.bottom > containerRect.bottom;
                
                if (rightOverflow || bottomOverflow) {
                    console.error(`❌ ${selector} 修复后仍有溢出! 右侧:${rightOverflow ? '是' : '否'} 底部:${bottomOverflow ? '是' : '否'}`);
                } else {
                    console.log(`✅ ${selector} 修复成功，无溢出`);
                }
            }
        });
    }
    
    // 获取当前华容道容器的实际间距值（像素）- 包含优化信息
    calculateSpacingMetrics() {
        if (!this.container) return null;
        
        // 获取华容道容器实际尺寸
        const containerRect = this.container.getBoundingClientRect();
        const containerWidth = containerRect.width || this.container.offsetWidth;
        const finalWidth = containerWidth > 0 ? containerWidth : 
                          Math.min(window.innerWidth * 0.9, 1400);
        const availableHeight = this.calculateOptimalHeight(finalWidth);
        
        // 基于华容道容器的基础间距
        const baseSpacing = {
            outerMargin: Math.max(this.percentConfig.minMargin, finalWidth * this.percentConfig.outerMargin),
            horizontalGap: Math.max(this.percentConfig.minGap, finalWidth * this.percentConfig.horizontalGap),
            verticalGap: Math.max(this.percentConfig.minGap, availableHeight * this.percentConfig.verticalGap)
        };
        
        // 空间利用率优化
        const screenRatio = finalWidth / availableHeight;
        let spaceUtilization = 0.88; // 基础88%利用率
        if (screenRatio > 2.0) spaceUtilization = 0.92; // 超宽屏92%
        else if (screenRatio < 1.2) spaceUtilization = 0.85; // 窄屏85%
        
        const spacing = {
            ...baseSpacing,
            containerSize: { width: finalWidth, height: availableHeight },
            screenRatio: screenRatio,
            isLandscape: finalWidth > availableHeight * 1.3,
            spaceUtilization: spaceUtilization,
            actualContainerHeight: this.container.style.height || 'auto',
            // 计算实际空间利用率
            contentUtilization: ((finalWidth * availableHeight * spaceUtilization) / (finalWidth * availableHeight) * 100).toFixed(1)
        };
        
        return spacing;
    }

    // 获取当前空间统计信息（供监控页面使用）
    getCurrentSpacing() {
        return this.calculateSpacingMetrics();
    }

    // 手动刷新布局（供监控页面调用）
    refresh() {
        this.calculateAndApplyLayout();
    }
}

// 初始化自适应布局
const huarongLayout = new ResponsiveHuarongLayout();

// 导出到全局供其他脚本使用
window.huarongLayout = huarongLayout;