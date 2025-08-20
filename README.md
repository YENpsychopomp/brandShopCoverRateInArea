# 門市覆蓋率地圖

以 OpenStreetMap 的 Nominatim 與 Overpass API 取得城市邊界與品牌門市位置，使用 Monte Carlo 估算覆蓋率並以 Folium 產生可互動的地圖。

## 特色
- 自動抓取城市邊界（Nominatim）
- 以 Overpass 查找品牌門市座標
- 以 Haversine 公式進行向量化距離計算，快速估算覆蓋率
- Folium 地圖展示：範圍、多個門市、覆蓋圓、抽樣點
- 依城市面積自動決定抽樣點數（density_per_km2）

## 專案結構
```
.
├─ main.py                        # 互動入口，提供多種模式
├─ coverage_map_test.py           # 獨立測試腳本（舊版）
├─ cover/
│  ├─ __init__.py
│  ├─ coverage_map.py             # 核心：抓邊界/門市、估算覆蓋、出地圖
│  └─ city_brands.py              # 城市與品牌名稱對照
└─ result/
   └─ *.html                      # 產生的地圖輸出
```

## 環境需求
- Python 3.10+
- 建議使用虛擬環境（venv 或 conda）

必要套件：
- requests
- shapely
- geopy
- pyproj
- folium
- overpy
- numpy

## 安裝
在專案根目錄安裝依賴：

```powershell
# 以 conda 為例（可改用 venv）
conda create -n hilifecover python=3.11 -y; conda activate hilifecover
pip install requests shapely geopy pyproj folium overpy numpy
```

## 使用方式
### 互動模式（推薦）
執行 `main.py`，依提示選擇模式：

```powershell
python .\main.py
```

- 1: 單一城市
  - 依序輸入 城市、品牌（預設：萊爾富）。
- 2: 多城市
  - 以逗號分隔輸入多個城市，品牌同上。
- 3: 所有城市（依 `city_brands.taiwan_cities_dict`）
  - 輸入品牌後，對所有城市逐一生成結果。
- 4: 退出

輸出地圖將存於 `result/`，檔名格式：
`{品牌英文或原名}-{城市英文或原名}_coverage_map.html`

### 直接呼叫函式
可在 Python 腳本中使用：

```python
from cover.coverage_map import run

logs = run(city="台北市", brand="萊爾富", radius=800, density_per_km2=200)
print("\n".join(logs))
```

## 重要參數說明
- radius（公尺）：每間店的覆蓋半徑，預設 800。
- density_per_km2（點/平方公里）：Monte Carlo 抽樣密度，樣本數 = 面積(km²) × density_per_km2。
  - 值越大估計越穩定，但計算時間越久。200 是穩健起點。

## 運作流程摘要
1. 取得城市邊界：`get_area_polygon(city)` 以 Nominatim 搜尋城市，回傳 Polygon/MultiPolygon。
2. 取得門市位置：`get_brand_locations_overpass(polygon, brand)` 以邊界 bbox 查詢，過濾落在區域內的節點。
3. 覆蓋率估算：`calculate_coverage(...)`
   - 在邊界內隨機抽樣點
   - 用 `haversine` 向量化計算與各門市距離（公尺）
   - 判斷是否在 `radius` 內，計算覆蓋比例
4. 地圖輸出：`show_map(...)` 以 Folium 畫出邊界、門市、覆蓋圈與抽樣點，並加入資訊框。

## 注意事項與常見問題
- API 使用規範：
  - 請尊重 Nominatim 與 Overpass 的使用條款與速率限制，避免過於頻繁的自動化請求。
- 查無門市或 API 回應為空：
  - 會顯示「沒有找到任何門市」，不輸出地圖。
- 城市或品牌名稱：
  - `city_brands.py` 提供中英對照；輸出檔名會優先使用對照表的英文名稱。
- 經緯度單位：
  - `haversine` 內使用弧度計算，外部傳入時已以 `np.radians` 轉換。

## 開發說明
- 主要檔案：`cover/coverage_map.py`
  - `polygon_area_km2`：用 WGS84 橢球面積換算 km²
  - `get_area_polygon`：Nominatim 抓取城市邊界
  - `get_brand_locations_overpass`：Overpass 以 bbox 查詢，回傳 (lat, lon)
  - `haversine`：向量化大圓距離（公尺）
  - `calculate_coverage`：Monte Carlo 覆蓋率估算
  - `show_map`：用 Folium 繪圖與資訊框
  - `run`：整合流程，存檔到 result/

## 授權
此專案僅作技術示範用途。品牌名稱及其商標權屬原權利人所有。OpenStreetMap 資料依其授權條款使用。
