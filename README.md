# brandShopCoverRateInArea

此專案使用 OpenStreetMap 與 Overpass API，結合 Monte Carlo 方法，計算並可視化高雄市便利商店（如全家、萊爾富、OK 等）的地理覆蓋率。

---

## 功能

1. **抓取城市邊界**  
   使用 [Nominatim API](https://nominatim.org/) 取得指定城市的 GeoJSON 邊界。

2. **抓取店鋪資料**  
   使用 [Overpass API](https://overpass-api.de/) 擷取指定品牌的店鋪位置，並自動過濾掉位於城市外的店鋪。

3. **Monte Carlo 覆蓋率估算**  
   - 自動根據城市面積決定抽樣點數
   - 計算每個隨機點是否在店鋪覆蓋半徑內
   - 支援自訂覆蓋半徑（預設 500 公尺）

4. **地圖可視化**  
   - 顯示城市邊界
   - 標記店鋪位置與覆蓋半徑
   - 顯示 Monte Carlo 隨機抽樣點（已覆蓋藍色，未覆蓋灰色）
   - 浮動資訊框展示覆蓋率、店鋪數量、抽樣點數

---
## 範例畫面
<img width="2558" height="1229" alt="螢幕擷取畫面 2025-08-17 151725" src="https://github.com/user-attachments/assets/da008d4c-c998-47d2-9502-e191b2a70497" />

## 安裝與依賴

```bash
pip install requests folium shapely geopy pyproj overpy numpy numba
```
