# 大连市近10年天气数据分析系统

这是一个用于课程作业的数据采集、分析与网页展示项目。当前选题已切换为“大连市近10年天气数据分析”，真实数据来自 Open-Meteo Archive API。

## 一键运行

双击根目录下的：

```text
一键运行.bat
```

脚本会自动完成：

```text
检测天气数据 -> 必要时采集真实数据 -> 清洗同步网页数据 -> 启动本地网页服务 -> 打开浏览器
```

强制重新采集真实天气数据：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_all.ps1 -RefreshData
```

只允许真实数据，采集失败就停止：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_all.ps1 -RefreshData -StrictRealData
```

## 页面结构

```text
frontend/index.html      总览
frontend/charts.html     气温、降水与极端天气趋势
frontend/records.html    每日天气明细检索
frontend/weather.html    天气类型与极端天气
frontend/source.html     数据采集与处理说明
```

## 数据文件

```text
data/weather_raw.json          原始 API 响应
data/weather_clean.json        清洗后的每日天气记录
data/weather_metadata.json     汇总统计和元信息
frontend/data/weather_data.js  前端直接加载的数据
```

## 手动运行

采集真实数据：

```powershell
e:\python\python.exe scripts/collect_weather.py
```

清洗并同步网页：

```powershell
e:\python\python.exe scripts/process_weather.py
```

启动本地网页服务：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/serve_static.ps1 -Port 8000
```

访问：

```text
http://localhost:8000/frontend/index.html
```

## 分析维度

- 10 年日级天气记录，当前真实数据为 3652 天。
- 年均气温趋势、月均气温与降水趋势。
- 年降水量、季节平均气温、季节降水量。
- 天气类型占比。
- 高温日、低温日、大雨日、大风日、降雪日统计。
- 每日明细筛选：年份、季节、天气类型、最高温阈值、关键词。

## 数据来源

- 真实来源：Open-Meteo Archive API。
- 位置：大连市，经纬度约 `38.914, 121.6147`。
- 如果网络采集失败，一键脚本会使用结构一致的本地演示天气数据兜底；页面顶部和 `weather_metadata.json` 会显示当前 `source`。
