 # shandong-grid-risk

 山东电网拓扑与输电断面风险分析（示意版）

 一个简单的 Python 原型工具，用于可视化山东电网简化拓扑，并结合 Open-Meteo 天气数据进行交易风险预警。

 ## 目标用户

 电力交易员、市场分析师。

 ## 核心能力

 - 可视化山东电网简化拓扑（受端负荷中心 + 供端电源/外电入口）
 - 从 Open-Meteo 获取未来 15 天气象预报
 - 基于简单规则识别风险事件：
   - 受端高温 → 用电负荷上行
   - 供端强降雨 → 新能源出力或外送受限
 - 输出综合电价风险预警

 ## 技术栈

 - Python 3.9+
 - networkx：拓扑图建模
 - matplotlib：静态可视化
 - requests：调用 Open-Meteo API
 - pandas：天气数据处理

## 运行方式

```bash
cd /Users/liyi/Documents/vibe/shandong-grid-risk
pip install -r requirements.txt
python main.py
```

## 输出

- `output/topology.png`：电网拓扑图
- 终端：未来 15 天的节点级风险预警和综合电价风险

## 免责声明

本项目使用的电网拓扑为基于公开能源报道构建的**简化示意模型**，不是山东电网的真实设备参数。天气数据来自 Open-Meteo 免费接口。风险规则为演示用途，不构成交易建议。

## 人口数据

人口数据来自第七次全国人口普查（2020）山东省 9 个受端地市常住人口，用于对需求侧高温风险进行加权。大城市（如临沂、青岛）权重更高，小城市权重更低。

受端高温风险已按人口加权，并输出受影响人口。可在 `scripts/scrape_population.py` 中替换或更新数据源。
 
 ## Web 可视化看板
 
 项目内置一个基于 ECharts 的网页看板，将电网拓扑投影到山东行政边界上，并叠加未来 15 天气象风险与电价指数。
 
 在 `main.py` 运行后，`web/data.json` 会被自动更新。然后启动本地 HTTP 服务器即可查看：
 
 ```bash
 cd /Users/liyi/Documents/vibe/shandong-grid-risk/web
 python3 -m http.server 8081
 ```
 
 在浏览器中打开：`http://dailymeteo.local:8081/index.html（本机也可 http://localhost:8081/index.html）`
 
 看板功能：
 - 山东省行政边界底图 + 简化电网拓扑（受端红 / 供端绿）
 - 日期选择器切换未来 15 天
 - 节点最高温 / 降雨量标签
 - 右侧风险预警卡片：预测电价指数、风险等级、触发节点数
 - 右下角 15 天电价风险指数折线图
 
 注意：看板通过 `fetch` 加载本地 JSON 文件，必须使用 HTTP 服务器访问，不能直接用 `file://` 打开。
