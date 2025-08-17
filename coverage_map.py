import requests
import folium
import random
from shapely.geometry import shape, Point, Polygon, MultiPolygon
from geopy.distance import geodesic
from pyproj import Geod
import numpy as np
import overpy

geod = Geod(ellps="WGS84")

# ===== 計算 Polygon / MultiPolygon 面積 km² =====
def polygon_area_km2(polygon):
    """
    計算 Polygon 或 MultiPolygon 的面積，單位 km²
    """
    if polygon.is_empty:
        return 0

    if isinstance(polygon, Polygon):
        polygons = [polygon]
    elif isinstance(polygon, MultiPolygon):
        polygons = list(polygon.geoms)
    else:
        raise ValueError("輸入必須是 Polygon 或 MultiPolygon")

    area_total = 0
    for poly in polygons:
        lon, lat = poly.exterior.coords.xy
        area, _ = geod.polygon_area_perimeter(lon, lat)
        area_total += abs(area)  # m²

    return area_total / 1e6  # m² → km²

# ===== 根據面積自動決定抽樣點數 =====
def auto_samples(polygon, density_per_km2=200):
    area = polygon_area_km2(polygon)
    return int(area * density_per_km2)

# ===== 取得城市邊界 =====
def get_area_polygon(city_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city_name, "format": "json", "polygon_geojson": 1, "limit": 1}
    headers = {"User-Agent": "Mozilla/5.0 (Python Script)"}
    res = requests.get(url, params=params, headers=headers)
    data = res.json()
    if not data:
        raise ValueError(f"找不到城市: {city_name}")
    geojson = data[0]["geojson"]
    return shape(geojson)

# ===== 使用 Overpass API 抓取品牌店鋪 =====
def get_brand_locations_overpass(polygon, brand):
    minlon, minlat, maxlon, maxlat = polygon.bounds
    api = overpy.Overpass()
    query = f"""
    node({minlat},{minlon},{maxlat},{maxlon})["name"="{brand}"];
    out;
    """
    result = api.query(query)
    stores = [(node.lat, node.lon) for node in result.nodes if polygon.contains(Point(node.lon, node.lat))]
    # for node in result.nodes:
    #     p = Point(node.lon, node.lat)
    #     if polygon.contains(p):
    #         print(f"Node ID: {node.id}, Lat: {node.lat}, Lon: {node.lon}, Name: {node.tags.get('name')}")
    print(f"總共找到 {len(stores)} 家 {brand}")
    return stores

def haversine(lats1, lons1, lats2, lons2):
    R = 6371000.0  # 地球半徑 (m)
    dlat = lats2 - lats1
    dlon = lons2 - lons1
    a = np.sin(dlat/2)**2 + np.cos(lats1) * np.cos(lats2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

# ===== 3. 覆蓋率計算 (Monte Carlo) =====
def calculate_coverage(polygon, stores, radius=500, samples=5000):
    minx, miny, maxx, maxy = polygon.bounds
    
    # === 1. 隨機點 (批次) ===
    xs = np.random.uniform(minx, maxx, samples*2)  
    ys = np.random.uniform(miny, maxy, samples*2)
    pts = np.array([(x, y) for x, y in zip(xs, ys) if polygon.contains(Point(x, y))])
    if len(pts) > samples:
        pts = pts[:samples]
    
    # === 2. 確保 stores 是 float ===
    store_lats = np.array([float(s[0]) for s in stores])
    store_lons = np.array([float(s[1]) for s in stores])
    
    # === 3. 向量化距離計算 ===
    lats1 = np.radians(pts[:,1])[:,None]   # (N,1)
    lons1 = np.radians(pts[:,0])[:,None]
    lats2 = np.radians(store_lats)[None,:] # (1,M)
    lons2 = np.radians(store_lons)[None,:]

    dist_matrix = haversine(lats1, lons1, lats2, lons2)
    
    # === 4. 判斷覆蓋 ===
    min_dist = dist_matrix.min(axis=1)
    covered_mask = min_dist <= radius
    coverage_ratio = covered_mask.mean()

    # === 5. 輸出 sample_points
    sample_points = [(lat, lon, covered) 
                     for (lon, lat), covered in zip(pts, covered_mask)]

    return coverage_ratio, sample_points


# ===== Folium 地圖繪製 =====
def show_map(polygon, stores, radius=500, sample_points=None, coverage=0, samples=0, city="", brand=""):
    centroid = [polygon.centroid.y, polygon.centroid.x]
    m = folium.Map(location=centroid, zoom_start=12)

    # --- 城市邊界 ---
    folium.GeoJson(polygon.__geo_interface__, name="區域").add_to(m)

    # --- 店鋪與覆蓋範圍 ---
    for lat, lon in stores:
        folium.Marker([lat, lon], icon=folium.Icon(color="red")).add_to(m)
        folium.Circle([lat, lon], radius=radius, color="blue", fill=True, opacity=0.2).add_to(m)

    # --- Monte Carlo 抽樣點 ---
    if sample_points:
        for lat, lon, covered in sample_points:
            color = "green" if covered else "gray"
            folium.CircleMarker([lat, lon], radius=2, color=color, fill=True, fill_opacity=0.7).add_to(m)

    # --- 固定左上角資訊框 ---
    info_html = f"""
    <div style="
        position: absolute;
        top: 10px;
        left: 10px;
        width: 250px;
        padding: 15px;
        background: linear-gradient(145deg, #ffffff, #e6f2ff);
        border: 2px solid #4CAF50;
        border-radius: 12px;
        box-shadow: 3px 3px 15px rgba(0,0,0,0.3);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 14px;
        z-index: 9999;
    ">
        <h4 style="margin: 0 0 10px 0; color:#4CAF50;">覆蓋率估算</h4>
        <b>城市：</b>{city}<br>
        <b>品牌：</b>{brand}<br>
        <b>店鋪數量：</b>{len(stores)}<br>
        <b>Monte Carlo 抽樣數：</b>{samples}<br>
        <b>覆蓋率：</b>{coverage*100:.2f}%
    </div>
    """
    from branca.element import Element
    m.get_root().html.add_child(Element(info_html))

    return m

# ===== 主程式 =====
if __name__ == "__main__":
    city = "Taichung"
    brand = "50嵐"
    radius = 800 #單位(公尺) 表方圓{radius}公尺
    
    polygon = get_area_polygon(city)
    stores = get_brand_locations_overpass(polygon, brand)
    
    samples = auto_samples(polygon, density_per_km2=50)
    print(f"Monte Carlo 抽樣點數：{samples}")
    
    if stores:
        coverage, sample_points = calculate_coverage(polygon, stores, radius=radius, samples=samples)
        print(f"{city} 的 {brand} 覆蓋率：約 {coverage*100:.5f}%")
        m = show_map(polygon, stores, radius=radius, sample_points=sample_points, coverage=coverage, samples=samples, city=city, brand=brand)
        m.save("coverage_map.html")
        print("地圖已輸出為 coverage_map.html")
    else:
        print(f"{city} 沒有找到任何 {brand} 店鋪")
